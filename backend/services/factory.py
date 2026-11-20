"""Builds Developer 3's services for the composition root (backend/api/main.py).

Environment:
  R2R_DB_PATH               SQLite file (default: backend/data/rage_to_reply.sqlite3)
  R2R_AI_MODE               "claude" (default) or "mock" (explicit local mock, no API calls)
  ANTHROPIC_MODEL           required when R2R_AI_MODE=claude (recommended: claude-opus-5-5)
  ANTHROPIC_API_KEY         Claude credentials (or any credential the anthropic SDK resolves)
  R2R_MODEL_TIMEOUT_SECONDS per-request Claude timeout, default 30
  R2R_MODEL_EFFORT          low | medium | high | xhigh | max, default medium
  R2R_REFUSAL_FALLBACK      "default" (server-side refusal fallback, default) or "off"
"""

from __future__ import annotations

import os
from pathlib import Path

from backend.application.ports import Services
from backend.memory.sqlite_store import SqliteMemoryService

from .analysis import ClaudeAnalysisService
from .drafting import ClaudeDraftingService
from .evidence import ClaudeEvidenceService
from .llm import AnthropicJsonModel, JsonModel
from .mock import MockJsonModel

DEFAULT_DB = Path(__file__).resolve().parent.parent / "data" / "rage_to_reply.sqlite3"


def build_model() -> JsonModel:
    mode = os.environ.get("R2R_AI_MODE", "claude")
    if mode == "mock":
        return MockJsonModel()
    if mode != "claude":
        raise RuntimeError("R2R_AI_MODE must be 'claude' or 'mock'.")
    model = os.environ.get("ANTHROPIC_MODEL", "").strip()
    if not model:
        raise RuntimeError("ANTHROPIC_MODEL must be set (or use R2R_AI_MODE=mock for local development).")
    effort = os.environ.get("R2R_MODEL_EFFORT", "medium")
    if effort not in ("low", "medium", "high", "xhigh", "max"):
        raise RuntimeError("R2R_MODEL_EFFORT is invalid.")
    fallback = os.environ.get("R2R_REFUSAL_FALLBACK", "default")
    if fallback not in ("default", "off"):
        raise RuntimeError("R2R_REFUSAL_FALLBACK must be 'default' or 'off'.")
    return AnthropicJsonModel(
        model=model,
        timeout_seconds=float(os.environ.get("R2R_MODEL_TIMEOUT_SECONDS", "30")),
        effort=effort,
        refusal_fallback=fallback == "default",
    )


def build_services() -> Services:
    model = build_model()
    return Services(
        memory=SqliteMemoryService(os.environ.get("R2R_DB_PATH") or DEFAULT_DB),
        analysis=ClaudeAnalysisService(model),
        evidence=ClaudeEvidenceService(model),
        drafting=ClaudeDraftingService(model),
    )
