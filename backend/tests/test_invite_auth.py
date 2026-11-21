"""Hosted invite-code sessions: sign-in, cookies, isolation, throttling, wiring."""

from __future__ import annotations

import importlib
import logging
import re
import sys
from dataclasses import replace

import pytest
from fastapi.testclient import TestClient

from backend.api.app import create_app
from backend.api.invite_auth import (
    SESSION_COOKIE,
    InviteSessions,
    SlidingWindowLimiter,
    _main,
    generate_code,
    hash_code,
    normalize_code,
    parse_invites,
)
from backend.devstubs import build_stub_services
from backend.memory.sqlite_store import SqliteMemoryService

from .conftest import GEN_BODY, load_fixture
from .test_boundary import assert_error

SECRET = "s" * 40
CODE_A = "R2R-AAAA-BBBB-CCCC-DDDD"
CODE_B = "R2R-EEEE-FFFF-GGGG-HHHH"
INVITES = {"organizer": hash_code(CODE_A), "team": hash_code(CODE_B)}


class Clock:
    def __init__(self, now: float = 1_000_000.0) -> None:
        self.now = now

    def __call__(self) -> float:
        return self.now


def make_client(
    services=None,
    *,
    invites=None,
    clock=None,
    login_limiter=None,
    generate_limiter=None,
) -> tuple[TestClient, InviteSessions]:
    sessions = InviteSessions(invites or INVITES, SECRET, clock=clock or Clock())
    app = create_app(
        services or build_stub_services(),
        sessions.resolve,
        sessions=sessions,
        login_limiter=login_limiter,
        generate_limiter=generate_limiter,
    )
    return TestClient(app, base_url="https://testserver", raise_server_exceptions=False), sessions


def sign_in(client: TestClient, code: str = CODE_A):
    return client.post("/api/session", json={"inviteCode": code})


# ------------------------------------------------------------------ codes


def test_codes_are_case_space_and_dash_insensitive():
    assert normalize_code(" r2r-aaaa bbbb-cccc-dddd ") == "R2RAAAABBBBCCCCDDDD"
    assert hash_code("r2r aaaa-bbbb cccc dddd") == hash_code(CODE_A)


def test_generated_codes_are_random_and_typeable():
    codes = {generate_code() for _ in range(50)}
    assert len(codes) == 50
    for code in codes:
        assert re.fullmatch(r"R2R(-[A-HJ-NP-Z2-9]{4}){4}", code)


def test_parse_invites_accepts_lines_commas_and_comments():
    spec = f"# invited\norganizer:{INVITES['organizer']}\n\n team : {INVITES['team'].upper()} "
    assert parse_invites(spec) == INVITES
    assert parse_invites(f"organizer:{INVITES['organizer']},team:{INVITES['team']}") == INVITES


@pytest.mark.parametrize(
    "spec",
    [
        "",
        "# only a comment",
        "organizer",
        f"Organizer:{INVITES['organizer']}",
        "organizer:abc123",
        f"organizer:{INVITES['organizer']}\norganizer:{INVITES['team']}",
        f"organizer:{INVITES['organizer']}\nteam:{INVITES['organizer']}",
    ],
)
def test_parse_invites_rejects_invalid_or_duplicate_entries(spec):
    with pytest.raises(RuntimeError) as excinfo:
        parse_invites(spec)
    assert INVITES["organizer"] not in str(excinfo.value)


def test_short_session_secret_refuses_to_start():
    with pytest.raises(RuntimeError, match="R2R_SESSION_SECRET"):
        InviteSessions(INVITES, "too-short")


def test_cli_prints_code_and_matching_entry(capsys, monkeypatch):
    monkeypatch.delenv("R2R_PUBLIC_ORIGIN", raising=False)
    assert _main(["judge-1"]) == 0
    out = capsys.readouterr().out
    code = re.search(r"R2R(-[A-Z0-9]{4}){4}", out).group(0)
    assert f"judge-1:{hash_code(code)}" in out
    assert "/login#" not in out
    assert _main(["Bad Label"]) == 2


def test_cli_prints_personal_link_for_https_origin(capsys, monkeypatch):
    monkeypatch.setenv("R2R_PUBLIC_ORIGIN", "https://ragetoreply.example/")
    assert _main(["team"]) == 0
    out = capsys.readouterr().out
    code = re.search(r"R2R(-[A-Z0-9]{4}){4}", out).group(0)
    assert f"https://ragetoreply.example/login#{code}" in out
    assert f"team:{hash_code(code)}" in out


# ------------------------------------------------------------------ sign-in


