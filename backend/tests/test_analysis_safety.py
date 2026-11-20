"""Keep manager emotion and motive attributions out of analysis output."""

from __future__ import annotations

from typing import Any

import pytest

from backend.application.errors import ModelError
from backend.application.ports import OwnerContext
from backend.services.analysis import ClaudeAnalysisService, parse_analysis


def analysis_output() -> dict[str, Any]:
    return {
        "explicit_requests": ["Explain why the document link cannot be opened"],
        "possible_actions": ["Ask for the password"],
        "missing_information": ["Whether a password was sent"],
        "potential_misunderstandings": ["The shared location may still require a password"],
        "employee_concern": "The employee reports being unable to open the document link.",
        "claims": ["The document link requires a password."],
        "search_queries": ["document link password"],
    }


@pytest.mark.parametrize(
    "field",
    [
        "explicit_requests",
        "possible_actions",
        "missing_information",
        "potential_misunderstandings",
        "employee_concern",
        "claims",
        "search_queries",
    ],
)
@pytest.mark.parametrize(
    "attribution",
    [
        "The manager is angry about the access issue.",
        "The manager is trying to embarrass the employee.",
    ],
)
def test_all_analysis_fields_reject_manager_attributions(field, attribution):
    output = analysis_output()
    output[field] = attribution if field == "employee_concern" else [attribution]

    with pytest.raises(ModelError, match="attributes emotions or motives"):
        parse_analysis(output)


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("employee_concern", "The employee reports that the manager is angry."),
        ("missing_information", ["Why the manager is furious."]),
    ],
)
def test_unsafe_concern_or_missing_information_retries_once(field, value):
    bad = analysis_output()
    bad[field] = value
    good = analysis_output()

    class ScriptedModel:
        def __init__(self):
            self.payloads = []

        def generate_json(self, **kwargs):
            self.payloads.append(kwargs["payload"])
            return bad if len(self.payloads) == 1 else good

    model = ScriptedModel()
    result = ClaudeAnalysisService(model).analyse(
        OwnerContext("test-owner", "authenticated"),
        manager_message="Why can't you open the documents?",
        employee_draft="The link requires a password.",
    )

    assert len(model.payloads) == 2
    assert "previous_attempt_problem" in model.payloads[1]
    assert result.employee_concern == good["employee_concern"]
    assert result.warnings[0] == "Missing information: Whether a password was sent."


def test_neutral_concern_and_access_questions_are_preserved():
    output = analysis_output()
    result = parse_analysis(output)

    assert result.employee_concern == output["employee_concern"]
    assert result.claims == tuple(output["claims"])
    assert result.search_queries == tuple(output["search_queries"])
    assert result.warnings[0] == "Missing information: Whether a password was sent."

