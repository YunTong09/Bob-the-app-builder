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
from backend.config import load_backend_env
from backend.services.slack import build_slack_service

from .app import create_app
from .identity import resolver_from_env
from .invite_auth import InviteSessions, SlidingWindowLimiter, parse_invites


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


def _positive_int(name: str, default: int) -> int:
    raw = os.environ.get(name, "").strip()
    if not raw:
        return default
    if not raw.isascii() or not raw.isdigit() or int(raw) < 1:
        raise RuntimeError(f"{name} must be a positive integer.")
    return int(raw)


def _build_invite_app() -> FastAPI:
    """Hosted mode behind a same-origin HTTPS gateway (see deploy/gce/).

    Start uvicorn with ``--proxy-headers --forwarded-allow-ips 127.0.0.1`` so
    sign-in throttling sees the visitor's address rather than the gateway's.
    """
    if os.environ.get("R2R_WEB_ORIGIN", "").strip():
        raise RuntimeError("R2R_WEB_ORIGIN is for the local demo only; unset it in invite_code mode.")
    public_origin = os.environ.get("R2R_PUBLIC_ORIGIN", "").strip()
    match = re.fullmatch(r"https://([a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?(?:\.[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?)+)", public_origin)
    if not match:
        raise RuntimeError("R2R_PUBLIC_ORIGIN must be the site's https:// origin, such as https://example.com.")

    sessions = InviteSessions(
        parse_invites(os.environ.get("R2R_INVITES", "")),
        os.environ.get("R2R_SESSION_SECRET", "").strip(),
        ttl_seconds=_positive_int("R2R_SESSION_TTL_HOURS", 168) * 3600,
    )
    app = create_app(
        _build_services(),
        sessions.resolve,
        slack=build_slack_service(),
        sessions=sessions,
        login_limiter=SlidingWindowLimiter(limit=_positive_int("R2R_LOGIN_FAILURES_PER_15_MIN", 10), window_seconds=15 * 60),
        generate_limiter=SlidingWindowLimiter(limit=_positive_int("R2R_GENERATE_LIMIT_PER_HOUR", 30), window_seconds=3600),
    )
    # Same-origin gateway: no CORS. Loopback hosts allow on-VM health checks.
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=[match.group(1), "127.0.0.1", "localhost"])
    return app


def build_app() -> FastAPI:
    load_backend_env()
    mode = os.environ.get("R2R_IDENTITY_MODE", "demo_local")
    if mode == "invite_code":
        return _build_invite_app()
    web_origin = os.environ.get("R2R_WEB_ORIGIN", "").strip()
    if web_origin and not re.fullmatch(r"http://(?:127\.0\.0\.1|localhost):[1-9][0-9]{0,4}", web_origin):
        raise RuntimeError("R2R_WEB_ORIGIN must be an explicit HTTP loopback origin with a port.")

    app = create_app(_build_services(), resolver_from_env(), slack=build_slack_service())
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
