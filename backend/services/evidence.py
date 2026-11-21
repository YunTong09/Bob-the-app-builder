"""Evidence assessment and the single evidence validator (Developer 3).

Assessment: Claude classifies each claim against the authorised records, citing
a verbatim quote for every record it relies on. Deterministic checks then drop
anything not grounded in a real retrieved record:
* unknown / other-owner message IDs are discarded;
* a quote must appear in that record's original content (ID membership alone is
  never treated as support);
* a "supported" or "contradicted" verdict with no surviving grounded record is
  downgraded to "unverified" -- missing evidence never proves a claim false.
An independent semantic review then checks each classification and whether its
support statements actually follow from the original records. Quote membership
alone is never semantic approval.

Validation (``validate``) is the only evidence validator in the system. The
orchestrator calls it with the original DraftInput before returning a reply. It
checks the actual final text with a separate semantic review. The drafting
service also calls ``check_draft`` to retry once on cheap structural failures.
"""

from __future__ import annotations

import re
import unicodedata
from typing import Any, Sequence

from backend.application.errors import EvidenceValidationError, ModelError
from backend.application.ports import (
    ClaimAssessment,
    DraftInput,
    EvidenceAssessment,
    EvidenceLink,
    MemoryRecord,
    MessageAnalysis,
    OwnerContext,
    ReplyDraft,
    ValidatedReply,
)

from .llm import JsonModel, call_with_retry
from .review import review_assessment, review_draft

MIN_QUOTE_CHARS = 8
MAX_REPLY_CHARS = 5000
MAX_TEXT_CHARS = 600

SYSTEM = """You check an employee's factual claims against their imported workplace
conversation history for Rage-to-Reply.

For each claim (identified by claim_index), decide:
- "supported": a record explicitly establishes the claim.
- "contradicted": a record explicitly conflicts with the claim.
- "unverified": the records do not establish the claim either way. Missing evidence is NOT
  proof that a claim is false.

For every record you rely on, give:
- message_id: exactly as provided.
- quote: an exact, contiguous excerpt copied character-for-character from that record's
  content (at least a few words) that shows the support or conflict.
- statement: one short neutral sentence saying only what the record itself establishes.
  Use the specific topic words from the record (for example folder access or delivery
  deadline) so the supporting point is easy to scan. Keep it narrower than the claim when
  needed: a record saying a link was shared does not establish that a password was shared.
  The app displays record timestamps separately. Never infer a date or repeat timestamp
  metadata in the statement.

An "unverified" claim may still list records that establish a related, narrower fact.
For "contradicted", add a short neutral note explaining the conflict without blaming anyone.
Only use the records provided. Never invent message IDs, quotes, dates or senders."""

SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "assessments": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "claim_index": {"type": "integer"},
                    "status": {"type": "string", "enum": ["supported", "contradicted", "unverified"]},
                    "evidence": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "message_id": {"type": "string"},
                                "quote": {"type": "string"},
                                "statement": {"type": "string"},
                            },
                            "required": ["message_id", "quote", "statement"],
                            "additionalProperties": False,
                        },
                    },
                    "note": {"type": "string"},
                },
                "required": ["claim_index", "status", "evidence", "note"],
                "additionalProperties": False,
            },
        }
    },
    "required": ["assessments"],
    "additionalProperties": False,
}

_QUOTE_CHARS = str.maketrans({"‘": "'", "’": "'", "“": '"', "”": '"', "–": "-", "—": "-"})


def normalise(text: str) -> str:
    text = unicodedata.normalize("NFKC", text).translate(_QUOTE_CHARS)
    return " ".join(text.split()).casefold()


def quote_in_record(quote: str, record: MemoryRecord) -> bool:
    q = normalise(quote)
    return len(q) >= MIN_QUOTE_CHARS and q in normalise(record.content)


def _clean(text: Any) -> str:
    return " ".join(text.split())[:MAX_TEXT_CHARS] if isinstance(text, str) else ""


def records_payload(records: Sequence[MemoryRecord]) -> list[dict[str, Any]]:
    return [
        {
            "message_id": r.id,
            "conversation_id": r.conversation_id,
            "sender": r.sender,
            "timestamp": r.timestamp,
            "content": r.content,
        }
        for r in records
    ]


