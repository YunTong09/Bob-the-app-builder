"""DEVELOPMENT TEST DOUBLES -- not production code, not Developer 3's services.

Used by integration tests and by ``R2R_SERVICES=stub`` so the frontend can
integrate before the real services land. The AI doubles return canned text
(no Claude call) and the evidence double only does a crude keyword-overlap
check. Nothing here counts as a completed AI, storage or evidence feature.
"""

from __future__ import annotations

import re
import threading
from typing import Sequence

from backend.application.errors import MemoryIdConflictError, ModelError
from backend.application.ports import (
    ClaimAssessment,
    DraftInput,
    EvidenceAssessment,
    EvidenceLink,
    ImportResult,
    MemoryRecord,
    MessageAnalysis,
    OwnerContext,
    ReplyDraft,
    SearchPage,
    Services,
    ValidatedReply,
)

_WORD = re.compile(r"\w+", re.UNICODE)
_STOP = {
    "the", "a", "an", "and", "or", "to", "of", "in", "on", "it", "is", "i", "you",
    "me", "my", "for", "that", "this", "be", "was", "are", "have", "has", "not",
    "please", "still", "why", "yet", "because", "can", "can't", "t", "s",
}


def _terms(text: str) -> list[str]:
    return [w.lower() for w in _WORD.findall(text)]


def _keywords(text: str) -> set[str]:
    return {w for w in _terms(text) if w not in _STOP and len(w) > 2}


class InMemoryMemoryService:
    """Contract-faithful in-memory store (owner-scoped, atomic import)."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._data: dict[str, dict[str, MemoryRecord]] = {}

    def _owned(self, owner: OwnerContext, conversation_id: str | None) -> list[MemoryRecord]:
        records = list(self._data.get(owner.owner_id, {}).values())
        if conversation_id is not None:
            records = [r for r in records if r.conversation_id == conversation_id]
        return records

    def import_messages(self, owner: OwnerContext, records: Sequence[MemoryRecord]) -> ImportResult:
        with self._lock:
            existing = self._data.get(owner.owner_id, {})
            conflicts = tuple(r.id for r in records if r.id in existing and existing[r.id] != r)
            if conflicts:
                raise MemoryIdConflictError(conflicts)
            new = [r for r in records if r.id not in existing]
            store = self._data.setdefault(owner.owner_id, {})
            for r in new:
                store[r.id] = r
            return ImportResult(imported_count=len(new), skipped_count=len(records) - len(new))

    def search(self, owner: OwnerContext, *, query: str | None, conversation_id: str | None, limit: int, offset: int) -> SearchPage:
        with self._lock:
            records = self._owned(owner, conversation_id)
        if query is None:
            ordered = sorted(records, key=lambda r: r.id)
        else:
            terms = _terms(query)
            if not terms:
                return SearchPage(records=(), total=0)
            scored = []
            for r in records:
                words = _terms(r.content)
                if all(t in words for t in terms):
                    scored.append((-sum(words.count(t) for t in terms), r.id, r))
            ordered = [r for *_, r in sorted(scored, key=lambda x: (x[0], x[1]))]
        return SearchPage(records=tuple(ordered[offset : offset + limit]), total=len(ordered))

    def retrieve(self, owner: OwnerContext, *, queries: Sequence[str], conversation_id: str | None, limit: int) -> tuple[MemoryRecord, ...]:
        wanted = set().union(*(_keywords(q) for q in queries)) if queries else set()
        with self._lock:
            records = self._owned(owner, conversation_id)
        scored = [(len(wanted & _keywords(r.content)), r) for r in records]
        hits = sorted((s for s in scored if s[0] > 0), key=lambda x: (-x[0], x[1].id))
        return tuple(r for _, r in hits[:limit])

    def delete_all(self, owner: OwnerContext) -> int:
        with self._lock:
            return len(self._data.pop(owner.owner_id, {}))


class StubAnalysisService:
    def analyse(self, owner: OwnerContext, *, manager_message: str, employee_draft: str) -> MessageAnalysis:
        claims = tuple(s.strip() for s in re.split(r"(?<=[.!?])\s+", employee_draft) if s.strip())
        return MessageAnalysis(
            manager_intent="[stub] The manager's explicit request has not been analysed by Claude.",
            employee_concern="[stub] The employee's concern has not been analysed by Claude.",
            claims=claims,
            search_queries=claims + (manager_message,),
            warnings=("Development stub: analysis is not AI-generated.",),
        )


class StubEvidenceService:
    """Crude keyword-overlap double. NOT the production evidence validator."""

    def assess(self, owner: OwnerContext, *, analysis: MessageAnalysis, records: tuple[MemoryRecord, ...]) -> EvidenceAssessment:
        out = []
        for claim in analysis.claims:
            ids = tuple(r.id for r in records if len(_keywords(claim) & _keywords(r.content)) >= 2)
            out.append(ClaimAssessment(claim=claim, status="supported" if ids else "unverified", message_ids=ids))
        return EvidenceAssessment(claims=tuple(out))

    def validate(self, owner: OwnerContext, *, draft: ReplyDraft, request: DraftInput) -> ValidatedReply:
        known = {r.id for r in request.records}
        if any(link.message_id not in known for link in draft.evidence):
            raise ModelError("draft references unknown record")
        return ValidatedReply(
            reply=draft.reply,
            evidence=draft.evidence,
            unverified_claims=tuple(c.claim for c in request.assessment.claims if c.status != "supported"),
            warnings=draft.warnings,
        )


class StubDraftingService:
    def draft(self, owner: OwnerContext, request: DraftInput) -> ReplyDraft:
        links = tuple(
            EvidenceLink(message_id=mid, supported_claim=c.claim)
            for c in request.assessment.claims
            if c.status == "supported"
            for mid in c.message_ids[:1]
        )
        return ReplyDraft(
            reply=f"[stub {request.tone} reply] Hi, thanks for your message. "
            "I'd like to clarify a few points so we can move forward.",
            evidence=links,
        )


def build_stub_services() -> Services:
    return Services(
        memory=InMemoryMemoryService(),
        analysis=StubAnalysisService(),
        evidence=StubEvidenceService(),
        drafting=StubDraftingService(),
    )
