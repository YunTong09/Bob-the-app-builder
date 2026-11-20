"""Slack preview HTTP integration; Slack and Claude never receive real calls."""

from __future__ import annotations

import importlib
import sys
from contextlib import contextmanager

import httpx
import pytest
from fastapi.testclient import TestClient

from backend.api.app import create_app
from backend.api.identity import demo_local_resolver
from backend.application.ports import MemoryRecord
from backend.services.slack import SlackHistoryService, SlackPreviewPage

from .test_boundary import assert_error

CHANNEL = "CDEMO123"
TEAM = "TDEMO123"
TOKEN = "xoxb-synthetic-test-token"
PRIVATE_PROVIDER_TEXT = "SYNTHETIC-PRIVATE-PROVIDER-CONTENT"


def message(ts="1700000000.123456", text="  Please review the budget.\n", **fields):
    return {"type": "message", "user": "UEMPLOYEE", "text": text, "ts": ts, **fields}


def page(messages=(), cursor=""):
    return {
        "ok": True,
        "messages": list(messages),
        "has_more": bool(cursor),
        "response_metadata": {"next_cursor": cursor},
    }


@contextmanager
def preview_client(services, history=None, *, handler=None, host="127.0.0.1"):
    """Use the real Slack service with an in-process HTTP transport."""
    requests = []

    def dispatch(request):
        requests.append(request)
        assert request.url.host == "slack.com"
        assert request.headers["Authorization"] == f"Bearer {TOKEN}"
        if handler is not None:
            return handler(request)
        if request.url.path == "/api/auth.test":
            assert request.method == "POST"
            return httpx.Response(200, json={"ok": True, "team_id": TEAM})
        assert request.url.path == "/api/conversations.history"
        assert request.method == "GET"
        return httpx.Response(200, json=history if history is not None else page())

    with httpx.Client(transport=httpx.MockTransport(dispatch)) as upstream:
        slack = SlackHistoryService(TOKEN, CHANNEL, client=upstream)
        app = create_app(services, demo_local_resolver, slack=slack)
        with TestClient(app, client=(host, 50000), raise_server_exceptions=False) as client:
            yield client, requests


def test_preview_selection_import_review_delete_without_ai(services, ai):
    history = page([message(), message("1700000001.000001", "A second, unselected message.")])
    with preview_client(services, history) as (client, requests):
        response = client.post("/api/slack/preview", json={"channelId": CHANNEL})
        assert response.status_code == 200, response.text
        preview = response.json()
        assert set(preview) == {"messages", "nextCursor", "skippedCount", "warnings"}
        assert preview["nextCursor"] is None and preview["skippedCount"] == 0
        assert preview["warnings"]
        assert preview["messages"][0] == {
            "id": f"slack:{TEAM}:{CHANNEL}:1700000000.123456",
            "conversationId": f"slack:{TEAM}:{CHANNEL}",
            "sender": "UEMPLOYEE",
            "content": "  Please review the budget.\n",
            "timestamp": "2023-11-14T22:13:20.123456+00:00",
            "source": f"Slack {TEAM}/{CHANNEL}/1700000000.123456",
        }
        assert client.get("/api/memory/search").json()["total"] == 0
        selected = preview["messages"][:1]
        saved = client.post("/api/memory/import", json={"messages": selected})
        assert saved.status_code == 200, saved.text
        assert saved.json() == {"importedCount": 1, "skippedCount": 0}
        reviewed = client.get("/api/memory/search").json()
        assert reviewed["messages"] == selected and reviewed["total"] == 1
        assert client.delete("/api/memory").json() == {"deletedCount": 1}
        assert client.get("/api/memory/search").json()["total"] == 0
        assert [request.url.path for request in requests] == ["/api/auth.test", "/api/conversations.history"]
        assert requests[-1].url.params["channel"] == CHANNEL
        assert requests[-1].url.params["limit"] == "100"
    assert ai.calls == []


