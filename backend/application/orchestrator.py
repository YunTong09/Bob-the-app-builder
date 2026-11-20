"""Application service: orchestrates P0 use cases independent of HTTP.

Owned by Developer 2. A future Slack adapter (or any other presentation layer)
should call ``RageToReplyApp`` directly with an ``OwnerContext`` it has derived
server-side; nothing in here depends on FastAPI or wire models.

This module deliberately contains no evidence-support logic -- that belongs to
Developer 3's ``EvidenceService``. It only enforces structural invariants at the
response boundary (every returned reference resolves to an authorised record
retrieved in this request, so content/metadata come from storage, not the model).
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Sequence

from .errors import ModelError, OwnershipError, StorageUnavailableError
from .ports import (
    DraftInput,
    MemoryRecord,
    OwnerContext,
    ReplyDraft,
    ReplyTone,
    SearchPage,
    Services,
    ValidatedReply,
)

log = logging.getLogger("rage_to_reply.app")

RETRIEVAL_LIMIT = 20

WARNING_NO_HISTORY = (
    "No supporting history was found, so claims are shown as user-reported "
    "rather than verified."
)
WARNING_RETRIEVAL_FAILED = (
    "Conversation history could not be searched right now, so this reply was "
    "generated without evidence. This does not mean no history exists."
)


@dataclass(frozen=True)
class ResolvedEvidence:
    message_id: str
    content: str
    sender: str
    timestamp: str | None
    source: str | None
    supported_claim: str


@dataclass(frozen=True)
class GeneratedReply:
    reply: str
    manager_intent: str
    employee_concern: str
    evidence: tuple[ResolvedEvidence, ...]
    unverified_claims: tuple[str, ...]
    warnings: tuple[str, ...]


def _dedupe(items: Sequence[str]) -> tuple[str, ...]:
    seen: dict[str, None] = {}
    for item in items:
        if isinstance(item, str) and item.strip():
            seen.setdefault(item, None)
    return tuple(seen)


def _require_text(value: object) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ModelError("model output missing required text")
    return value


class RageToReplyApp:
    def __init__(self, services: Services) -> None:
        self._s = services

    # ------------------------------------------------------------------ generate
    def generate_reply(
        self,
        owner: OwnerContext,
        *,
        manager_message: str,
        employee_draft: str,
        tone: ReplyTone,
        conversation_id: str | None,
    ) -> GeneratedReply:
        _require_owner(owner)
        # Nothing here persists the manager message or the draft.

        analysis = self._s.analysis.analyse(
            owner, manager_message=manager_message, employee_draft=employee_draft
        )

        retrieval_failed = False
        try:
            records = tuple(
                self._s.memory.retrieve(
                    owner,
                    queries=analysis.search_queries,
                    conversation_id=conversation_id,
                    limit=RETRIEVAL_LIMIT,
                )
            )
        except StorageUnavailableError:
            # Ownership is already established (owner validated above and
            # OwnershipError is not caught here). Discard any partial results.
            log.warning("retrieval unavailable; using warned fallback")
            records = ()
            retrieval_failed = True

        _check_retrieved(records, conversation_id)

        assessment = self._s.evidence.assess(owner, analysis=analysis, records=records)
        draft: ReplyDraft = self._s.drafting.draft(
            owner,
            DraftInput(
                manager_message=manager_message,
                employee_draft=employee_draft,
                tone=tone,
                analysis=analysis,
                assessment=assessment,
                records=records,
            ),
        )
        validated: ValidatedReply = self._s.evidence.validate(
            owner, draft=draft, assessment=assessment, records=records
        )

        by_id = {r.id: r for r in records}
        evidence: list[ResolvedEvidence] = []
        for link in validated.evidence:
            record = by_id.get(link.message_id)
            if record is None:
                # Validator let through a reference outside this request's
                # authorised records: never return it.
                raise ModelError("validated evidence references an unknown record")
            evidence.append(
                ResolvedEvidence(
                    message_id=record.id,
                    content=record.content,
                    sender=record.sender,
                    timestamp=record.timestamp,
                    source=record.source,
                    supported_claim=_require_text(link.supported_claim),
                )
            )

        warnings = list(analysis.warnings) + list(validated.warnings)
        if retrieval_failed:
            warnings.append(WARNING_RETRIEVAL_FAILED)
        elif not evidence:
            warnings.append(WARNING_NO_HISTORY)

        return GeneratedReply(
            reply=_require_text(validated.reply),
            manager_intent=_require_text(analysis.manager_intent),
            employee_concern=_require_text(analysis.employee_concern),
            evidence=tuple(evidence),
            unverified_claims=_dedupe(validated.unverified_claims),
            warnings=_dedupe(warnings),
        )

    # ------------------------------------------------------------------ memory
    def import_memory(
        self, owner: OwnerContext, records: Sequence[MemoryRecord]
    ) -> tuple[int, int]:
        _require_owner(owner)
        result = self._s.memory.import_messages(owner, tuple(records))
        if (
            result.imported_count < 0
            or result.skipped_count < 0
            or result.imported_count + result.skipped_count != len(records)
        ):
            raise RuntimeError("import counts do not match submitted messages")
        return result.imported_count, result.skipped_count

    def search_memory(
        self,
        owner: OwnerContext,
        *,
        query: str | None,
        conversation_id: str | None,
        limit: int,
        offset: int,
    ) -> SearchPage:
        _require_owner(owner)
        page = self._s.memory.search(
            owner,
            query=query,
            conversation_id=conversation_id,
            limit=limit,
            offset=offset,
        )
        if page.total < 0 or len(page.records) > limit:
            raise RuntimeError("search page violates limits")
        _check_retrieved(page.records, conversation_id)
        return page

    def delete_memory(self, owner: OwnerContext) -> int:
        _require_owner(owner)
        deleted = self._s.memory.delete_all(owner)
        if not isinstance(deleted, int) or deleted < 0:
            raise RuntimeError("invalid deleted count")
        return deleted


def _require_owner(owner: object) -> None:
    if not isinstance(owner, OwnerContext):
        raise OwnershipError("owner context missing")


def _check_retrieved(records: Sequence[MemoryRecord], conversation_id: str | None) -> None:
    """Structural guard against a storage bug leaking out-of-scope records."""
    for r in records:
        if not isinstance(r, MemoryRecord):
            raise RuntimeError("storage returned a non-record")
        if conversation_id is not None and r.conversation_id != conversation_id:
            raise OwnershipError("storage returned a record outside the requested conversation")
