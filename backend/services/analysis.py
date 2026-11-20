"""Structured analysis of the manager message and employee draft (Developer 3)."""

from __future__ import annotations

import re
from typing import Any

from backend.application.errors import ModelError
from backend.application.ports import MessageAnalysis, OwnerContext

from .llm import JsonModel, call_with_retry

MAX_ITEMS = 8
MAX_CLAIMS = 10
MAX_ITEM_CHARS = 600

SYSTEM = """You analyse workplace messages for Rage-to-Reply, which helps an employee turn an
emotional draft into a professional reply. You do not write the reply.

From the manager's message, extract:
- explicit_requests: what the manager literally asks for. Quote or closely paraphrase; no inference.
- possible_actions: actions the employee could take in response. These are interpretations.
- missing_information: information needed to respond that neither message provides.
- potential_misunderstandings: places where the two messages may be talking past each other.

From the employee's draft, extract:
- employee_concern: one neutral sentence describing the employee's concern, written as
  "The employee reports ..." or similar. Remove insults, profanity and emotion.
- claims: concrete, checkable factual claims the employee makes about events, documents,
  access, dates, requests or actions. One short neutral sentence each. Exclude opinions,
  feelings and insults. Claims are user-reported, not verified facts.
- search_queries: 1-6 short keyword phrases for finding related past messages.

Rules:
- Never state or guess the manager's emotions, tone, motives or hidden intentions
  (e.g. do not say the manager is angry, frustrated, disappointed or testing the employee).
- Do not invent facts, names, dates or history.
- Use the language of the manager's message.
- Use empty arrays when nothing applies."""

_STR_ARRAY = {"type": "array", "items": {"type": "string"}}
SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "explicit_requests": _STR_ARRAY,
        "possible_actions": _STR_ARRAY,
        "missing_information": _STR_ARRAY,
        "potential_misunderstandings": _STR_ARRAY,
        "employee_concern": {"type": "string"},
        "claims": _STR_ARRAY,
        "search_queries": _STR_ARRAY,
    },
    "required": [
        "explicit_requests",
        "possible_actions",
        "missing_information",
        "potential_misunderstandings",
        "employee_concern",
        "claims",
        "search_queries",
    ],
    "additionalProperties": False,
}

# Statements attributing feelings or motives to the manager are unusable output.
_EMOTION_CLAIM = re.compile(
    r"\b(manager|they|he|she)\b[^.]{0,40}\b(is|are|seems?|sounds?|feels?|felt|was|were|appears?)\b[^.]{0,20}\b"
    r"(angry|furious|frustrated|upset|annoyed|irritated|disappointed|impatient|hostile|passive[- ]aggressive|"
    r"stressed|anxious|testing|trying to)\b",
    re.IGNORECASE,
)


def _strings(data: dict[str, Any], key: str, limit: int) -> list[str]:
    value = data.get(key)
    if not isinstance(value, list) or not all(isinstance(v, str) for v in value):
        raise ModelError(f"analysis: {key} must be a list of strings")
    out: list[str] = []
    for v in value:
        v = " ".join(v.split())
        if v and v not in out:
            out.append(v[:MAX_ITEM_CHARS])
    return out[:limit]


def _end(text: str) -> str:
    return text if text.endswith((".", "?", "!")) else text + "."


def parse_analysis(data: dict[str, Any]) -> MessageAnalysis:
    requests = _strings(data, "explicit_requests", MAX_ITEMS)
    actions = _strings(data, "possible_actions", MAX_ITEMS)
    missing = _strings(data, "missing_information", MAX_ITEMS)
    misunderstandings = _strings(data, "potential_misunderstandings", MAX_ITEMS)
    claims = _strings(data, "claims", MAX_CLAIMS)
    queries = _strings(data, "search_queries", MAX_ITEMS)
    concern = data.get("employee_concern")
    if not isinstance(concern, str) or not concern.strip():
        raise ModelError("analysis: employee_concern missing")
    concern = " ".join(concern.split())[:MAX_ITEM_CHARS]

    for text in [*requests, *actions, *misunderstandings]:
        if _EMOTION_CLAIM.search(text):
            raise ModelError("analysis: attributes emotions or motives to the manager")

    if requests:
        intent = " ".join(f"Explicit request: {_end(r)}" for r in requests)
    else:
        intent = "No explicit request was identified in the manager's message."
    if actions:
        intent += " " + " ".join(f"Possible action (interpretation): {_end(a)}" for a in actions)

    warnings = tuple(f"Missing information: {_end(m)}" for m in missing) + tuple(
        f"Possible misunderstanding (interpretation): {_end(m)}" for m in misunderstandings
    )
    return MessageAnalysis(
        manager_intent=intent,
        employee_concern=concern,
        claims=tuple(claims),
        search_queries=tuple(queries) or tuple(claims),
        warnings=warnings,
    )


class ClaudeAnalysisService:
    def __init__(self, model: JsonModel) -> None:
        self._model = model

    def analyse(self, owner: OwnerContext, *, manager_message: str, employee_draft: str) -> MessageAnalysis:
        return call_with_retry(
            self._model,
            task="analysis",
            system=SYSTEM,
            payload={"manager_message": manager_message, "employee_draft": employee_draft},
            schema=SCHEMA,
            max_tokens=16000,
            parse=parse_analysis,
        )