def test_unchanged_import_skips_and_edited_message_conflict_is_atomic(services, ai):
    history = page([message(), message("1700000001.000001", "Not yet imported.")])
    with preview_client(services, history) as (client, requests):
        first = client.post("/api/slack/preview", json={"channelId": CHANNEL}).json()["messages"]
        assert client.post("/api/memory/import", json={"messages": first[:1]}).json()["importedCount"] == 1
        unchanged = client.post("/api/slack/preview", json={"channelId": CHANNEL}).json()["messages"]
        assert unchanged == first
        assert client.post("/api/memory/import", json={"messages": unchanged[:1]}).json() == {
            "importedCount": 0, "skippedCount": 1,
        }
        history["messages"][0]["text"] = "The edited budget message."
        edited = client.post("/api/slack/preview", json={"channelId": CHANNEL}).json()["messages"]
        assert edited[0]["id"] == first[0]["id"]
        assert_error(client.post("/api/memory/import", json={"messages": edited}), 409, "MEMORY_ID_CONFLICT")
        reviewed = client.get("/api/memory/search").json()
        assert reviewed["messages"] == first[:1] and reviewed["total"] == 1
        assert len(requests) == 6
    assert ai.calls == []


def test_preview_omits_optional_null_metadata_and_keeps_null_next_cursor(services, ai):
    record = MemoryRecord("missing-metadata", "demo", "UEMPLOYEE", "Synthetic note.", None, None)

    class StaticSlack:
        def preview(self, **kwargs):
            return SlackPreviewPage((record,), None, 0, ())

    app = create_app(services, demo_local_resolver, slack=StaticSlack())
    with TestClient(app, client=("127.0.0.1", 50000), raise_server_exceptions=False) as client:
        response = client.post("/api/slack/preview", json={"channelId": CHANNEL})
        assert response.status_code == 200, response.text
        body = response.json()
        assert body["nextCursor"] is None
        assert body["messages"] == [{
            "id": record.id, "conversationId": record.conversation_id,
            "sender": record.sender, "content": record.content,
        }]
        assert client.post("/api/memory/import", json={"messages": body["messages"]}).status_code == 200
        saved = client.get("/api/memory/search").json()["messages"][0]
        assert saved["timestamp"] is None and saved["source"] is None
    assert ai.calls == []


def test_all_skipped_page_keeps_cursor_until_user_requests_next_page(services, ai):
    history = page([
        message(subtype="channel_join"),
        message("1700000001.000001", text=""),
    ], cursor="next-page==")
    with preview_client(services, history) as (client, requests):
        response = client.post("/api/slack/preview", json={"channelId": CHANNEL, "limit": 2})
        assert response.status_code == 200, response.text
        body = response.json()
        assert body["messages"] == [] and body["skippedCount"] == 2
        assert body["nextCursor"] == "next-page==" and body["warnings"]
        assert len(requests) == 2  # No automatic crawl after the skipped page.
        assert client.get("/api/memory/search").json()["total"] == 0
        history.update(page())
        next_page = client.post("/api/slack/preview", json={
            "channelId": CHANNEL, "limit": 2, "cursor": body["nextCursor"],
        })
        assert next_page.status_code == 200, next_page.text
        assert next_page.json()["nextCursor"] is None
        assert requests[-1].url.params["cursor"] == "next-page=="
        assert len(requests) == 4
    assert ai.calls == []


def test_empty_history_is_success_and_is_not_persisted(services, ai):
    with preview_client(services) as (client, requests):
        response = client.post("/api/slack/preview", json={"channelId": CHANNEL})
        assert response.status_code == 200, response.text
        assert response.json()["messages"] == []
        assert response.json()["nextCursor"] is None
        assert response.json()["skippedCount"] == 0
        assert client.get("/api/memory/search").json()["total"] == 0
        assert len(requests) == 2
    assert ai.calls == []


