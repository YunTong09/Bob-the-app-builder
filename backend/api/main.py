"""Composition root: ``uvicorn backend.api.main:app --host 127.0.0.1``.

Service selection (R2R_SERVICES):
* ``real`` (default) -- Developer 3's services via
  ``backend.services.factory.build_services() -> Services``. Startup fails with
  a clear message until that factory exists; it never silently uses stubs.
* ``stub`` -- development-only test doubles in ``backend/devstubs`` (in-memory,
  canned AI output, NOT Claude, NOT production evidence validation). For
  frontend integration only.
"""

from __future__ import annotations

import os

from fastapi import FastAPI

from backend.application.ports import Services
from backend.services.slack import build_slack_service

from .app import create_app
from .identity import resolver_from_env


def _build_services() -> Services:
    mode = os.environ.get("R2R_SERVICES", "real")
    if mode == "stub":
        from backend.devstubs import build_stub_services

        return build_stub_services()
    if mode != "real":
        raise RuntimeError("R2R_SERVICES must be 'real' or 'stub'.")
    try:
        from backend.services.factory import build_services  # Developer 3
    except ImportError as exc:
        raise RuntimeError(
            "Developer 3 services are not available yet (expected "
            "backend.services.factory.build_services). Set R2R_SERVICES=stub "
            "to run with development stubs."
        ) from exc
    return build_services()


def build_app() -> FastAPI:
    return create_app(_build_services(), resolver_from_env(), slack=build_slack_service())


app = build_app()