def test_sign_in_sets_hardened_session_cookie():
    client, _ = make_client()
    r = sign_in(client)
    assert r.status_code == 200
    assert r.json() == {"authenticated": True}
    cookie = r.headers["set-cookie"]
    assert cookie.startswith(f"{SESSION_COOKIE}=")
    for attribute in ("HttpOnly", "Secure", "SameSite=strict", "Path=/", "Max-Age=604800"):
        assert attribute.lower() in cookie.lower()
    assert "domain=" not in cookie.lower()
    assert CODE_A not in cookie


def test_session_grants_access_to_contracted_routes():
    client, _ = make_client()
    assert sign_in(client, "r2r-aaaa-bbbb-cccc-dddd").status_code == 200
    assert client.get("/api/session").json() == {"authenticated": True}
    assert client.post("/api/memory/import", json=load_fixture("import_request.json")).status_code == 200
    assert client.get("/api/memory/search").json()["total"] == 2
    assert client.post("/api/reply/generate", json=GEN_BODY).status_code == 200


@pytest.mark.parametrize(
    ("method", "path"),
    [("GET", "/api/session"), ("GET", "/api/memory/search"), ("DELETE", "/api/memory"), ("POST", "/api/reply/generate")],
)
def test_missing_session_is_unauthenticated(method, path):
    client, _ = make_client()
    r = client.request(method, path, json=GEN_BODY if method == "POST" else None)
    assert_error(r, 401, "UNAUTHENTICATED")


def test_wrong_code_is_rejected_without_cookie_or_echo(caplog):
    client, _ = make_client()
    with caplog.at_level(logging.DEBUG):
        r = sign_in(client, "R2R-WRONG-CODE")
    assert_error(r, 401, "UNAUTHENTICATED")
    assert "set-cookie" not in r.headers
    assert "R2R-WRONG-CODE" not in r.text
    assert "R2R-WRONG-CODE" not in caplog.text


def test_proxy_and_identity_headers_do_not_grant_access():
    client, _ = make_client()
    r = client.get(
        "/api/memory/search",
        headers={"X-Forwarded-For": "127.0.0.1", "X-Test-Owner": "organizer", "Cookie": f"{SESSION_COOKIE}=organizer.9999999999.forged"},
    )
    assert_error(r, 401, "UNAUTHENTICATED")


def test_proxied_requests_with_valid_session_are_accepted():
    client, _ = make_client()
    sign_in(client)
    assert client.get("/api/memory/search", headers={"X-Forwarded-For": "203.0.113.9"}).status_code == 200


@pytest.mark.parametrize("change", ["label", "expiry", "signature", "shape"])
def test_tampered_cookies_are_rejected(change):
    client, sessions = make_client()
    label, expires, signature = sessions.issue("organizer").split(".")
    forged = {
        "label": f"team.{expires}.{signature}",
        "expiry": f"{label}.{int(expires) + 3600}.{signature}",
        "signature": f"{label}.{expires}.{signature[:-2]}AA",
        "shape": f"{label}.{expires}",
    }[change]
    client.cookies.set(SESSION_COOKIE, forged)
    assert_error(client.get("/api/session"), 401, "UNAUTHENTICATED")


def test_sessions_expire():
    clock = Clock()
    client, sessions = make_client(clock=clock)
    sign_in(client)
    clock.now += sessions.ttl_seconds - 1
    assert client.get("/api/session").status_code == 200
    clock.now += 2
    assert_error(client.get("/api/session"), 401, "UNAUTHENTICATED")


def test_removing_or_rotating_an_invite_revokes_existing_sessions():
    clock = Clock()
    _, sessions = make_client(clock=clock)
    token = sessions.issue("organizer")

    rotated = InviteSessions({**INVITES, "organizer": hash_code("R2R-NEW1-NEW2-NEW3-NEW4")}, SECRET, clock=clock)
    removed = InviteSessions({"team": INVITES["team"]}, SECRET, clock=clock)
    other_secret = InviteSessions(INVITES, "t" * 40, clock=clock)
    assert sessions.verify(token) == "organizer"
    assert rotated.verify(token) is None
    assert removed.verify(token) is None
    assert other_secret.verify(token) is None


def test_sign_out_clears_the_cookie():
    client, _ = make_client()
    sign_in(client)
    r = client.delete("/api/session")
    assert r.status_code == 200
    assert r.json() == {"authenticated": False}
    assert SESSION_COOKIE in r.headers["set-cookie"] and "max-age=0" in r.headers["set-cookie"].lower()
    assert_error(client.get("/api/session"), 401, "UNAUTHENTICATED")