def test_date_bounds_preserve_microseconds_and_compare_across_timezones(services):
    with preview_client(services) as (client, requests):
        response = client.post("/api/slack/preview", json={
            "channelId": CHANNEL,
            "oldest": "2023-11-15T08:13:20.123456000+10:00",
            "latest": "2023-11-14T22:13:21.000001Z",
            "cursor": "opaque-cursor==", "limit": 3,
        })
        assert response.status_code == 200, response.text
        params = requests[-1].url.params
        assert params["oldest"] == "1700000000.123456"
        assert params["latest"] == "1700000001.000001"
        assert params["inclusive"] == "true"
        assert params["cursor"] == "opaque-cursor==" and params["limit"] == "3"


@pytest.mark.parametrize("token", [None, "invalid-slack-token", "xapp-not-a-bot-token"])
def test_missing_or_invalid_config_does_not_prevent_backend_startup(monkeypatch, token):
    monkeypatch.setenv("R2R_SERVICES", "stub")
    monkeypatch.setenv("R2R_IDENTITY_MODE", "demo_local")
    if token is None:
        monkeypatch.delenv("SLACK_BOT_TOKEN", raising=False)
        monkeypatch.delenv("R2R_SLACK_CHANNEL_ID", raising=False)
    else:
        monkeypatch.setenv("SLACK_BOT_TOKEN", token)
        monkeypatch.setenv("R2R_SLACK_CHANNEL_ID", CHANNEL)
    monkeypatch.delitem(sys.modules, "backend.api.main", raising=False)
    main = importlib.import_module("backend.api.main")
    with TestClient(main.app, client=("127.0.0.1", 50000), raise_server_exceptions=False) as client:
        assert_error(client.post("/api/slack/preview", json={"channelId": CHANNEL}), 503, "SLACK_NOT_CONFIGURED")
        assert client.get("/api/memory/search").status_code == 200


def test_disallowed_channel_is_rejected_before_any_slack_request(services):
    with preview_client(services) as (client, requests):
        response = client.post("/api/slack/preview", json={"channelId": "COTHER123"})
        assert_error(response, 403, "SLACK_CHANNEL_NOT_ALLOWED")
        assert requests == []


@pytest.mark.parametrize("host", ["127.0.0.1", "::1"])
def test_preview_allows_direct_loopback_demo_without_login(services, host):
    with preview_client(services, host=host) as (client, requests):
        assert client.post("/api/slack/preview", json={"channelId": CHANNEL}).status_code == 200
        assert len(requests) == 2


@pytest.mark.parametrize("host, headers", [
    ("192.168.1.20", {}),
    ("203.0.113.9", {}),
    ("testclient", {}),
    ("127.0.0.1", {"X-Forwarded-For": "203.0.113.9"}),
    ("::1", {"Forwarded": "for=203.0.113.9"}),
    ("127.0.0.1", {"X-Real-IP": "203.0.113.9"}),
])
def test_preview_rejects_remote_and_proxied_clients_before_slack(services, host, headers):
    with preview_client(services, host=host) as (client, requests):
        response = client.post("/api/slack/preview", json={"channelId": CHANNEL}, headers=headers)
        assert_error(response, 401, "UNAUTHENTICATED")
        assert requests == []


