"""Generation pipeline: Validate -> Analyse -> Retrieve -> Assess -> Draft -> Validate -> Respond."""

from __future__ import annotations

import pytest

from backend.application.errors import (
    EvidenceValidationError,
    ModelError,
    ModelTimeoutError,
    OwnershipError,
    StorageUnavailableError,
)
from backend.application.orchestrator import WARNING_NO_HISTORY, WARNING_RETRIEVAL_FAILED
from backend.application.ports import (
    ClaimAssessment,
    EvidenceAssessment,
    EvidenceLink,
    ReplyDraft,
    ValidatedReply,
)

from .conftest import GEN_BODY, OWNER_HEADER, import_fixture, load_fixture
from .test_boundary import assert_error

RESPONSE_KEYS = {"reply", "managerIntent", "employeeConcern", "evidence", "unverifiedClaims", "warnings"}


def test_contract_example_full_flow(client, ai):
    """Reproduces the synthetic response in API_CONTRACT.md end to end."""
    import_fixture(client)
    expected = load_fixture("generate_response.json")
    ai.draft_result = ReplyDraft(
        reply=expected["reply"],
        evidence=(EvidenceLink("msg_001", "The manager shared a document location."),),
    )
    ai.validated = lambda draft, records: ValidatedReply(
        reply=draft.reply,
        evidence=draft.evidence,
        unverified_claims=tuple(expected["unverifiedClaims"]),
        warnings=tuple(expected["warnings"]),
    )
    r = client.post("/api/reply/generate", json=load_fixture("generate_request.json"))
    assert r.status_code == 200, r.text
    assert r.json() == expected
    assert ai.names() == ["analyse", "assess", "draft", "validate"]


def test_evidence_content_comes_from_store_not_model(client, ai):
    import_fixture(client)
    ai.draft_result = ReplyDraft(reply="ok reply", evidence=(EvidenceLink("msg_002", "Employee planned to review docs."),))
    body = client.post("/api/reply/generate", json={**GEN_BODY, "conversationId": "conv_demo"}).json()
    ev = body["evidence"][0]
    assert ev == {
        "messageId": "msg_002",
        "content": "Thanks, I'll take a look at the shared drive documents this afternoon.",
        "sender": "Employee",
        "timestamp": None,  # missing metadata stays null
        "supportedClaim": "Employee planned to review docs.",
        "source": None,
    }


def test_same_owner_context_passed_to_every_service(client, ai):
    import_fixture(client)
    client.post("/api/reply/generate", json=GEN_BODY)
    owners = {c[1] if c[0] == "analyse" else c[1][0] for c in ai.calls}
    assert len(owners) == 1 and next(iter(owners)).owner_id == "owner-a"


def test_validator_receives_the_original_drafting_context(client, ai):
    import_fixture(client)
    request_body = {**GEN_BODY, "tone": "assertive", "conversationId": "conv_demo"}
    assert client.post("/api/reply/generate", json=request_body).status_code == 200
    drafting_context = next(call[1][1] for call in ai.calls if call[0] == "draft")
    validation_context = next(call[1][2] for call in ai.calls if call[0] == "validate")
    assert validation_context is drafting_context
    assert validation_context.manager_message == request_body["managerMessage"]
    assert validation_context.employee_draft == request_body["employeeDraft"]
    assert validation_context.tone == "assertive"
    assert {record.conversation_id for record in validation_context.records} == {"conv_demo"}


def test_empty_history_returns_useful_reply_with_warning(client, ai):
    r = client.post("/api/reply/generate", json=GEN_BODY)
    assert r.status_code == 200
    body = r.json()
    assert set(body) == RESPONSE_KEYS
    assert body["evidence"] == [] and body["reply"]
    assert WARNING_NO_HISTORY in body["warnings"]
    assert WARNING_RETRIEVAL_FAILED not in body["warnings"]


def test_unknown_conversation_behaves_as_empty(client, ai):
    import_fixture(client)
    r = client.post("/api/reply/generate", json={**GEN_BODY, "conversationId": "conv_other"})
    assert r.status_code == 200
    assert r.json()["evidence"] == [] and WARNING_NO_HISTORY in r.json()["warnings"]
    assess_records = next(c[1][1] for c in ai.calls if c[0] == "assess")
    assert assess_records == ()


def test_retrieval_failure_is_warned_fallback(client, ai, memory, monkeypatch):
    def boom(*a, **k):
        raise StorageUnavailableError("db down")

    monkeypatch.setattr(memory, "retrieve", boom)
    r = client.post("/api/reply/generate", json=GEN_BODY)
    assert r.status_code == 200
    body = r.json()
    assert body["evidence"] == []
    assert WARNING_RETRIEVAL_FAILED in body["warnings"]
    assert WARNING_NO_HISTORY not in body["warnings"]  # outage is not "empty history"


def test_ownership_failure_never_falls_back(client, ai, memory, monkeypatch):
    def boom(*a, **k):
        raise OwnershipError("could not scope query")

    monkeypatch.setattr(memory, "retrieve", boom)
    r = client.post("/api/reply/generate", json=GEN_BODY)
    assert_error(r, 500, "INTERNAL_ERROR")
    assert "draft" not in ai.names()