@pytest.mark.parametrize("store", ["in_memory", "sqlite"])
def test_invites_have_isolated_memory(store, tmp_path):
    services = build_stub_services()
    if store == "sqlite":
        services = replace(services, memory=SqliteMemoryService(tmp_path / "memory.sqlite3"))
    organizer, _ = make_client(services)
    team, _ = make_client(services)
    sign_in(organizer, CODE_A)
    sign_in(team, CODE_B)

    assert organizer.post("/api/memory/import", json=load_fixture("import_request.json")).status_code == 200
    assert organizer.get("/api/memory/search").json()["total"] == 2
    assert team.get("/api/memory/search").json()["total"] == 0
    assert team.delete("/api/memory").json() == {"deletedCount": 0}
    assert organizer.get("/api/memory/search").json()["total"] == 2


def test_owner_is_derived_from_the_invite_label(services, ai):
    client, _ = make_client(services)
    sign_in(client, CODE_B)
    assert client.post("/api/reply/generate", json=GEN_BODY).status_code == 200
    owner = ai.calls[0][1]
    assert owner.owner_id == "invite:team"
    assert owner.mode == "authenticated"


# ------------------------------------------------------------------ validation


@pytest.mark.parametrize(
    ("kwargs", "status", "code"),
    [
        ({"content": b'{"inviteCode": "x"}', "headers": {"Content-Type": "text/plain"}}, 415, "UNSUPPORTED_MEDIA_TYPE"),
        ({"content": b"{not json", "headers": {"Content-Type": "application/json"}}, 400, "INVALID_JSON"),
        ({"json": {}}, 422, "VALIDATION_ERROR"),
        ({"json": {"inviteCode": "   "}}, 422, "VALIDATION_ERROR"),
        ({"json": {"inviteCode": 123}}, 422, "VALIDATION_ERROR"),
        ({"json": {"inviteCode": "x" * 65}}, 422, "VALIDATION_ERROR"),
        ({"json": {"inviteCode": CODE_A, "userId": "organizer"}}, 422, "VALIDATION_ERROR"),
    ],
)
def test_sign_in_validation_errors(kwargs, status, code):
    client, _ = make_client()
    r = client.post("/api/session", **kwargs)
    assert_error(r, status, code)
    assert "set-cookie" not in r.headers


def test_session_routes_reject_query_parameters():
    client, _ = make_client()
    assert_error(client.post("/api/session?userId=x", json={"inviteCode": CODE_A}), 422, "VALIDATION_ERROR")


def test_session_routes_do_not_exist_in_demo_mode():
    from backend.api.identity import demo_local_resolver

    client = TestClient(create_app(build_stub_services(), demo_local_resolver), client=("127.0.0.1", 50000))
    assert_error(client.post("/api/session", json={"inviteCode": CODE_A}), 404, "NOT_FOUND")


# ------------------------------------------------------------------ throttling


def test_repeated_failed_sign_ins_are_throttled_per_client():
    clock = Clock()
    limiter = SlidingWindowLimiter(limit=3, window_seconds=900, clock=clock)
    client, _ = make_client(login_limiter=limiter)
    for _ in range(3):
        assert_error(sign_in(client, "R2R-BAD"), 401, "UNAUTHENTICATED")

    blocked = sign_in(client, CODE_A)  # even a valid code waits out the lockout
    assert_error(blocked, 429, "RATE_LIMITED")
    assert 1 <= int(blocked.headers["retry-after"]) <= 900
    assert "set-cookie" not in blocked.headers

    clock.now += 901
    assert sign_in(client, CODE_A).status_code == 200


def test_successful_sign_ins_do_not_count_toward_lockout():
    limiter = SlidingWindowLimiter(limit=2, window_seconds=900, clock=Clock())
    client, _ = make_client(login_limiter=limiter)
    for _ in range(5):
        assert sign_in(client).status_code == 200


def test_generation_is_limited_per_owner():
    clock = Clock()
    services = build_stub_services()
    limiter = SlidingWindowLimiter(limit=2, window_seconds=3600, clock=clock)
    organizer, _ = make_client(services, generate_limiter=limiter)
    team, _ = make_client(services, generate_limiter=limiter)
    sign_in(organizer, CODE_A)
    sign_in(team, CODE_B)

    assert organizer.post("/api/reply/generate", json=GEN_BODY).status_code == 200
    assert organizer.post("/api/reply/generate", json=GEN_BODY).status_code == 200
    limited = organizer.post("/api/reply/generate", json=GEN_BODY)
    assert_error(limited, 429, "RATE_LIMITED")
    assert 1 <= int(limited.headers["retry-after"]) <= 3600
    assert team.post("/api/reply/generate", json=GEN_BODY).status_code == 200

    clock.now += 3601
    assert organizer.post("/api/reply/generate", json=GEN_BODY).status_code == 200


