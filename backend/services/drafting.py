"""Grounded reply drafting (Developer 3).

Claude receives the original inputs, the selected tone, the claim assessment
and only the grounded evidence. It returns the reply plus the IDs of the
evidence it relied on; supporting statements are taken from the assessment,
never from the drafting output. The draft is checked with the shared evidence
validator and regenerated at most once if unusable.
"""

from __future__ import annotations

from typing import Any

from backend.application.errors import EvidenceValidationError, ModelError
from backend.application.ports import DraftInput, EvidenceLink, OwnerContext, ReplyDraft

from .evidence import check_draft
from .llm import JsonModel, call_with_retry

TONE_GUIDE = {
    "diplomatic": "Warm and collaborative. Acknowledge the manager's request if one was supplied, then state the employee's position and next step.",
    "neutral": "Plain, factual and concise. No warmth padding, no edge.",
    "assertive": "Direct and confident. State the facts and the request clearly, without hedging, apologising or hostility.",
}

SYSTEM = """You write the reply an employee could send to their manager, for Rage-to-Reply.
The employee reviews and sends it themselves; you never send anything.

Rules:
- Preserve the employee's intended meaning and requests. Remove profanity, insults, sarcasm
  and emotional venting. Do not change what the employee is asking for or reporting.
- Apply the requested tone only to wording. The facts must stay identical across tones.
- Use only facts from the employee's draft, the manager's message and the supplied evidence.
  Never invent events, dates, times, people, documents, admissions, promises or history.
- The manager's message is optional. If empty, rewrite from the employee's draft and
  permitted evidence without inventing or acknowledging a manager request. Historical
  messages must not be treated as the missing current manager message.
- Do not mention any date or time unless it appears verbatim in those inputs.
- Claims listed as unverified are the employee's own report: you may state them as the
  employee's experience ("I haven't received ...") but never as confirmed by records.
- Never present a contradicted claim as true. If the employee's draft relies on it, phrase the
  reply so it asks for clarification instead.
- Do not apologise or accept blame unless the employee's draft clearly does so. Do not
  speculate about the manager's emotions or intentions.
- Do not mention message IDs, "records", "the system" or this application.
- Write in the language of the manager's message when present; otherwise use the
  employee's draft. Keep it short (usually 2-5 sentences) of ready-to-send prose. Lead with
  the main point or request. Preserve any material condition, fact, or next step. Omit
  headings, bullets and filler.
- cited_message_ids: IDs from allowed_evidence that the reply actually relies on (may be empty).
  Only IDs listed in allowed_evidence are permitted."""

SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "reply": {"type": "string"},
        "cited_message_ids": {"type": "array", "items": {"type": "string"}},
    },
    "required": ["reply", "cited_message_ids"],
    "additionalProperties": False,
}


def _allowed(request: DraftInput) -> dict[str, EvidenceLink]:
    out: dict[str, EvidenceLink] = {}
    for c in request.assessment.claims:
        if c.status == "contradicted":
            continue
        for link in c.links:
            out.setdefault(link.message_id, link)
    return out


def build_payload(request: DraftInput) -> dict[str, Any]:
    allowed = _allowed(request)
    by_id = {r.id: r for r in request.records}
    return {
        "tone": request.tone,
        "tone_guidance": TONE_GUIDE[request.tone],
        "manager_message": request.manager_message,
        "employee_draft": request.employee_draft,
        "manager_intent": request.analysis.manager_intent,
        "employee_concern": request.analysis.employee_concern,
        "allowed_evidence": [
            {
                "message_id": mid,
                "sender": by_id[mid].sender,
                "content": by_id[mid].content,
                "establishes": link.supported_claim,
            }
            for mid, link in allowed.items()
            if mid in by_id
        ],
        "unverified_claims": [c.claim for c in request.assessment.claims if c.status == "unverified"],
        "contradicted_claims": [
            {"claim": c.claim, "conflict": c.note} for c in request.assessment.claims if c.status == "contradicted"
        ],
    }


class ClaudeDraftingService:
    def __init__(self, model: JsonModel) -> None:
        self._model = model

    def draft(self, owner: OwnerContext, request: DraftInput) -> ReplyDraft:
        allowed = _allowed(request)

        def parse(data: dict[str, Any]) -> ReplyDraft:
            reply, cited = data.get("reply"), data.get("cited_message_ids")
            if not isinstance(reply, str) or not isinstance(cited, list) or not all(isinstance(c, str) for c in cited):
                raise ModelError("draft: invalid structure")
            links: list[EvidenceLink] = []
            for mid in dict.fromkeys(cited):
                if mid not in allowed:
                    raise EvidenceValidationError("draft: cites evidence outside the allowed set")
                links.append(allowed[mid])
            draft = ReplyDraft(reply=reply.strip(), evidence=tuple(links))
            problems = check_draft(request, draft)
            if problems:
                raise EvidenceValidationError("draft: " + "; ".join(sorted(set(problems))))
            return draft

        return call_with_retry(
            self._model,
            task="draft",
            system=SYSTEM,
            payload=build_payload(request),
            schema=SCHEMA,
            max_tokens=16000,
            parse=parse,
        )