@pytest.mark.parametrize("patch, field", [
    ({"channelId": None}, "channelId"),
    ({"channelId": ""}, "channelId"),
    ({"channelId": "cDEMO123"}, "channelId"),
    ({"channelId": "DDEMO123"}, "channelId"),
    ({"channelId": " CDEMO123"}, "channelId"),
    ({"channelId": "C" * 129}, "channelId"),
    ({"limit": True}, "limit"),
    ({"limit": "20"}, "limit"),
    ({"limit": 1.5}, "limit"),
    ({"limit": 0}, "limit"),
    ({"limit": 101}, "limit"),
    ({"limit": None}, "limit"),
    ({"oldest": None}, "oldest"),
    ({"latest": None}, "latest"),
    ({"cursor": None}, "cursor"),
    ({"oldest": "2023-11-14T22:13:20"}, "oldest"),
    ({"oldest": "2023-11-14T22:13:20+00:99"}, "oldest"),
    ({"oldest": "1970-01-01T00:00:00+01:00"}, "oldest"),
    ({"oldest": "2023-11-14T22:13:20.1234567Z"}, "oldest"),
    ({"latest": "9999-12-31T23:59:59-23:59"}, "latest"),
    ({"cursor": ""}, "cursor"),
    ({"cursor": " "}, "cursor"),
    ({"cursor": "next-page "}, "cursor"),
    ({"cursor": "next page"}, "cursor"),
    ({"cursor": "next\npage"}, "cursor"),
    ({"cursor": "next-\u2603-page"}, "cursor"),
    ({"cursor": "a" * 2049}, "cursor"),
    ({"token": "xoxb-client-supplied-secret"}, "token"),
    ({"userId": "someone-else"}, "userId"),
    ({"sessionId": "someone-else"}, "sessionId"),
    ({"channel_id": CHANNEL}, "channel_id"),
])
def test_preview_rejects_invalid_wire_fields_without_contacting_slack(services, patch, field):
    with preview_client(services) as (client, requests):
        response = client.post("/api/slack/preview", json={"channelId": CHANNEL, **patch})
        error = assert_error(response, 422, "VALIDATION_ERROR")
        assert field in [detail["field"] for detail in error["details"]]
        assert "xoxb-client-supplied-secret" not in response.text
        assert requests == []


def test_preview_requires_channel_and_orders_bounds_chronologically(services):
    with preview_client(services) as (client, requests):
        assert_error(client.post("/api/slack/preview", json={}), 422, "VALIDATION_ERROR")
        response = client.post("/api/slack/preview", json={
            "channelId": CHANNEL,
            "oldest": "2023-11-14T23:00:00Z",
            "latest": "2023-11-15T08:00:00+10:00",
        })
        assert_error(response, 422, "VALIDATION_ERROR")
        assert requests == []


def test_preview_rejects_query_params_before_contacting_slack(services):
    with preview_client(services) as (client, requests):
        response = client.post("/api/slack/preview?userId=someone-else", json={"channelId": CHANNEL})
        assert_error(response, 422, "VALIDATION_ERROR")
        assert requests == []


@pytest.mark.parametrize("content, headers, status, code", [
    (b'{"channelId":"CDEMO123"}', {"Content-Type": "text/plain"}, 415, "UNSUPPORTED_MEDIA_TYPE"),
    (b"{bad-json", {"Content-Type": "application/json"}, 400, "INVALID_JSON"),
    (b"[]", {"Content-Type": "application/json"}, 422, "VALIDATION_ERROR"),
    (b"a" * 1_048_577, {"Content-Type": "application/json"}, 413, "REQUEST_TOO_LARGE"),
])
def test_preview_uses_existing_http_boundary(services, content, headers, status, code):
    with preview_client(services) as (client, requests):
        assert_error(client.post("/api/slack/preview", content=content, headers=headers), status, code)
        assert requests == []


