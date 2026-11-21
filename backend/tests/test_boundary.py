"""HTTP boundary: validation, size limits, content types, error envelope."""

from __future__ import annotations

import pytest

from .conftest import GEN_BODY, load_fixture


def assert_error(r, status: int, code: str) -> dict:
    assert r.status_code == status, r.text
    body = r.json()
    assert set(body) == {"error"}
    assert body["error"]["code"] == code
    assert isinstance(body["error"]["message"], str) and body["error"]["message"]
    return body["error"]


# ------------------------------------------------------------------ generation validation


@pytest.mark.parametrize(
    "patch, field",
    [
        ({"employeeDraft": "   \n\t"}, "employeeDraft"),
        ({"managerMessage": None}, "managerMessage"),
        ({"managerMessage": 123}, "managerMessage"),
        ({"managerMessage": False}, "managerMessage"),
        ({"managerMessage": []}, "managerMessage"),
        ({"managerMessage": "x" * 10_001}, "managerMessage"),
        ({"managerMessage": " " * 10_001}, "managerMessage"),
        ({"tone": "angry"}, "tone"),
        ({"tone": 1}, "tone"),
        ({"employeeDraft": 123}, "employeeDraft"),
        ({"employeeDraft": "x" * 10_001}, "employeeDraft"),
        ({"conversationId": " conv"}, "conversationId"),
        ({"conversationId": "c" * 129}, "conversationId"),
        ({"conversationId": None}, "conversationId"),
        ({"userId": "someone-else"}, "userId"),
        ({"sessionId": "abc"}, "sessionId"),
        ({"manager_message": "snake case is not the wire name"}, "manager_message"),
    ],
)
def test_generate_rejects_invalid_fields(client, ai, patch, field):
    r = client.post("/api/reply/generate", json={**GEN_BODY, **patch})
    err = assert_error(r, 422, "VALIDATION_ERROR")
    assert field in [d["field"] for d in err["details"]]
    assert ai.calls == []  # Claude is never called for invalid input


@pytest.mark.parametrize("field", ["employeeDraft", "tone"])
def test_generate_missing_required_field(client, ai, field):
    body = {k: v for k, v in GEN_BODY.items() if k != field}
    err = assert_error(client.post("/api/reply/generate", json=body), 422, "VALIDATION_ERROR")
    assert err["details"] == [{"field": field, "message": "Field required."}]
    assert ai.calls == []


def test_whitespace_error_matches_contract_example(client):
    r = client.post("/api/reply/generate", json={**GEN_BODY, "employeeDraft": "   "})
    assert r.json() == load_fixture("error_validation.json")


def test_validation_errors_never_echo_draft(client):
    r = client.post("/api/reply/generate", json={**GEN_BODY, "tone": "SECRET-DRAFT-TEXT", "employeeDraft": "SECRET-DRAFT-TEXT" * 700})
    assert r.status_code == 422
    assert "SECRET-DRAFT-TEXT" not in r.text


@pytest.mark.parametrize("field", ["employeeDraft", "managerMessage"])
def test_max_length_text_is_accepted(client, field):
    r = client.post("/api/reply/generate", json={**GEN_BODY, field: "x" * 10_000})
    assert r.status_code == 200, r.text


def test_body_must_be_object(client):
    assert_error(client.post("/api/reply/generate", json=[GEN_BODY]), 422, "VALIDATION_ERROR")


@pytest.mark.parametrize("raw", [b"{not json", b"", b'{"tone": NaN}', b"\xff\xfe"])
def test_invalid_json(client, raw):
    r = client.post("/api/reply/generate", content=raw, headers={"Content-Type": "application/json"})
    assert_error(r, 400, "INVALID_JSON")


@pytest.mark.parametrize("ctype", [None, "text/plain", "multipart/form-data; boundary=x", "application/json; charset=latin-1"])
def test_unsupported_media_type(client, ai, ctype):
    import json

    headers = {"Content-Type": ctype} if ctype else {}
    r = client.post("/api/reply/generate", content=json.dumps(GEN_BODY).encode(), headers=headers)
    assert_error(r, 415, "UNSUPPORTED_MEDIA_TYPE")
    assert ai.calls == []


def test_json_with_utf8_charset_accepted(client):
    import json

    r = client.post("/api/reply/generate", content=json.dumps(GEN_BODY).encode(), headers={"Content-Type": "application/json; charset=UTF-8"})
    assert r.status_code == 200


# ------------------------------------------------------------------ size limits


def test_oversized_body_with_content_length(client, ai):
    body = b'{"x":"' + b"a" * 1_048_576 + b'"}'
    r = client.post("/api/memory/import", content=body, headers={"Content-Type": "application/json"})
    assert_error(r, 413, "REQUEST_TOO_LARGE")
    assert ai.calls == []


def test_oversized_chunked_body_without_content_length(client, ai):
    def chunks():
        for _ in range(17):
            yield b"a" * 65_536  # 1,114,112 bytes

    r = client.post("/api/reply/generate", content=chunks(), headers={"Content-Type": "application/json"})
    assert_error(r, 413, "REQUEST_TOO_LARGE")
    assert ai.calls == []


def test_body_exactly_at_limit_is_not_413(client):
    import json

    filler = 1_048_576 - len(json.dumps({**GEN_BODY, "pad": ""}).encode())
    raw = json.dumps({**GEN_BODY, "pad": "a" * filler}).encode()
    assert len(raw) == 1_048_576
    r = client.post("/api/reply/generate", content=raw, headers={"Content-Type": "application/json"})
    assert_error(r, 422, "VALIDATION_ERROR")  # unknown "pad" field, but not 413


# ------------------------------------------------------------------ framework errors


def test_unknown_route_404_envelope(client):
    assert_error(client.get("/api/nope"), 404, "NOT_FOUND")


def test_wrong_method_405_envelope(client):
    r = client.get("/api/reply/generate")
    assert_error(r, 405, "METHOD_NOT_ALLOWED")
    assert "POST" in r.headers.get("allow", "")


@pytest.mark.parametrize("method", ["GET", "PUT"])
def test_preferences_not_implemented(client, method):
    assert_error(client.request(method, "/api/preferences", json={}), 501, "NOT_IMPLEMENTED")


def test_unknown_query_param_on_generate(client):
    assert_error(client.post("/api/reply/generate?userId=x", json=GEN_BODY), 422, "VALIDATION_ERROR")


def test_very_long_limit_is_validation_error(client):
    r = client.get("/api/memory/search", params={"limit": "9" * 5_000})
    err = assert_error(r, 422, "VALIDATION_ERROR")
    assert err["details"][0]["field"] == "limit"


def test_leading_zeroes_do_not_make_small_pagination_values_invalid(client):
    r = client.get("/api/memory/search", params={"limit": "0" * 5_000 + "20", "offset": "0" * 5_000})
    assert r.status_code == 200, r.text
    assert r.json() == {"messages": [], "total": 0, "limit": 20, "offset": 0}


def test_unexpected_exception_is_500_envelope(client, ai):
    ai.analysis = RuntimeError("provider said: SECRET-DRAFT-TEXT sk-ant-123")
    r = client.post("/api/reply/generate", json=GEN_BODY)
    assert_error(r, 500, "INTERNAL_ERROR")
    assert "SECRET" not in r.text and "sk-ant" not in r.text
