"""Full HTTP -> orchestrator -> Developer 3 services -> SQLite flow, Claude scripted."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from backend.api.app import create_app
from backend.application.ports import Services
from backend.memory.sqlite_store import SqliteMemoryService
from backend.services.analysis import ClaudeAnalysisService
from backend.services.drafting import ClaudeDraftingService
from backend.services.evidence import ClaudeEvidenceService
from backend.services.mock import MOCK_PREFIX, MockJsonModel

from .conftest import OWNER_HEADER, header_identity, load_fixture
from .test_ai_services import Scripted
from .test_boundary import assert_error

ANALYSIS = {
    "explicit_requests": ["Explain why the documents have not been accessed"],
    "possible_actions": [],
    "missing_information": [],
    "potential_misunderstandings": [],
    "employee_concern": "The employee reports being unable to access the protected link.",
    "claims": ["The employee reports that opening the link requires a password."],
    "search_queries": ["documents shared drive"],
}
ASSESSMENT = {
    "assessments": [
        {
            "claim_index": 0,
            "status": "unverified",
            "evidence": [{"message_id": "msg_001", "quote": "uploaded the documents to the shared drive", "statement": "The manager shared a document location."}],
            "note": "",
        }
    ]
}
EXPECTED = load_fixture("generate_response.json")
DRAFT = {"reply": EXPECTED["reply"], "cited_message_ids": ["msg_001"]}


def make_client(tmp_path, model):
    memory = SqliteMemoryService(tmp_path / "m.sqlite3")
    services = Services(memory, ClaudeAnalysisService(model), ClaudeEvidenceService(model), ClaudeDraftingService(model))
    return TestClient(create_app(services, header_identity), headers={OWNER_HEADER: "owner-a"}, raise_server_exceptions=False)


def test_contract_example_end_to_end(tmp_path):
    model = Scripted(analysis=[ANALYSIS], assessment=[ASSESSMENT], draft=[DRAFT])
    c = make_client(tmp_path, model)
    assert c.post("/api/memory/import", json=load_fixture("import_request.json")).status_code == 200
    r = c.post("/api/reply/generate", json=load_fixture("generate_request.json"))
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["reply"] == EXPECTED["reply"]
    assert body["evidence"] == EXPECTED["evidence"]  # hydrated from SQLite, incl. source
    assert body["unverifiedClaims"] == EXPECTED["unverifiedClaims"]
    assert body["managerIntent"].startswith("Explicit request:")
    assert [t for t, _ in model.calls] == ["analysis", "assessment", "draft"]
    # Retrieval was owner+conversation scoped and nothing from the request was stored.
    assert {r["message_id"] for r in model.calls[1][1]["records"]} <= {"msg_001", "msg_002"}
    assert c.get("/api/memory/search").json()["total"] == 2


def test_other_owner_history_never_reaches_claude(tmp_path):
    model = Scripted(analysis=[ANALYSIS], draft=[{"reply": "Could you share the password?", "cited_message_ids": []}])
    c = make_client(tmp_path, model)
    c.post("/api/memory/import", json=load_fixture("import_request.json"), headers={OWNER_HEADER: "owner-b"})
    body = c.post("/api/reply/generate", json=load_fixture("generate_request.json")).json()
    assert body["evidence"] == []
    assert any("No supporting history" in w for w in body["warnings"])
    assert "assessment" not in [t for t, _ in model.calls]  # no records -> no assessment call


def test_deleted_history_not_used(tmp_path):
    model = Scripted(analysis=[ANALYSIS], draft=[{"reply": "Could you share the password?", "cited_message_ids": []}])
    c = make_client(tmp_path, model)
    c.post("/api/memory/import", json=load_fixture("import_request.json"))
    assert c.delete("/api/memory").json() == {"deletedCount": 2}
    assert c.post("/api/reply/generate", json=load_fixture("generate_request.json")).json()["evidence"] == []


def test_invented_citation_twice_is_502(tmp_path):
    bad = {"reply": "Per your message, fine.", "cited_message_ids": ["msg_404"]}
    c = make_client(tmp_path, Scripted(analysis=[ANALYSIS], assessment=[ASSESSMENT], draft=[bad, bad]))
    c.post("/api/memory/import", json=load_fixture("import_request.json"))
    r = c.post("/api/reply/generate", json=load_fixture("generate_request.json"))
    assert_error(r, 502, "MODEL_ERROR")
    assert "msg_404" not in r.text and "password" not in r.text


@pytest.mark.parametrize("tone", ["diplomatic", "neutral", "assertive"])
def test_mock_mode_end_to_end(tmp_path, tone):
    c = make_client(tmp_path, MockJsonModel())
    c.post("/api/memory/import", json=load_fixture("import_request.json"))
    req = {**load_fixture("generate_request.json"), "tone": tone, "employeeDraft": "I can't find the documents on the shared drive."}
    body = c.post("/api/reply/generate", json=req).json()
    assert body["reply"].startswith(MOCK_PREFIX)
    assert {e["messageId"] for e in body["evidence"]} <= {"msg_001", "msg_002"}
    assert body["evidence"] and all(e["content"] for e in body["evidence"])
    assert body["unverifiedClaims"] == ["I can't find the documents on the shared drive."]
