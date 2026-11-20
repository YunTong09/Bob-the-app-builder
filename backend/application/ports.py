"""Service interfaces between the application layer (Developer 2) and the
AI / memory / evidence services (Developer 3).

PROPOSED HANDOFF -- pending Developer 3 sign-off. Changes here must be agreed
by both owners because the orchestrator and Developer 3's implementations both
depend on them.

Rules every implementation must follow:

* Every operation receives the same ``OwnerContext``. Ownership (and any
  ``conversation_id`` restriction) is applied inside the storage query before
  ranking, counting or limiting. Implementations must never fall back to an
  unscoped query; if the owner cannot be applied, raise ``OwnershipError``.
* Domain types here are plain frozen dataclasses with snake_case names; they are
  NOT wire models. ``backend/models/wire.py`` owns the HTTP shapes and the
  orchestrator converts between them.
* Missing metadata is ``None``; never substitute import time or invent a source.
* Raise only the failure types in ``backend/application/errors.py``. Any other
  exception is treated as an unexpected internal error (HTTP 500).
* Implementations must not log raw manager messages, employee drafts, prompts
  or provider responses.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal, Protocol, Sequence

ReplyTone = Literal["diplomatic", "neutral", "assertive"]


# --------------------------------------------------------------------------
# Identity
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class OwnerContext:
    """Server-derived owner. Never built from client-supplied IDs."""

    owner_id: str
    mode: Literal["demo_local", "authenticated"]

    def __post_init__(self) -> None:
        if not self.owner_id or self.owner_id.strip() != self.owner_id:
            raise ValueError("owner_id must be a non-empty, trimmed string")


# --------------------------------------------------------------------------
# Memory records
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class MemoryRecord:
    """A stored message visible to the current owner."""

    id: str
    conversation_id: str
    sender: str
    content: str
    timestamp: str | None  # RFC 3339 string exactly as imported, or None
    source: str | None  # source label exactly as imported, or None


@dataclass(frozen=True)
class ImportResult:
    imported_count: int
    skipped_count: int


@dataclass(frozen=True)
class SearchPage:
    records: tuple[MemoryRecord, ...]
    total: int  # all matches for owner (+ conversation) before pagination


class MemoryService(Protocol):
    def import_messages(
        self, owner: OwnerContext, records: Sequence[MemoryRecord]
    ) -> ImportResult:
        """Atomically store records (messages + FTS index in one transaction).

        The orchestrator guarantees: 1-100 records, unique IDs within the batch,
        all fields already validated. Identical existing records (same
        conversation, sender, content, timestamp and source) are skipped. Any
        differing existing record for this owner raises ``MemoryIdConflictError``
        and nothing is stored. ``imported + skipped == len(records)``.
        """
        ...

    def search(
        self,
        owner: OwnerContext,
        *,
        query: str | None,
        conversation_id: str | None,
        limit: int,
        offset: int,
    ) -> SearchPage:
        """History review / search.

        ``query`` is None for "list saved history" (order by id ascending).
        Otherwise it is literal user text: split into terms joined with AND
        (never raw FTS/SQL); order by relevance then id ascending. A query with
        no searchable terms returns no matches.
        """
        ...

    def retrieve(
        self,
        owner: OwnerContext,
        *,
        queries: Sequence[str],
        conversation_id: str | None,
        limit: int,
    ) -> tuple[MemoryRecord, ...]:
        """Retrieve candidate evidence for generation (owner-scoped, at most
        ``limit`` records). Raise ``StorageUnavailableError`` on outage; never
        return partial results."""
        ...

    def delete_all(self, owner: OwnerContext) -> int:
        """Delete all of the owner's messages and their FTS entries in one
        transaction. Must not touch other owners or preferences."""
        ...


# --------------------------------------------------------------------------
# Analysis
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class MessageAnalysis:
    manager_intent: str  # explicit requests; interpretations labelled as such
    employee_concern: str
    claims: tuple[str, ...]  # factual claims extracted from the employee draft
    search_queries: tuple[str, ...]  # plain-text queries for MemoryService.retrieve
    warnings: tuple[str, ...] = ()  # missing information, possible misunderstandings


class AnalysisService(Protocol):
    def analyse(
        self, owner: OwnerContext, *, manager_message: str, employee_draft: str
    ) -> MessageAnalysis:
        """Raise ``ModelTimeoutError`` / ``ModelError`` on Claude failure or
        unusable output."""
        ...


# --------------------------------------------------------------------------
# Evidence assessment, drafting and validation
# --------------------------------------------------------------------------

ClaimStatus = Literal["supported", "contradicted", "unverified"]


@dataclass(frozen=True)
class EvidenceLink:
    """A reference from a statement to a stored record. Carries no content:
    the orchestrator fills content/sender/timestamp/source from the authorised
    record so the model can never supply or alter source text."""

    message_id: str
    supported_claim: str


@dataclass(frozen=True)
class ClaimAssessment:
    claim: str
    status: ClaimStatus
    message_ids: tuple[str, ...] = ()  # records supporting/contradicting the claim
    note: str | None = None  # e.g. explanation of a contradiction
    # Verified support: what each record actually establishes (may be narrower
    # than the claim, e.g. "The manager shared a document location."). Only
    # links whose quote was found verbatim in the record are kept. Empty for
    # contradicted claims. (Additive field agreed by Developers 2 and 3.)
    links: tuple["EvidenceLink", ...] = ()


@dataclass(frozen=True)
class EvidenceAssessment:
    claims: tuple[ClaimAssessment, ...]


@dataclass(frozen=True)
class DraftInput:
    manager_message: str
    employee_draft: str
    tone: ReplyTone
    analysis: MessageAnalysis
    assessment: EvidenceAssessment
    records: tuple[MemoryRecord, ...]  # authorised records only; untrusted content


@dataclass(frozen=True)
class ReplyDraft:
    reply: str
    evidence: tuple[EvidenceLink, ...]
    warnings: tuple[str, ...] = ()


@dataclass(frozen=True)
class ValidatedReply:
    """Output of the evidence validator: the only evidence the API may return."""

    reply: str
    evidence: tuple[EvidenceLink, ...]  # each ID is in the authorised records AND supports its claim
    unverified_claims: tuple[str, ...]
    warnings: tuple[str, ...] = field(default_factory=tuple)  # incl. contradiction explanations


class EvidenceService(Protocol):
    def assess(
        self,
        owner: OwnerContext,
        *,
        analysis: MessageAnalysis,
        records: tuple[MemoryRecord, ...],
    ) -> EvidenceAssessment:
        """Classify each claim as supported / contradicted / unverified against
        the records. Empty records => every claim unverified (missing history is
        not proof a claim is false)."""
        ...

    def validate(
        self,
        owner: OwnerContext,
        *,
        draft: ReplyDraft,
        assessment: EvidenceAssessment,
        records: tuple[MemoryRecord, ...],
    ) -> ValidatedReply:
        """Final check before returning a reply. Must reject references to IDs
        not in ``records`` and links whose record does not support the claim,
        and must not present contradicted claims as supported. Raise
        ``EvidenceValidationError`` if the draft is unusable (e.g. invented
        references the reply depends on)."""
        ...


class DraftingService(Protocol):
    def draft(self, owner: OwnerContext, request: DraftInput) -> ReplyDraft:
        """Raise ``ModelTimeoutError`` / ``ModelError`` on Claude failure or
        unusable output."""
        ...


@dataclass(frozen=True)
class Services:
    memory: MemoryService
    analysis: AnalysisService
    evidence: EvidenceService
    drafting: DraftingService