def parse_assessment(data: dict[str, Any], claims: Sequence[str], records: Sequence[MemoryRecord]) -> EvidenceAssessment:
    items = data.get("assessments")
    if not isinstance(items, list):
        raise ModelError("assessment: assessments missing")
    by_id = {r.id: r for r in records}
    results: dict[int, ClaimAssessment] = {}

    for item in items:
        if not isinstance(item, dict):
            raise ModelError("assessment: item is not an object")
        idx, status, evidence = item.get("claim_index"), item.get("status"), item.get("evidence")
        if not isinstance(idx, int) or isinstance(idx, bool) or not 0 <= idx < len(claims) or idx in results:
            continue  # unknown or duplicate claim reference: ignore
        if status not in ("supported", "contradicted", "unverified") or not isinstance(evidence, list):
            raise ModelError("assessment: invalid status or evidence")

        grounded: list[tuple[str, str]] = []
        for ev in evidence:
            if not isinstance(ev, dict):
                continue
            mid, quote, statement = ev.get("message_id"), ev.get("quote"), _clean(ev.get("statement"))
            record = by_id.get(mid) if isinstance(mid, str) else None
            if record is None or not isinstance(quote, str) or not statement:
                continue  # invented ID or incomplete reference
            if not quote_in_record(quote, record):
                continue  # altered or invented source text
            if mid not in [g[0] for g in grounded]:
                grounded.append((mid, statement))

        if status in ("supported", "contradicted") and not grounded:
            status = "unverified"
        note = _clean(item.get("note")) or None
        if status == "contradicted":
            results[idx] = ClaimAssessment(
                claim=claims[idx],
                status="contradicted",
                message_ids=tuple(m for m, _ in grounded),
                note=note or "A stored message appears to conflict with this claim.",
            )
        else:
            results[idx] = ClaimAssessment(
                claim=claims[idx],
                status=status,
                message_ids=tuple(m for m, _ in grounded),
                note=note if status == "unverified" else None,
                links=tuple(EvidenceLink(message_id=m, supported_claim=s) for m, s in grounded),
            )

    ordered = tuple(results.get(i) or ClaimAssessment(claim=c, status="unverified") for i, c in enumerate(claims))
    return EvidenceAssessment(claims=ordered)


# ---------------------------------------------------------------- reply checks

_BLAME = re.compile(
    r"\b(i\s+apologi[sz]e|i'?m\s+(so\s+|very\s+|really\s+)?sorry|i\s+am\s+(so\s+|very\s+|really\s+)?sorry|sorry\s+for|"
    r"apologies\s+for|my\s+(fault|mistake|bad|error)|i\s+take\s+(full\s+)?responsibility|i\s+should\s+have|it\s+was\s+my\s+fault)\b",
    re.IGNORECASE,
)
_MONTHS = r"(jan(uary)?|feb(ruary)?|mar(ch)?|apr(il)?|may|jun(e)?|jul(y)?|aug(ust)?|sep(t(ember)?)?|oct(ober)?|nov(ember)?|dec(ember)?)"
_DATE = re.compile(
    r"\b(\d{4}-\d{2}-\d{2}|\d{1,2}/\d{1,2}(/\d{2,4})?|\d{1,2}(st|nd|rd|th)?\s+(of\s+)?" + _MONTHS + r"\b|"
    + _MONTHS + r"\s+\d{1,2}(st|nd|rd|th)?\b|(mon|tues|wednes|thurs|fri|satur|sun)day|yesterday|last\s+week|"
    r"\d{1,2}(:\d{2})?\s*(am|pm)\b|\d{1,2}:\d{2})",
    re.IGNORECASE,
)
_VERIFIED_PHRASE = re.compile(
    r"\b(as\s+(confirmed|documented|shown|recorded|evidenced)|our\s+records\s+show|according\s+to\s+(our|the)\s+records|"
    r"as\s+per\s+your\s+(message|email)|in\s+your\s+(message|email)\s+(on|dated))\b",
    re.IGNORECASE,
)


def _token_present(token: str, haystack: str) -> bool:
    return normalise(token) in haystack