@pytest.mark.parametrize("provider_code, status, code", [
    ("invalid_auth", 502, "SLACK_AUTH_FAILED"),
    ("missing_scope", 403, "SLACK_PERMISSION_DENIED"),
    ("not_in_channel", 403, "SLACK_PERMISSION_DENIED"),
    ("channel_not_found", 404, "SLACK_CHANNEL_NOT_FOUND"),
    ("ratelimited", 429, "SLACK_RATE_LIMITED"),
    ("internal_error", 503, "SLACK_UNAVAILABLE"),
    ("unknown_provider_error", 502, "SLACK_UPSTREAM_ERROR"),
])
def test_slack_provider_errors_use_safe_api_envelopes(services, ai, caplog, provider_code, status, code):
    def handler(request):
        if request.url.path == "/api/auth.test":
            return httpx.Response(200, json={"ok": True, "team_id": TEAM})
        return httpx.Response(200, json={"ok": False, "error": provider_code, "detail": PRIVATE_PROVIDER_TEXT})

    with preview_client(services, handler=handler) as (client, requests):
        response = client.post("/api/slack/preview", json={"channelId": CHANNEL})
        assert_error(response, status, code)
        assert TOKEN not in response.text and PRIVATE_PROVIDER_TEXT not in response.text
        assert PRIVATE_PROVIDER_TEXT not in caplog.text
        assert client.get("/api/memory/search").json()["total"] == 0
        assert len(requests) == 2
        if code == "SLACK_RATE_LIMITED":
            assert response.headers["Retry-After"] == "60"
    assert ai.calls == []


@pytest.mark.parametrize("retry_after, expected", [("120", "120"), ("0", "1"), ("99999999", "3600"), ("-1", "60"), ("invalid", "60")])
def test_rate_limit_header_is_bounded_without_retries(services, retry_after, expected):
    def handler(request):
        return httpx.Response(429, headers={"Retry-After": retry_after}, text=PRIVATE_PROVIDER_TEXT)

    with preview_client(services, handler=handler) as (client, requests):
        response = client.post("/api/slack/preview", json={"channelId": CHANNEL})
        assert_error(response, 429, "SLACK_RATE_LIMITED")
        assert response.headers["Retry-After"] == expected
        assert PRIVATE_PROVIDER_TEXT not in response.text
        assert len(requests) == 1


@pytest.mark.parametrize("exception, status, code", [
    (httpx.ReadTimeout, 504, "SLACK_TIMEOUT"),
    (httpx.ConnectError, 503, "SLACK_UNAVAILABLE"),
])
def test_transport_failure_is_safe_error_without_retry(services, exception, status, code):
    def handler(request):
        raise exception(PRIVATE_PROVIDER_TEXT, request=request)

    with preview_client(services, handler=handler) as (client, requests):
        response = client.post("/api/slack/preview", json={"channelId": CHANNEL})
        assert_error(response, status, code)
        assert PRIVATE_PROVIDER_TEXT not in response.text
        assert len(requests) == 1


@pytest.mark.parametrize("payload", [
    {"ok": True, "messages": "invalid"},
    {"ok": True, "messages": [], "has_more": True},
    {"ok": True, "messages": [], "response_metadata": {"next_cursor": "unsafe cursor"}},
    {"ok": True, "messages": [], "has_more": "false"},
])
def test_unsafe_provider_pages_are_errors_not_empty_success(services, payload):
    with preview_client(services, payload) as (client, requests):
        response = client.post("/api/slack/preview", json={"channelId": CHANNEL})
        assert_error(response, 502, "SLACK_UPSTREAM_ERROR")
        assert len(requests) == 2
        assert client.get("/api/memory/search").json()["total"] == 0


def test_api_revalidates_preview_records_before_returning_any_messages(services):
    good = MemoryRecord("good", "demo", "UEMPLOYEE", "Synthetic note.", None, None)
    bad = MemoryRecord("bad", "demo", "UEMPLOYEE", " ", None, None)

    class InvalidSlack:
        def preview(self, **kwargs):
            return SlackPreviewPage((good, bad), None, 0, ())

    app = create_app(services, demo_local_resolver, slack=InvalidSlack())
    with TestClient(app, client=("127.0.0.1", 50000), raise_server_exceptions=False) as client:
        response = client.post("/api/slack/preview", json={"channelId": CHANNEL})
        assert_error(response, 502, "SLACK_UPSTREAM_ERROR")
        assert client.get("/api/memory/search").json()["total"] == 0