def test_out_of_scope_records_from_storage_are_rejected(client, ai, memory, monkeypatch):
    import_fixture(client)
    real = memory.retrieve
    monkeypatch.setattr(memory, "retrieve", lambda owner, **k: real(owner, queries=k["queries"], conversation_id=None, limit=k["limit"]))
    r = client.post("/api/reply/generate", json={**GEN_BODY, "conversationId": "conv_other"})
    assert_error(r, 500, "INTERNAL_ERROR")


def test_unauthenticated_request_is_rejected_before_services(client, ai):
    r = client.post("/api/reply/generate", json=GEN_BODY, headers={OWNER_HEADER: ""})
    assert_error(r, 401, "UNAUTHENTICATED")
    assert ai.calls == []


def test_contradictory_evidence(client, ai):
    import_fixture(client)
    ai.assessment = EvidenceAssessment(
        claims=(ClaimAssessment("The documents were never shared.", "contradicted", ("msg_001",), "msg_001 says they were uploaded."),)
    )
    ai.validated = ValidatedReply(
        reply="Hi, I wasn't able to locate the documents. Could you confirm where they are?",
        evidence=(),
        unverified_claims=(),
        warnings=("A stored message says the documents were uploaded to the shared drive, which conflicts with the draft.",),
    )
    body = client.post("/api/reply/generate", json=GEN_BODY).json()
    assert body["evidence"] == []
    assert any("conflicts" in w for w in body["warnings"])
    assert "The documents were never shared." not in [e["supportedClaim"] for e in body["evidence"]]


def test_unsupported_claims_are_listed(client, ai):
    ai.validated = ValidatedReply(reply="reply", evidence=(), unverified_claims=("The link asks for a password.", "The link asks for a password."))
    body = client.post("/api/reply/generate", json=GEN_BODY).json()
    assert body["unverifiedClaims"] == ["The link asks for a password."]


def test_invented_reference_rejected_by_validator_is_502(client, ai):
    import_fixture(client)
    ai.draft_result = ReplyDraft(reply="As you said on Monday...", evidence=(EvidenceLink("msg_999", "Invented."),))
    ai.validated = EvidenceValidationError("unknown id")
    r = client.post("/api/reply/generate", json=GEN_BODY)
    assert_error(r, 502, "MODEL_ERROR")
    assert "msg_999" not in r.text


def test_invented_reference_passed_by_validator_still_never_returned(client, ai):
    """Boundary invariant: even a faulty validator cannot leak a non-retrieved ID."""
    import_fixture(client)
    ai.validated = ValidatedReply(reply="r", evidence=(EvidenceLink("msg_999", "Invented."),), unverified_claims=())
    assert_error(client.post("/api/reply/generate", json=GEN_BODY), 502, "MODEL_ERROR")


def test_other_owners_record_cannot_be_cited(client, ai):
    import_fixture(client, owner="owner-b")
    ai.validated = ValidatedReply(reply="r", evidence=(EvidenceLink("msg_001", "x"),), unverified_claims=())
    r = client.post("/api/reply/generate", json=GEN_BODY)  # owner-a has no history
    assert_error(r, 502, "MODEL_ERROR")
    assert "Synthetic demo" not in r.text


@pytest.mark.parametrize(
    "stage, exc, status, code",
    [
        ("analysis", ModelTimeoutError("t"), 504, "MODEL_TIMEOUT"),
        ("draft_result", ModelTimeoutError("t"), 504, "MODEL_TIMEOUT"),
        ("analysis", ModelError("bad json"), 502, "MODEL_ERROR"),
        ("draft_result", ModelError("malformed"), 502, "MODEL_ERROR"),
        ("assessment", ModelError("malformed"), 502, "MODEL_ERROR"),
    ],
)
def test_model_failures_never_fabricate_success(client, ai, stage, exc, status, code):
    setattr(ai, stage, exc)
    r = client.post("/api/reply/generate", json=GEN_BODY)
    err = assert_error(r, status, code)
    assert "SECRET-DRAFT-TEXT" not in r.text
    assert "reply" not in r.json()
    assert err.get("details") is None


@pytest.mark.parametrize("reply", ["", "   "])
def test_empty_model_reply_is_unusable(client, ai, reply):
    ai.validated = ValidatedReply(reply=reply, evidence=(), unverified_claims=())
    assert_error(client.post("/api/reply/generate", json=GEN_BODY), 502, "MODEL_ERROR")


def test_blank_supported_claim_is_unusable(client, ai):
    import_fixture(client)
    ai.validated = ValidatedReply(reply="r", evidence=(EvidenceLink("msg_001", " "),), unverified_claims=())
    assert_error(client.post("/api/reply/generate", json=GEN_BODY), 502, "MODEL_ERROR")


def test_generation_does_not_persist_inputs(client, ai):
    client.post("/api/reply/generate", json={**GEN_BODY, "conversationId": "conv_demo"})
    body = client.get("/api/memory/search").json()
    assert body["total"] == 0 and body["messages"] == []


def test_regeneration_with_another_tone_uses_same_endpoint(client, ai):
    for tone in ("diplomatic", "neutral", "assertive"):
        assert client.post("/api/reply/generate", json={**GEN_BODY, "tone": tone}).status_code == 200
    tones = [c[1][1].tone for c in ai.calls if c[0] == "draft"]
    assert tones == ["diplomatic", "neutral", "assertive"]
