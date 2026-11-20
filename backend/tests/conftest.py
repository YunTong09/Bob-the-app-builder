"""Test wiring. Claude is never called: AI services are programmable doubles.

Memory uses the in-memory double by default. To run the same API tests against
Developer 3's store, set R2R_TEST_MEMORY_FACTORY=module:callable (a zero-arg
callable returning a fresh MemoryService).
"""

from __future__ import annotations

import importlib
import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

import pytest
from fastapi import Request
from fastapi.testclient import TestClient

from backend.api.app import create_app
from backend.api.errors import ApiError
from backend import config
from backend.application.ports import (
    DraftInput,
    EvidenceAssessment,
    MemoryRecord,
    MessageAnalysis,
    OwnerContext,
    ReplyDraft,
    Services,
    ValidatedReply,
)
from backend.devstubs import InMemoryMemoryService

FIXTURES = Path(__file__).resolve().parent.parent / "fixtures"
OWNER_HEADER = "X-Test-Owner"


@pytest.fixture(autouse=True)
def isolate_local_backend_env(monkeypatch, tmp_path_factory):
    """Unit/integration tests must never load a developer's real credentials."""
    monkeypatch.setattr(config, "DEFAULT_ENV_FILE", tmp_path_factory.getbasetemp() / "absent-backend.env")


def load_fixture(name: str) -> Any:
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


def header_identity(request: Request) -> OwnerContext:
    """Test-only resolver standing in for authenticated sessions."""
    owner = request.headers.get(OWNER_HEADER)
    if not owner:
        raise ApiError(401, "UNAUTHENTICATED", "Authentication is required.")
    return OwnerContext(owner_id=owner, mode="authenticated")


def _memory_factory() -> Callable[[], Any]:
    spec = os.environ.get("R2R_TEST_MEMORY_FACTORY")
    if not spec:
        return InMemoryMemoryService
    module, _, attr = spec.partition(":")
    return getattr(importlib.import_module(module), attr)


@dataclass
class FakeAI:
    """Programmable analysis / evidence / drafting doubles that record calls."""

    analysis: MessageAnalysis | Exception = field(
        default_factory=lambda: MessageAnalysis(
            manager_intent="The manager is asking why the documents have not been accessed.",
            employee_concern="The employee reports being unable to access the protected link.",
            claims=("The link asks for a password.",),
            search_queries=("documents shared drive",),
        )
    )
    assessment: EvidenceAssessment | Exception = field(default_factory=lambda: EvidenceAssessment(claims=()))
    draft_result: ReplyDraft | Exception | None = None
    validated: ValidatedReply | Callable[..., ValidatedReply] | Exception | None = None
    calls: list[tuple[str, Any]] = field(default_factory=list)

    # AnalysisService
    def analyse(self, owner: OwnerContext, *, manager_message: str, employee_draft: str) -> MessageAnalysis:
        self.calls.append(("analyse", owner))
        if isinstance(self.analysis, Exception):
            raise self.analysis
        return self.analysis

    # EvidenceService
    def assess(self, owner: OwnerContext, *, analysis: MessageAnalysis, records: tuple[MemoryRecord, ...]) -> EvidenceAssessment:
        self.calls.append(("assess", (owner, records)))
        if isinstance(self.assessment, Exception):
            raise self.assessment
        return self.assessment

    def validate(self, owner: OwnerContext, *, draft: ReplyDraft, request: DraftInput) -> ValidatedReply:
        self.calls.append(("validate", (owner, draft, request)))
        v = self.validated
        if isinstance(v, Exception):
            raise v
        if callable(v):
            return v(draft=draft, records=request.records)
        if v is None:
            return ValidatedReply(reply=draft.reply, evidence=draft.evidence, unverified_claims=(), warnings=draft.warnings)
        return v

    # DraftingService
    def draft(self, owner: OwnerContext, request: DraftInput) -> ReplyDraft:
        self.calls.append(("draft", (owner, request)))
        if isinstance(self.draft_result, Exception):
            raise self.draft_result
        return self.draft_result or ReplyDraft(reply="Hi, could you please share the password for the document link?", evidence=())

    def names(self) -> list[str]:
        return [c[0] for c in self.calls]


@pytest.fixture
def ai() -> FakeAI:
    return FakeAI()


@pytest.fixture
def memory() -> Any:
    return _memory_factory()()


@pytest.fixture
def services(ai: FakeAI, memory: Any) -> Services:
    return Services(memory=memory, analysis=ai, evidence=ai, drafting=ai)


@pytest.fixture
def client(services: Services) -> TestClient:
    app = create_app(services, header_identity)
    return TestClient(app, headers={OWNER_HEADER: "owner-a"}, raise_server_exceptions=False)


GEN_BODY = {
    "managerMessage": "Why haven't you accessed the documents yet?",
    "employeeDraft": "SECRET-DRAFT-TEXT I still can't open the link because it asks for a password.",
    "tone": "neutral",
}


def import_fixture(client: TestClient, owner: str = "owner-a") -> None:
    r = client.post("/api/memory/import", json=load_fixture("import_request.json"), headers={OWNER_HEADER: owner})
    assert r.status_code == 200, r.text
