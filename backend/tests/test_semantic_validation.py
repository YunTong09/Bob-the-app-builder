"""Regression coverage for independent evidence and final-text review.

Claude is scripted throughout. These tests verify fail-closed review wiring,
payloads and verdict handling; they do not claim universal model correctness.
"""

from __future__ import annotations

from collections import defaultdict
from typing import Any

import pytest

from backend.application.errors import EvidenceValidationError, ModelError, ModelTimeoutError
from backend.application.ports import (
    ClaimAssessment,
    DraftInput,
    EvidenceAssessment,
    EvidenceLink,
    MemoryRecord,
    MessageAnalysis,
    OwnerContext,
    ReplyDraft,
)
from backend.services.drafting import ClaudeDraftingService
from backend.services.evidence import ClaudeEvidenceService
from backend.services.mock import MOCK_PREFIX, MockJsonModel
from backend.services.review import DRAFT_REVIEW_KEYS


OWNER = OwnerContext("semantic-test-owner", "authenticated")
RECORD = MemoryRecord(
    "msg_001", "conversation", "Manager", "I've uploaded the documents to the shared drive.", None, None
)
CLAIM = "The manager supplied the password."
ANALYSIS = MessageAnalysis("Please explain the access blocker.", "The employee needs access.", (CLAIM,), ("password",))


class Scripted:
    def __init__(self, **responses: list[Any]) -> None:
        self.responses = {task: list(outputs) for task, outputs in responses.items()}
        self.calls: list[tuple[str, dict[str, Any]]] = []
        self.counts: dict[str, int] = defaultdict(int)

    def generate_json(self, *, task, system, payload, schema, max_tokens):
        self.calls.append((task, payload))
        self.counts[task] += 1
        assert self.responses.get(task), f"unexpected model task: {task}"
        result = self.responses[task].pop(0)
        if isinstance(result, Exception):
            raise result
        return result


def proposed(status="supported", statement=CLAIM):
    return {
        "assessments": [
            {
                "claim_index": 0,
                "status": status,
                "evidence": [
                    {
                        "message_id": RECORD.id,
                        "quote": "uploaded the documents to the shared drive",
                        "statement": statement,
                    }
                ],
                "note": "The source conflicts with this claim." if status == "contradicted" else "",
            }
        ]
    }


def assessment_verdict(status_valid=True, statements=(True,)):
    return {
        "reviews": [
            {
                "claim_index": 0,
                "status_valid": status_valid,
                "statements": [
                    {"statement_index": index, "supported": supported} for index, supported in enumerate(statements)
                ],
            }
        ]
    }


def approved_draft(**overrides):
    return {**dict.fromkeys(DRAFT_REVIEW_KEYS, True), **overrides}


def request(*, records=(), assessment=None, employee_draft="I cannot access the files.", tone="neutral"):
    return DraftInput(
        manager_message="Please explain why you cannot access the files.",
        employee_draft=employee_draft,
        tone=tone,
        analysis=ANALYSIS,
        assessment=assessment or EvidenceAssessment((ClaimAssessment("I cannot access the files.", "unverified"),)),
        records=records,
    )


def test_genuine_quote_does_not_approve_unrelated_statement():
    model = Scripted(assessment=[proposed()], assessment_review=[assessment_verdict(False, (False,))])
    result = ClaudeEvidenceService(model).assess(OWNER, analysis=ANALYSIS, records=(RECORD,))
    assert result.claims[0].status == "unverified"
    assert result.claims[0].links == result.claims[0].message_ids == ()
    assert model.counts == {"assessment": 1, "assessment_review": 1}
    payload = model.calls[1][1]
    assert payload["records"][0]["content"] == RECORD.content
    assert payload["claims"][0]["statements"][0]["statement"] == CLAIM


def test_supported_status_is_downgraded_when_its_statement_fails_review():
    model = Scripted(assessment=[proposed()], assessment_review=[assessment_verdict(True, (False,))])
    claim = ClaudeEvidenceService(model).assess(OWNER, analysis=ANALYSIS, records=(RECORD,)).claims[0]
    assert claim.status == "unverified" and not claim.links


