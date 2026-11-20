"""Explicit local mock for Claude (R2R_AI_MODE=mock).

Returns deterministic, clearly labelled JSON in the same shapes Claude must
produce, so the real SQLite store, the real evidence validator and the
orchestrator can be exercised without an API key. It is never used as a
fallback when real Claude calls fail.

The mock cannot judge support, so it marks every claim "unverified" and only
offers keyword-related records as context.
"""

from __future__ import annotations

import re
from typing import Any

MOCK_PREFIX = "[Mock reply - Claude not called]"
_WORD = re.compile(r"[^\W_]{3,}", re.UNICODE)
_STOP = {"the", "and", "you", "for", "that", "this", "have", "still", "please", "why", "yet", "because", "can", "with", "not"}

_REPLIES = {
    "diplomatic": "Hi, thanks for following up. I'd like to share where things stand and what I need to move forward. Could we confirm the next steps together?",
    "neutral": "Hi, here is where things stand. Please let me know what you need from me next.",
    "assertive": "Hi, to move forward I need the outstanding item resolved. Please confirm the next steps.",
}


def _sentences(text: str) -> list[str]:
    return [s.strip() for s in re.split(r"(?<=[.!?])\s+", text) if len(s.strip()) > 3]


def _keywords(text: str) -> set[str]:
    return {w.casefold() for w in _WORD.findall(text)} - _STOP


class MockJsonModel:
    def generate_json(self, *, task: str, system: str, payload: dict[str, Any], schema: dict[str, Any], max_tokens: int) -> dict[str, Any]:
        return getattr(self, f"_{task}")(payload)

    def _analysis(self, p: dict[str, Any]) -> dict[str, Any]:
        manager = _sentences(p["manager_message"])
        claims = _sentences(p["employee_draft"])[:5]
        return {
            "explicit_requests": [f"[mock] {s}" for s in manager if s.endswith("?") or "please" in s.casefold()][:3],
            "possible_actions": [],
            "missing_information": ["[mock] Analysis was not performed by Claude"],
            "potential_misunderstandings": [],
            "employee_concern": "[mock] The employee's concern was not analysed by Claude.",
            "claims": claims,
            "search_queries": claims + manager,
        }

    def _assessment(self, p: dict[str, Any]) -> dict[str, Any]:
        out = []
        for c in p["claims"]:
            evidence = [
                {
                    "message_id": r["message_id"],
                    "quote": r["content"][:200],
                    "statement": f"[mock] Possibly related message from {r['sender']}; support not assessed by Claude.",
                }
                for r in p["records"]
                if len(_keywords(c["claim"]) & _keywords(r["content"])) >= 2 and len(r["content"].strip()) >= 8
            ][:2]
            out.append({"claim_index": c["claim_index"], "status": "unverified", "evidence": evidence, "note": ""})
        return {"assessments": out}

    def _draft(self, p: dict[str, Any]) -> dict[str, Any]:
        return {
            "reply": f"{MOCK_PREFIX} {_REPLIES[p['tone']]}",
            "cited_message_ids": [e["message_id"] for e in p["allowed_evidence"]],
        }
