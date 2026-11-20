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
import re

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.trustedhost import TrustedHostMiddleware

from backend.application.ports import Services

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
    web_origin = os.environ.get("R2R_WEB_ORIGIN", "").strip()
    if web_origin and not re.fullmatch(r"http://(?:127\.0\.0\.1|localhost):[1-9][0-9]{0,4}", web_origin):
        raise RuntimeError("R2R_WEB_ORIGIN must be an explicit HTTP loopback origin with a port.")

    app = create_app(_build_services(), resolver_from_env())
    if web_origin:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=[web_origin],
            allow_methods=["GET", "POST", "PUT", "DELETE"],
            allow_headers=["Content-Type"],
        )
        app.add_middleware(TrustedHostMiddleware, allowed_hosts=["127.0.0.1", "localhost"])
    return app


app = build_app()
