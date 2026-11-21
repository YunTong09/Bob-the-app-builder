"""Server-side owner derivation for the local demo.

This module implements the restricted, loopback-only single-user demo
identity. The hosted invite-code mode (``R2R_IDENTITY_MODE=invite_code``) lives
in ``invite_auth.py`` and is selected in ``main.py``; any other mode refuses to
start.

Client-supplied ``userId`` / ``sessionId`` values are never read: the wire
models reject them as unknown fields, and nothing here inspects them.
"""

from __future__ import annotations

import ipaddress
import os
from typing import Callable

from fastapi import Request

from backend.application.ports import OwnerContext

from .errors import ApiError

IdentityResolver = Callable[[Request], OwnerContext]

DEMO_OWNER_ID = "local-demo-owner"
_PROXY_HEADERS = (b"forwarded", b"x-forwarded-for", b"x-real-ip")


def _unauthenticated() -> ApiError:
    return ApiError(401, "UNAUTHENTICATED", "This server only accepts requests from the local demo machine.")


def _is_loopback(host: str | None) -> bool:
    if not host:
        return False
    try:
        return ipaddress.ip_address(host).is_loopback
    except ValueError:
        return False


def demo_local_resolver(request: Request) -> OwnerContext:
    """Single-user demo owner, accepted only for direct loopback connections.

    Requests arriving through a proxy are refused, because a proxy on the same
    machine could otherwise expose the shared demo identity to other users.
    """
    client = request.client
    if client is None or not _is_loopback(client.host):
        raise _unauthenticated()
    if any(name in _PROXY_HEADERS for name, _ in request.scope.get("headers", [])):
        raise _unauthenticated()
    return OwnerContext(owner_id=DEMO_OWNER_ID, mode="demo_local")


def resolver_from_env() -> IdentityResolver:
    mode = os.environ.get("R2R_IDENTITY_MODE", "demo_local")
    if mode != "demo_local":
        raise RuntimeError("R2R_IDENTITY_MODE must be 'demo_local' or 'invite_code'.")
    return demo_local_resolver