def test_invalid_generation_requests_do_not_consume_the_limit():
    limiter = SlidingWindowLimiter(limit=1, window_seconds=3600, clock=Clock())
    client, _ = make_client(generate_limiter=limiter)
    sign_in(client)
    assert_error(client.post("/api/reply/generate", json={"tone": "neutral"}), 422, "VALIDATION_ERROR")
    assert client.post("/api/reply/generate", json=GEN_BODY).status_code == 200


def test_limiter_bounds_tracked_keys():
    clock = Clock()
    limiter = SlidingWindowLimiter(limit=1, window_seconds=60, clock=clock, max_keys=3)
    for i in range(10):
        limiter.record(f"client-{i}")
    assert len(limiter._events) <= 3


# ------------------------------------------------------------------ composition root


def invite_env(monkeypatch, **overrides):
    env = {
        "R2R_IDENTITY_MODE": "invite_code",
        "R2R_SERVICES": "stub",
        "R2R_PUBLIC_ORIGIN": "https://rage-to-reply.example",
        "R2R_INVITES": f"organizer:{INVITES['organizer']}\nteam:{INVITES['team']}",
        "R2R_SESSION_SECRET": SECRET,
    }
    env.update(overrides)
    monkeypatch.delenv("R2R_WEB_ORIGIN", raising=False)
    for key, value in env.items():
        if value is None:
            monkeypatch.delenv(key, raising=False)
        else:
            monkeypatch.setenv(key, value)
    monkeypatch.delitem(sys.modules, "backend.api.main", raising=False)


def test_invite_mode_full_flow_through_composition_root(monkeypatch):
    invite_env(monkeypatch)
    main = importlib.import_module("backend.api.main")
    client = TestClient(main.app, base_url="https://rage-to-reply.example", client=("203.0.113.9", 50000))
    assert_error(client.get("/api/memory/search"), 401, "UNAUTHENTICATED")
    assert sign_in(client).status_code == 200
    assert client.post("/api/memory/import", json=load_fixture("import_request.json")).status_code == 200
    assert client.post("/api/reply/generate", json=GEN_BODY).status_code == 200

    # No CORS in the same-origin deployment; unknown hosts are refused.
    preflight = client.options(
        "/api/reply/generate",
        headers={"Origin": "https://evil.example", "Access-Control-Request-Method": "POST"},
    )
    assert "access-control-allow-origin" not in preflight.headers
    assert client.get("/api/session", headers={"Host": "evil.example"}).status_code == 400
    local = TestClient(main.app, base_url="http://127.0.0.1:8000", client=("127.0.0.1", 50000))
    assert_error(local.get("/api/memory/search"), 401, "UNAUTHENTICATED")


def test_invite_mode_applies_configured_generation_limit(monkeypatch):
    invite_env(monkeypatch, R2R_GENERATE_LIMIT_PER_HOUR="1")
    main = importlib.import_module("backend.api.main")
    client = TestClient(main.app, base_url="https://rage-to-reply.example")
    sign_in(client)
    assert client.post("/api/reply/generate", json=GEN_BODY).status_code == 200
    assert_error(client.post("/api/reply/generate", json=GEN_BODY), 429, "RATE_LIMITED")


@pytest.mark.parametrize(
    ("overrides", "message"),
    [
        ({"R2R_PUBLIC_ORIGIN": None}, "R2R_PUBLIC_ORIGIN"),
        ({"R2R_PUBLIC_ORIGIN": "http://rage-to-reply.example"}, "R2R_PUBLIC_ORIGIN"),
        ({"R2R_PUBLIC_ORIGIN": "https://rage-to-reply.example/app"}, "R2R_PUBLIC_ORIGIN"),
        ({"R2R_PUBLIC_ORIGIN": "https://localhost"}, "R2R_PUBLIC_ORIGIN"),
        ({"R2R_WEB_ORIGIN": "http://127.0.0.1:3000"}, "R2R_WEB_ORIGIN"),
        ({"R2R_INVITES": None}, "R2R_INVITES"),
        ({"R2R_SESSION_SECRET": "short"}, "R2R_SESSION_SECRET"),
        ({"R2R_SESSION_TTL_HOURS": "0"}, "R2R_SESSION_TTL_HOURS"),
        ({"R2R_GENERATE_LIMIT_PER_HOUR": "lots"}, "R2R_GENERATE_LIMIT_PER_HOUR"),
    ],
)
def test_invite_mode_misconfiguration_fails_loudly(monkeypatch, overrides, message):
    invite_env(monkeypatch, **overrides)
    with pytest.raises(RuntimeError, match=message):
        importlib.import_module("backend.api.main")