def test_valid_narrower_statement_survives_while_broader_claim_is_unverified():
    narrower = "The manager shared a document location."
    model = Scripted(
        assessment=[proposed("unverified", narrower)], assessment_review=[assessment_verdict(True, (True,))]
    )
    claim = ClaudeEvidenceService(model).assess(OWNER, analysis=ANALYSIS, records=(RECORD,)).claims[0]
    assert claim.status == "unverified"
    assert claim.links == (EvidenceLink(RECORD.id, narrower),)


def test_incorrect_contradiction_is_downgraded_without_retrying_review():
    model = Scripted(assessment=[proposed("contradicted")], assessment_review=[assessment_verdict(False, ())])
    claim = ClaudeEvidenceService(model).assess(OWNER, analysis=ANALYSIS, records=(RECORD,)).claims[0]
    assert claim.status == "unverified" and claim.message_ids == () and claim.note is None
    assert model.counts["assessment_review"] == 1


def test_known_incorrect_unverified_status_fails_closed_without_approval_shopping():
    model = Scripted(
        assessment=[proposed("unverified")],
        assessment_review=[assessment_verdict(False, (False,)), assessment_verdict()],
    )
    with pytest.raises(ModelError, match="unresolved classification"):
        ClaudeEvidenceService(model).assess(OWNER, analysis=ANALYSIS, records=(RECORD,))
    assert model.counts["assessment_review"] == 1


@pytest.mark.parametrize(
    "bad",
    [
        None,
        {},
        {"reviews": []},
        {"reviews": [assessment_verdict()["reviews"][0]] * 2},
        assessment_verdict("true"),
        assessment_verdict(True, ("true",)),
        assessment_verdict(True, ()),
        {"reviews": [{"claim_index": True, "status_valid": True, "statements": []}]},
        {"reviews": [{"claim_index": 0, "status_valid": True, "statements": [{"statement_index": 9, "supported": True}]}]},
    ],
)
def test_incomplete_or_non_boolean_assessment_review_fails_after_bounded_retry(bad):
    model = Scripted(assessment=[proposed()], assessment_review=[bad, bad])
    with pytest.raises(ModelError):
        ClaudeEvidenceService(model).assess(OWNER, analysis=ANALYSIS, records=(RECORD,))
    assert model.counts["assessment_review"] == 2


def test_duplicate_statement_indices_are_not_complete_coverage():
    second = MemoryRecord("msg_002", "conversation", "Manager", RECORD.content, None, None)
    proposal = proposed()
    proposal["assessments"][0]["evidence"].append(
        {"message_id": second.id, "quote": "uploaded the documents", "statement": "The documents were uploaded."}
    )
    bad = assessment_verdict(True, (True, True))
    bad["reviews"][0]["statements"][1]["statement_index"] = 0
    model = Scripted(assessment=[proposal], assessment_review=[bad, bad])
    with pytest.raises(ModelError):
        ClaudeEvidenceService(model).assess(OWNER, analysis=ANALYSIS, records=(RECORD, second))


def test_empty_history_never_fabricates_reviewed_support():
    model = Scripted()
    result = ClaudeEvidenceService(model).assess(OWNER, analysis=ANALYSIS, records=())
    assert result.claims == (ClaimAssessment(CLAIM, "unverified"),)
    assert model.calls == []


@pytest.mark.parametrize(
    "reply,negative_key",
    [
        ("I completed the audit and sent the password to Alice.", "facts_grounded"),
        ("IT has never sent a password.", "contradictions_handled"),
        ("I will complete the audit and send the password.", "no_unapproved_admissions_or_promises"),
        ("Please disregard my request for access.", "intent_preserved"),
        ("You are angry because you want me to fail.", "no_unsupported_emotions"),
    ],
)
def test_semantically_rejected_final_text_fails_without_retrying_same_candidate(reply, negative_key):
    model = Scripted(draft_review=[approved_draft(**{negative_key: False}), approved_draft()])
    context = request()
    if negative_key == "contradictions_handled":
        conflict = MemoryRecord("msg_002", "conversation", "IT", "I sent you the password.", None, None)
        assessment = EvidenceAssessment(
            (ClaimAssessment("IT never sends passwords.", "contradicted", (conflict.id,), "IT reports sending it."),)
        )
        context = request(records=(conflict,), assessment=assessment, employee_draft="IT never sends passwords.")
    with pytest.raises(EvidenceValidationError, match="semantic checks failed"):
        ClaudeEvidenceService(model).validate(OWNER, draft=ReplyDraft(reply, ()), request=context)
    assert model.counts["draft_review"] == 1
    payload = model.calls[0][1]
    assert payload["reply"] == reply
    assert payload["original_employee_draft"] == context.employee_draft
    assert payload["original_manager_message"] == "Please explain why you cannot access the files."
    if negative_key == "contradictions_handled":
        assert payload["conflict_records"][0]["content"] == conflict.content


