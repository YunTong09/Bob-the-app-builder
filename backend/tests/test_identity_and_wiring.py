"""Demo identity restrictions and the composition root."""

from __future__ import annotations

import importlib

import pytest
from fastapi.testclient import TestClient

from backend.api.app import create_app
from backend.api.identity import demo_local_resolver, resolver_from_env
from backend.devstubs import build_stub_services

from .conftest import GEN_BODY, load_fixture
from .test_boundary import assert_error


def demo_client(host: str) -> TestClient:
    app = create_app(build_stub_services(), demo_local_resolver)
    return TestClient(app, client=(host, 50000), raise_server_exceptions=False)


@pytest.mark.parametrize("host", ["127.0.0.1", "::1"])
def test_demo_identity_allows_loopback(host):
    c = demo_client(host)
    assert c.post("/api/memory/import", json=load_fixture("import_request.json")).status_code == 200
    assert c.get("/api/memory/search").json()["total"] == 2


@pytest.mark.parametrize("host", ["192.168.1.20", "10.0.0.5", "testclient"])
def test_demo_identity_rejects_non_loopback(host):
    assert_error(demo_client(host).get("/api/memory/search"), 401, "UNAUTHENTICATED")


@pytest.mark.parametrize("header", ["X-Forwarded-For", "Forwarded", "X-Real-IP"])
def test_demo_identity_rejects_proxied_requests(header):
    r = demo_client("127.0.0.1").get("/api/memory/search", headers={header: "203.0.113.9"})
    assert_error(r, 401, "UNAUTHENTICATED")


def test_other_identity_modes_refuse_to_start(monkeypatch):
    monkeypatch.setenv("R2R_IDENTITY_MODE", "authenticated")
    with pytest.raises(RuntimeError):
        resolver_from_env()


def test_real_services_without_model_config_fail_loudly(monkeypatch):
    """No silent fallback to mock/stub replies when Claude is not configured."""
    import sys

    monkeypatch.setenv("R2R_SERVICES", "real")
    monkeypatch.delenv("R2R_AI_MODE", raising=False)
    monkeypatch.delenv("ANTHROPIC_MODEL", raising=False)
    monkeypatch.delitem(sys.modules, "backend.api.main", raising=False)
    with pytest.raises(RuntimeError, match="ANTHROPIC_MODEL"):
        importlib.import_module("backend.api.main")


def test_real_services_mock_mode_builds(monkeypatch, tmp_path):
    import sys

    monkeypatch.setenv("R2R_SERVICES", "real")
    monkeypatch.setenv("R2R_AI_MODE", "mock")
    monkeypatch.setenv("R2R_DB_PATH", str(tmp_path / "db.sqlite3"))
    monkeypatch.delitem(sys.modules, "backend.api.main", raising=False)
    main = importlib.import_module("backend.api.main")
    c = TestClient(main.app, client=("127.0.0.1", 50000))
    assert c.post("/api/memory/import", json=load_fixture("import_request.json")).json() == {"importedCount": 2, "skippedCount": 0}
    assert c.post("/api/reply/generate", json=GEN_BODY).status_code == 200


def test_stub_mode_full_flow(monkeypatch):
    """Smoke test of the runnable dev server wiring (stubs, loopback identity)."""
    import sys

    monkeypatch.setenv("R2R_SERVICES", "stub")
    monkeypatch.delitem(sys.modules, "backend.api.main", raising=False)
    main = importlib.import_module("backend.api.main")
    c = TestClient(main.app, client=("127.0.0.1", 50000))
    c.post("/api/memory/import", json=load_fixture("import_request.json"))
    r = c.post("/api/reply/generate", json={**GEN_BODY, "employeeDraft": "The documents were uploaded to the shared drive."})
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["reply"].startswith("[stub")
    assert [e["messageId"] for e in body["evidence"]] == ["msg_001"]
    assert body["evidence"][0]["content"] == "I've uploaded the documents to the shared drive."