def check_draft(request: DraftInput, draft: ReplyDraft) -> list[str]:
    """Problems that make a draft unusable (safe, content-free descriptions)."""
    problems = list(_structural_problems(draft, request.assessment, request.records))
    reply = draft.reply if isinstance(draft.reply, str) else ""

    if _BLAME.search(reply) and not _BLAME.search(request.employee_draft):
        problems.append("reply apologises or accepts blame that the employee did not express")

    cited = {link.message_id for link in draft.evidence}
    grounding = normalise(
        " ".join(
            [request.manager_message, request.employee_draft]
            + [r.content for r in request.records if r.id in cited]
        )
    )
    for m in _DATE.finditer(reply):
        if not _token_present(m.group(0), grounding):
            problems.append("reply mentions a date or time not present in the inputs or cited evidence")
            break
    return problems


def _structural_problems(draft: ReplyDraft, assessment: EvidenceAssessment, records: Sequence[MemoryRecord]) -> list[str]:
    problems: list[str] = []
    reply = draft.reply
    if not isinstance(reply, str) or not reply.strip():
        return ["reply is empty"]
    if len(reply) > MAX_REPLY_CHARS:
        problems.append("reply is too long")

    record_ids = {r.id for r in records}
    allowed = {
        (link.message_id, link.supported_claim)
        for c in assessment.claims
        if c.status != "contradicted"
        for link in c.links
    }
    allowed_ids = {mid for mid, _ in allowed}
    contradicted_ids = {mid for c in assessment.claims if c.status == "contradicted" for mid in c.message_ids}

    for link in draft.evidence:
        if link.message_id not in record_ids:
            problems.append("reply cites a message that was not retrieved")
        elif link.message_id in contradicted_ids and link.message_id not in allowed_ids:
            problems.append("reply cites contradicting evidence as support")
        elif (link.message_id, link.supported_claim) not in allowed:
            problems.append("reply cites evidence for a statement the record does not support")

    lowered = reply.casefold()
    for rid in record_ids:
        if len(rid) >= 4 and re.search(r"(?<![\w-])" + re.escape(rid.casefold()) + r"(?![\w-])", lowered):
            problems.append("reply exposes internal message identifiers")
            break

    if _VERIFIED_PHRASE.search(reply) and not draft.evidence:
        problems.append("reply presents history as verified without supporting evidence")
    return problems


class ClaudeEvidenceService:
    def __init__(self, model: JsonModel) -> None:
        self._model = model

    def assess(self, owner: OwnerContext, *, analysis: MessageAnalysis, records: tuple[MemoryRecord, ...]) -> EvidenceAssessment:
        claims = list(analysis.claims)
        if not claims:
            return EvidenceAssessment(claims=())
        if not records:
            # No history: nothing can be supported or contradicted; no model call needed.
            return EvidenceAssessment(claims=tuple(ClaimAssessment(claim=c, status="unverified") for c in claims))
        assessment = call_with_retry(
            self._model,
            task="assessment",
            system=SYSTEM,
            payload={
                "claims": [{"claim_index": i, "claim": c} for i, c in enumerate(claims)],
                "records": records_payload(records),
            },
            schema=SCHEMA,
            max_tokens=16000,
            parse=lambda data: parse_assessment(data, claims, records),
        )
        return review_assessment(self._model, assessment, records)

    def validate(
        self,
        owner: OwnerContext,
        *,
        draft: ReplyDraft,
        request: DraftInput,
    ) -> ValidatedReply:
        assessment, records = request.assessment, request.records
        problems = check_draft(request, draft)
        if problems:
            raise EvidenceValidationError("; ".join(sorted(set(problems))))
        review_draft(self._model, request, draft)

        # Deduplicate evidence by message ID, keeping the first statement.
        evidence: list[EvidenceLink] = []
        for link in draft.evidence:
            if link.message_id not in [e.message_id for e in evidence]:
                evidence.append(link)

        warnings = list(draft.warnings)
        for c in assessment.claims:
            if c.status == "contradicted":
                warnings.append(
                    f"Conflicting history: the claim \"{c.claim}\" is not supported as stated. {c.note}".strip()
                )
        unverified = tuple(c.claim for c in assessment.claims if c.status == "unverified")
        return ValidatedReply(reply=draft.reply, evidence=tuple(evidence), unverified_claims=unverified, warnings=tuple(warnings))