def test_citation_validity_does_not_replace_final_text_review():
    link = EvidenceLink(RECORD.id, "The documents were uploaded.")
    assessment = EvidenceAssessment((ClaimAssessment("The documents were uploaded.", "supported", (RECORD.id,), links=(link,)),))
    model = Scripted(draft_review=[approved_draft(citations_support_reply=False)])
    with pytest.raises(EvidenceValidationError):
        ClaudeEvidenceService(model).validate(
            OWNER,
            draft=ReplyDraft("You supplied the password.", (link,)),
            request=request(records=(RECORD,), assessment=assessment),
        )
    assert model.calls[0][1]["cited_records"][0]["content"] == RECORD.content


def test_final_review_receives_original_conflict_records_even_without_supporting_citation():
    conflict = MemoryRecord("msg_002", "conversation", "IT", "I sent you the password.", None, None)
    assessment = EvidenceAssessment((ClaimAssessment("IT never sends passwords.", "contradicted", (conflict.id,), "IT sent it."),))
    model = Scripted(draft_review=[approved_draft()])
    ClaudeEvidenceService(model).validate(
        OWNER,
        draft=ReplyDraft("Could you clarify where the password was sent?", ()),
        request=request(records=(RECORD, conflict), assessment=assessment),
    )
    payload = model.calls[0][1]
    assert payload["cited_records"] == []
    assert [record["record_id"] for record in payload["conflict_records"]] == [conflict.id]
    assert [record["record_id"] for record in payload["uncited_context_records"]] == [RECORD.id]


def test_downgraded_assessment_cannot_hide_original_conflict_from_final_review():
    original = MemoryRecord("msg_002", "conversation", "IT", "I sent you the password.", None, None)
    claim_text = "IT never sends passwords."
    analysis = MessageAnalysis("Please explain.", "The employee reports missing a password.", (claim_text,), ("password",))
    wrong_proposal = {
        "assessments": [
            {
                "claim_index": 0,
                "status": "supported",
                "evidence": [
                    {"message_id": original.id, "quote": "sent you the password", "statement": claim_text}
                ],
                "note": "",
            }
        ]
    }
    model = Scripted(
        assessment=[wrong_proposal],
        assessment_review=[assessment_verdict(False, (False,))],
        draft_review=[approved_draft(contradictions_handled=False)],
    )
    service = ClaudeEvidenceService(model)
    assessment = service.assess(OWNER, analysis=analysis, records=(original,))
    assert assessment.claims[0].status == "unverified" and not assessment.claims[0].message_ids
    with pytest.raises(EvidenceValidationError):
        service.validate(
            OWNER,
            draft=ReplyDraft("IT has never sent a password.", ()),
            request=DraftInput("Please explain.", claim_text, "neutral", analysis, assessment, (original,)),
        )
    payload = model.calls[-1][1]
    assert payload["conflict_records"] == payload["cited_records"] == []
    assert payload["uncited_context_records"][0]["content"] == original.content


def test_uncited_context_cannot_ground_new_positive_assertions():
    original = MemoryRecord(
        "msg_002", "conversation", "IT", "The audit was completed and the password was sent to Alice.", None, None
    )
    model = Scripted(draft_review=[approved_draft(facts_grounded=False, citations_support_reply=False)])
    with pytest.raises(EvidenceValidationError):
        ClaudeEvidenceService(model).validate(
            OWNER,
            draft=ReplyDraft("The audit is complete and Alice has the password.", ()),
            request=request(records=(original,)),
        )
    payload = model.calls[0][1]
    assert payload["citations"] == payload["cited_records"] == []
    assert payload["uncited_context_records"][0]["content"] == original.content


