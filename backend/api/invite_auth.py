"""Invite-code sessions for the hosted demo (``R2R_IDENTITY_MODE=invite_code``).

Each invited person receives a distinct, randomly generated code. The server
stores only ``label:sha256(code)`` pairs (``R2R_INVITES``), exchanges a valid
code for a signed, HttpOnly session cookie and derives the owner from that
cookie as ``invite:<label>``. Client-supplied identifiers are never trusted.

Sessions are stateless HMAC tokens bound to the label and the current code
hash, so removing an invite or rotating its code invalidates existing
sessions on the next request. Nothing here logs codes, cookies or secrets.

Generate a new invite::

    python -m backend.api.invite_auth organizer
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import math
import re
import secrets
import sys
import threading
import time
from collections import deque
from typing import Callable

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from backend.application.ports import OwnerContext
from backend.models.wire import CreateSessionRequest, SessionResponse

from .errors import ApiError

SESSION_COOKIE = "__Host-r2r_session"
OWNER_PREFIX = "invite:"
MIN_SECRET_CHARS = 32
DEFAULT_TTL_SECONDS = 7 * 24 * 3600

_LABEL = re.compile(r"[a-z0-9][a-z0-9-]{0,31}")
_HASH = re.compile(r"[0-9a-f]{64}")
_CODE_ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"  # no 0/O or 1/I
_CODE_PREFIX = "R2R"


# ------------------------------------------------------------------ codes


def normalize_code(raw: str) -> str:
    """Case-, space- and dash-insensitive so codes are easy to type."""
    return re.sub(r"[\s-]+", "", raw).upper()


def hash_code(raw: str) -> str:
    return hashlib.sha256(normalize_code(raw).encode("utf-8")).hexdigest()


def generate_code() -> str:
    groups = ["".join(secrets.choice(_CODE_ALPHABET) for _ in range(4)) for _ in range(4)]
    return "-".join([_CODE_PREFIX, *groups])


def parse_invites(spec: str) -> dict[str, str]:
    """Parse ``label:sha256hex`` entries separated by newlines or commas."""
    invites: dict[str, str] = {}
    seen_hashes: set[str] = set()
    for number, entry in enumerate(re.split(r"[\n,]", spec), start=1):
        entry = entry.strip()
        if not entry or entry.startswith("#"):
            continue
        label, sep, digest = entry.partition(":")
        label, digest = label.strip(), digest.strip().lower()
        if not sep or not _LABEL.fullmatch(label) or not _HASH.fullmatch(digest):
            raise RuntimeError(f"R2R_INVITES entry {number} must be 'label:sha256hex' with a lowercase label.")
        if label in invites or digest in seen_hashes:
            raise RuntimeError(f"R2R_INVITES entry {number} repeats a label or code.")
        invites[label] = digest
        seen_hashes.add(digest)
    if not invites:
        raise RuntimeError("R2R_INVITES must contain at least one invite.")
    return invites


# ------------------------------------------------------------------ limits


class SlidingWindowLimiter:
    """In-process sliding-window counter (the hosted backend runs one process)."""

    def __init__(
        self,
        limit: int,
        window_seconds: float,
        clock: Callable[[], float] = time.monotonic,
        max_keys: int = 10_000,
    ) -> None:
        if limit < 1 or window_seconds <= 0:
            raise ValueError("limit and window must be positive")
        self.limit = limit
        self.window = window_seconds
        self._clock = clock
        self._max_keys = max_keys
        self._events: dict[str, deque[float]] = {}
        self._lock = threading.Lock()

    def _recent(self, key: str, now: float) -> deque[float]:
        if key not in self._events and len(self._events) >= self._max_keys:
            # Bound memory: drop idle keys, then the oldest keys if still full.
            for idle in [k for k, v in self._events.items() if not v or v[-1] <= now - self.window]:
                del self._events[idle]
            while len(self._events) >= self._max_keys:
                del self._events[next(iter(self._events))]
        events = self._events.setdefault(key, deque())
        while events and events[0] <= now - self.window:
            events.popleft()
        return events

    def _delay(self, events: deque[float], now: float) -> int | None:
        if len(events) < self.limit:
            return None
        return max(1, math.ceil(events[0] + self.window - now))

    def retry_after(self, key: str) -> int | None:
        """Seconds until another event is allowed, or ``None`` if allowed now."""
        with self._lock:
            now = self._clock()
            return self._delay(self._recent(key, now), now)

    def record(self, key: str) -> None:
        with self._lock:
            now = self._clock()
            self._recent(key, now).append(now)

    def hit(self, key: str) -> int | None:
        """Record an event if allowed; otherwise return the retry delay."""
        with self._lock:
            now = self._clock()
            events = self._recent(key, now)
            delay = self._delay(events, now)
            if delay is None:
                events.append(now)
            return delay


def rate_limited(message: str, retry_after: int) -> ApiError:
    return ApiError(429, "RATE_LIMITED", message, headers={"Retry-After": str(max(1, min(3600, retry_after)))})


# ------------------------------------------------------------------ sessions


def _unauthenticated() -> ApiError:
    return ApiError(401, "UNAUTHENTICATED", "Sign in with your invite code.")


class InviteSessions:
    def __init__(
        self,
        invites: dict[str, str],
        secret: str,
        ttl_seconds: int = DEFAULT_TTL_SECONDS,
        clock: Callable[[], float] = time.time,
    ) -> None:
        if len(secret) < MIN_SECRET_CHARS:
            raise RuntimeError(f"R2R_SESSION_SECRET must contain at least {MIN_SECRET_CHARS} characters.")
        if ttl_seconds < 60:
            raise RuntimeError("Session lifetime must be at least one minute.")
        self._invites = dict(invites)
        self._by_hash = {digest: label for label, digest in invites.items()}
        self._key = secret.encode("utf-8")
        self.ttl_seconds = ttl_seconds
        self._clock = clock

    def label_for_code(self, raw_code: str) -> str | None:
        digest = hash_code(raw_code)
        match = None
        for known, label in self._by_hash.items():
            if hmac.compare_digest(known, digest):
                match = label
        return match

    def _signature(self, label: str, expires: int) -> str:
        message = f"{label}.{expires}.{self._invites[label]}".encode("utf-8")
        mac = hmac.new(self._key, message, hashlib.sha256).digest()
        return base64.urlsafe_b64encode(mac).rstrip(b"=").decode("ascii")

    def issue(self, label: str) -> str:
        expires = int(self._clock()) + self.ttl_seconds
        return f"{label}.{expires}.{self._signature(label, expires)}"

    def verify(self, token: str | None) -> str | None:
        if not token or len(token) > 200:
            return None
        parts = token.split(".")
        if len(parts) != 3:
            return None
        label, expires_text, signature = parts
        if label not in self._invites or not expires_text.isascii() or not expires_text.isdigit():
            return None
        expires = int(expires_text)
        if expires <= self._clock():
            return None
        if not hmac.compare_digest(signature, self._signature(label, expires)):
            return None
        return label

    def resolve(self, request: Request) -> OwnerContext:
        label = self.verify(request.cookies.get(SESSION_COOKIE))
        if label is None:
            raise _unauthenticated()
        return OwnerContext(owner_id=OWNER_PREFIX + label, mode="authenticated")


def install_session_routes(
    app: FastAPI,
    sessions: InviteSessions,
    parse_body: Callable,
    reject_query_params: Callable,
    login_limiter: SlidingWindowLimiter,
) -> None:
    """Register ``/api/session``. Parsing helpers come from ``app.py`` so the
    415/400/422 behaviour matches every other contracted route."""

    def _set_cookie(response: JSONResponse, value: str) -> None:
        response.set_cookie(
            SESSION_COOKIE,
            value,
            max_age=sessions.ttl_seconds,
            path="/",
            secure=True,
            httponly=True,
            samesite="strict",
        )

    @app.post("/api/session")
    async def create_session(request: Request) -> JSONResponse:
        reject_query_params(request, set())
        client = request.client.host if request.client else "unknown"
        retry = login_limiter.retry_after(client)
        if retry is not None:
            raise rate_limited("Too many sign-in attempts. Try again later.", retry)
        body = await parse_body(request, CreateSessionRequest)
        label = sessions.label_for_code(body.invite_code)
        if label is None:
            login_limiter.record(client)
            raise ApiError(401, "UNAUTHENTICATED", "That invite code is not valid.")
        response = JSONResponse(SessionResponse(authenticated=True).model_dump(by_alias=True))
        _set_cookie(response, sessions.issue(label))
        return response

    @app.get("/api/session")
    async def read_session(request: Request) -> SessionResponse:
        reject_query_params(request, set())
        sessions.resolve(request)
        return SessionResponse(authenticated=True)

    @app.delete("/api/session")
    async def delete_session(request: Request) -> JSONResponse:
        reject_query_params(request, set())
        response = JSONResponse(SessionResponse(authenticated=False).model_dump(by_alias=True))
        response.delete_cookie(SESSION_COOKIE, path="/", secure=True, httponly=True, samesite="strict")
        return response


# ------------------------------------------------------------------ CLI


def _main(argv: list[str]) -> int:
    if len(argv) != 1 or not _LABEL.fullmatch(argv[0]):
        print("Usage: python -m backend.api.invite_auth <label>  (lowercase letters, digits, dashes)", file=sys.stderr)
        return 2
    code = generate_code()
    print(f"Invite code for {argv[0]} (share privately): {code}")
    print(f"R2R_INVITES entry: {argv[0]}:{hash_code(code)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(_main(sys.argv[1:]))
