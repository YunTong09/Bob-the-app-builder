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
from .test_ai_services import APPROVED_DRAFT_REVIEW, Scripted, approved_assessment_review
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
    model = Scripted(
        analysis=[ANALYSIS],
        assessment=[ASSESSMENT],
        assessment_review=[approved_assessment_review(1)],
        draft=[DRAFT],
        draft_review=[APPROVED_DRAFT_REVIEW],
    )
    c = make_client(tmp_path, model)
    assert c.post("/api/memory/import", json=load_fixture("import_request.json")).status_code == 200
    r = c.post("/api/reply/generate", json=load_fixture("generate_request.json"))
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["reply"] == EXPECTED["reply"]
    assert body["evidence"] == EXPECTED["evidence"]  # hydrated from SQLite, incl. source
    assert body["unverifiedClaims"] == EXPECTED["unverifiedClaims"]
    assert body["managerIntent"].startswith("Explicit request:")
    assert [t for t, _ in model.calls] == ["analysis", "assessment", "assessment_review", "draft", "draft_review"]
    # Retrieval was owner+conversation scoped and nothing from the request was stored.
    assert {r["message_id"] for r in model.calls[1][1]["records"]} <= {"msg_001", "msg_002"}
    assert c.get("/api/memory/search").json()["total"] == 2


def test_other_owner_history_never_reaches_claude(tmp_path):
    model = Scripted(analysis=[ANALYSIS], draft=[{"reply": "Could you share the password?", "cited_message_ids": []}], draft_review=[APPROVED_DRAFT_REVIEW])
    c = make_client(tmp_path, model)
    c.post("/api/memory/import", json=load_fixture("import_request.json"), headers={OWNER_HEADER: "owner-b"})
    body = c.post("/api/reply/generate", json=load_fixture("generate_request.json")).json()
    assert body["evidence"] == []
    assert any("No supporting history" in w for w in body["warnings"])
    assert "assessment" not in [t for t, _ in model.calls]  # no records -> no assessment call


def test_deleted_history_not_used(tmp_path):
    model = Scripted(analysis=[ANALYSIS], draft=[{"reply": "Could you share the password?", "cited_message_ids": []}], draft_review=[APPROVED_DRAFT_REVIEW])
    c = make_client(tmp_path, model)
    c.post("/api/memory/import", json=load_fixture("import_request.json"))
    assert c.delete("/api/memory").json() == {"deletedCount": 2}
    assert c.post("/api/reply/generate", json=load_fixture("generate_request.json")).json()["evidence"] == []


def test_invented_citation_twice_is_502(tmp_path):
    bad = {"reply": "Per your message, fine.", "cited_message_ids": ["msg_404"]}
    c = make_client(tmp_path, Scripted(analysis=[ANALYSIS], assessment=[ASSESSMENT], assessment_review=[approved_assessment_review(1)], draft=[bad, bad]))
    c.post("/api/memory/import", json=load_fixture("import_request.json"))
    r = c.post("/api/reply/generate", json=load_fixture("generate_request.json"))
    assert_error(r, 502, "MODEL_ERROR")
    assert "msg_404" not in r.text and "password" not in r.text


def test_semantically_rejected_reply_never_reaches_the_client(tmp_path):
    invented = "I completed the audit and sent the password to Alice."
    review = {**APPROVED_DRAFT_REVIEW, "facts_grounded": False}
    model = Scripted(
        analysis=[ANALYSIS],
        draft=[{"reply": invented, "cited_message_ids": []}] * 2,
        draft_review=[review],
    )
    c = make_client(tmp_path, model)
    response = c.post("/api/reply/generate", json=load_fixture("generate_request.json"))
    assert_error(response, 502, "MODEL_ERROR")
    assert invented not in response.text and "Alice" not in response.text
    # An explicit rejection is final: do not keep asking the reviewer until
    # an unchanged, invented statement happens to receive approval.
    assert [task for task, _ in model.calls].count("draft_review") == 1


def test_genuine_quote_cannot_promote_an_unrelated_claim_to_evidence(tmp_path):
    proposed = {
        "assessments": [{
            "claim_index": 0,
            "status": "supported",
            "evidence": [{
                "message_id": "msg_001",
                "quote": "uploaded the documents to the shared drive",
                "statement": "The manager supplied the password.",
            }],
            "note": "",
        }],
    }
    review = {
        "reviews": [{
            "claim_index": 0,
            "status_valid": False,
            "statements": [{"statement_index": 0, "supported": False}],
        }],
    }
    model = Scripted(
        analysis=[ANALYSIS],
        assessment=[proposed],
        assessment_review=[review],
        draft=[{"reply": "The link requires a password. Could you share it?", "cited_message_ids": []}],
        draft_review=[APPROVED_DRAFT_REVIEW],
    )
    c = make_client(tmp_path, model)
    assert c.post("/api/memory/import", json=load_fixture("import_request.json")).status_code == 200
    response = c.post("/api/reply/generate", json=load_fixture("generate_request.json"))
    assert response.status_code == 200, response.text
    assert response.json()["evidence"] == []
    assert response.json()["unverifiedClaims"] == ANALYSIS["claims"]
    assert "The manager supplied the password" not in response.text


@pytest.mark.parametrize(
    "failure,status,code",
    [
        ("timeout", 504, "MODEL_TIMEOUT"),
        ("malformed", 502, "MODEL_ERROR"),
    ],
)
def test_semantic_review_failure_is_not_a_successful_reply(tmp_path, failure, status, code):
    from backend.application.errors import ModelTimeoutError

    outputs = [ModelTimeoutError("draft_review")] if failure == "timeout" else [{}, {}]
    model = Scripted(
        analysis=[ANALYSIS],
        draft=[{"reply": "Could you share the password?", "cited_message_ids": []}],
        draft_review=outputs,
    )
    c = make_client(tmp_path, model)
    response = c.post("/api/reply/generate", json=load_fixture("generate_request.json"))
    assert_error(response, status, code)
    assert "reply" not in response.json()


@pytest.mark.parametrize("tone", ["diplomatic", "neutral", "assertive"])
def test_mock_mode_end_to_end(tmp_path, tone):
    c = make_client(tmp_path, MockJsonModel())
    c.post("/api/memory/import", json=load_fixture("import_request.json"))
    req = {**load_fixture("generate_request.json"), "tone": tone, "employeeDraft": "I can't find the documents on the shared drive."}
    body = c.post("/api/reply/generate", json=req).json()
    assert body["reply"].startswith(MOCK_PREFIX)
    assert {e["messageId"] for e in body["evidence"]} <= {"msg_001", "msg_002"}
    # Mock review cannot establish semantic support, so related messages are
    # not promoted to verified evidence merely because they share keywords.
    assert body["evidence"] == []
    assert body["unverifiedClaims"] == ["I can't find the documents on the shared drive."]