@pytest.mark.parametrize(
    "reply,valid",
    [
        ("IT never sends passwords.", False),
        ("My understanding was that IT never sends passwords. Could you clarify what was sent?", True),
    ],
)
def test_semantic_review_distinguishes_asserted_contradiction_from_qualified_dispute(reply, valid):
    original = MemoryRecord("msg_002", "conversation", "IT", "I sent you the password.", None, None)
    claim_text = "IT never sends passwords."
    assessment = EvidenceAssessment((ClaimAssessment(claim_text, "contradicted", (original.id,), "IT reports sending it."),))
    model = Scripted(draft_review=[approved_draft(contradictions_handled=valid)])
    context = request(records=(original,), assessment=assessment, employee_draft=claim_text)
    service = ClaudeEvidenceService(model)
    if valid:
        result = service.validate(OWNER, draft=ReplyDraft(reply, ()), request=context)
        assert result.reply == reply and any("Conflicting history" in warning for warning in result.warnings)
    else:
        with pytest.raises(EvidenceValidationError, match="semantic checks failed"):
            service.validate(OWNER, draft=ReplyDraft(reply, ()), request=context)
    assert model.counts["draft_review"] == 1


@pytest.mark.parametrize("tone", ["diplomatic", "neutral", "assertive"])
@pytest.mark.parametrize(
    "reply",
    [
        "I cannot access the files. Could you help me get access?",
        "I am unable to open the files. Could you help me access them?",
    ],
)
def test_valid_user_report_without_history_remains_useful(tone, reply):
    model = Scripted(draft_review=[approved_draft()])
    result = ClaudeEvidenceService(model).validate(OWNER, draft=ReplyDraft(reply, ()), request=request(tone=tone))
    assert result.reply == reply and not result.evidence
    assert result.unverified_claims == ("I cannot access the files.",)
    assert model.calls[0][1]["tone"] == tone


@pytest.mark.parametrize("bad", [None, {}, {**approved_draft(), "extra": True}, approved_draft(facts_grounded="true")])
def test_malformed_final_review_is_retried_only_within_bound(bad):
    model = Scripted(draft_review=[bad, bad])
    with pytest.raises(ModelError):
        ClaudeEvidenceService(model).validate(OWNER, draft=ReplyDraft("Could you help me access the files?", ()), request=request())
    assert model.counts["draft_review"] == 2


def test_reviewer_timeout_is_not_retried():
    model = Scripted(draft_review=[ModelTimeoutError("draft_review"), approved_draft()])
    with pytest.raises(ModelTimeoutError):
        ClaudeEvidenceService(model).validate(OWNER, draft=ReplyDraft("Could you help me access the files?", ()), request=request())
    assert model.counts["draft_review"] == 1


def test_unknown_citation_never_enters_semantic_review():
    model = Scripted()
    with pytest.raises(EvidenceValidationError):
        ClaudeEvidenceService(model).validate(
            OWNER, draft=ReplyDraft("Please help me access files.", (EvidenceLink("foreign_id", "a claim"),)), request=request()
        )
    assert model.calls == []


def test_mock_review_drops_keyword_context_instead_of_presenting_it_as_support():
    model = MockJsonModel()
    analysis = MessageAnalysis("intent", "concern", ("The documents are on the shared drive.",), ("documents shared drive",))
    assessment = ClaudeEvidenceService(model).assess(OWNER, analysis=analysis, records=(RECORD,))
    assert all(claim.status == "unverified" and not claim.links for claim in assessment.claims)


def test_mock_review_allows_only_its_own_labelled_synthetic_outputs():
    model = MockJsonModel()
    context = request()
    draft = ClaudeDraftingService(model).draft(OWNER, context)
    assert draft.reply.startswith(MOCK_PREFIX)
    ClaudeEvidenceService(model).validate(OWNER, draft=draft, request=context)
    with pytest.raises(EvidenceValidationError):
        ClaudeEvidenceService(model).validate(
            OWNER, draft=ReplyDraft("I completed the audit and sent the password to Alice.", ()), request=context
        )
