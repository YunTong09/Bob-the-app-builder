"""Memory import, search/review, deletion and owner isolation via the API."""

from __future__ import annotations

import copy

import pytest

from backend.application.errors import StorageUnavailableError
from backend.application.ports import EvidenceLink, ValidatedReply

from .conftest import GEN_BODY, OWNER_HEADER, import_fixture, load_fixture
from .test_boundary import assert_error


def msg(i: int, **over) -> dict:
    m = {"id": f"m{i:03d}", "conversationId": "c1", "sender": "Manager", "content": f"note {i} about budget"}
    m.update(over)
    return m


def search(client, owner="owner-a", **params):
    r = client.get("/api/memory/search", params=params, headers={OWNER_HEADER: owner})
    assert r.status_code == 200, r.text
    return r.json()


# ------------------------------------------------------------------ import


def test_import_and_review_preserves_metadata_and_nulls(client):
    r = client.post("/api/memory/import", json=load_fixture("import_request.json"))
    assert r.json() == {"importedCount": 2, "skippedCount": 0}
    body = search(client)
    assert body == {
        "messages": [
            {
                "id": "msg_001",
                "conversationId": "conv_demo",
                "sender": "Manager",
                "content": "I've uploaded the documents to the shared drive.",
                "timestamp": "2026-11-18T10:30:00+10:00",
                "source": "Synthetic demo conversation",
            },
            {
                "id": "msg_002",
                "conversationId": "conv_demo",
                "sender": "Employee",
                "content": "Thanks, I'll take a look at the shared drive documents this afternoon.",
                "timestamp": None,
                "source": None,
            },
        ],
        "total": 2,
        "limit": 20,
        "offset": 0,
    }


def test_content_is_stored_verbatim(client):
    content = "  leading and trailing whitespace kept \n"
    client.post("/api/memory/import", json={"messages": [msg(1, content=content)]})
    assert search(client)["messages"][0]["content"] == content


def test_identical_reimport_is_skipped(client):
    import_fixture(client)
    r = client.post("/api/memory/import", json=load_fixture("import_request.json"))
    assert r.json() == {"importedCount": 0, "skippedCount": 2}


def test_conflicting_id_is_409_and_atomic(client):
    import_fixture(client)
    req = load_fixture("import_request.json")
    req["messages"][0]["content"] = "Different content"
    req["messages"].append(msg(50))
    assert_error(client.post("/api/memory/import", json=req), 409, "MEMORY_ID_CONFLICT")
    body = search(client)
    assert body["total"] == 2  # m050 was not imported
    assert body["messages"][0]["content"] == "I've uploaded the documents to the shared drive."


@pytest.mark.parametrize("field, value", [("timestamp", "2026-11-18T10:30:00+10:00"), ("source", "Other source")])
def test_metadata_difference_is_conflict(client, field, value):
    client.post("/api/memory/import", json={"messages": [msg(1)]})
    assert_error(client.post("/api/memory/import", json={"messages": [msg(1, **{field: value})]}), 409, "MEMORY_ID_CONFLICT")


def test_duplicate_ids_within_request_is_422(client):
    r = client.post("/api/memory/import", json={"messages": [msg(1), msg(1, content="other")]})
    err = assert_error(r, 422, "VALIDATION_ERROR")
    assert err["details"] == [{"field": "messages[1].id", "message": "Duplicate ID in this request."}]
    assert search(client)["total"] == 0


@pytest.mark.parametrize(
    "bad, field",
    [
        ({"timestamp": None}, "messages[0].timestamp"),
        ({"source": None}, "messages[0].source"),
        ({"timestamp": "2026-11-18T10:30:00"}, "messages[0].timestamp"),  # no timezone
        ({"timestamp": "2026-11-18"}, "messages[0].timestamp"),
        ({"timestamp": "2026-13-40T10:30:00Z"}, "messages[0].timestamp"),
        ({"content": " "}, "messages[0].content"),
        ({"sender": "s" * 201}, "messages[0].sender"),
        ({"source": ""}, "messages[0].source"),
        ({"id": "m1 "}, "messages[0].id"),
        ({"id": ""}, "messages[0].id"),
        ({"userId": "x"}, "messages[0].userId"),
    ],
)
def test_import_field_validation(client, bad, field):
    err = assert_error(client.post("/api/memory/import", json={"messages": [msg(1, **bad)]}), 422, "VALIDATION_ERROR")
    assert field in [d["field"] for d in err["details"]]


def test_missing_sender_is_rejected_not_invented(client):
    m = msg(1)
    del m["sender"]
    err = assert_error(client.post("/api/memory/import", json={"messages": [m]}), 422, "VALIDATION_ERROR")
    assert err["details"] == [{"field": "messages[0].sender", "message": "Field required."}]


@pytest.mark.parametrize("n", [0, 101])
def test_import_message_count_bounds(client, n):
    assert_error(client.post("/api/memory/import", json={"messages": [msg(i) for i in range(n)]}), 422, "VALIDATION_ERROR")


def test_import_100_messages(client):
    r = client.post("/api/memory/import", json={"messages": [msg(i) for i in range(100)]})
    assert r.json() == {"importedCount": 100, "skippedCount": 0}


@pytest.mark.parametrize("ts", [
    "2026-11-18T00:30:00.123Z",
    "2026-11-18t00:30:00z",
    "2026-11-18T10:30:00+10:00",
    "2026-11-18T10:30:00-03:30",
    "2026-11-18T23:59:59+23:59",
    "2024-02-29T12:00:00+00:00",
])
def test_timestamp_kept_verbatim(client, ts):
    r = client.post("/api/memory/import", json={"messages": [msg(1, timestamp=ts)]})
    assert r.status_code == 200, r.text
    assert search(client)["messages"][0]["timestamp"] == ts


@pytest.mark.parametrize("ts", [
    "2026-11-18T12:00:00+00:99",
    "2026-11-18T12:00:00-00:60",
    "2026-11-18T12:00:00+01:99",
    "2026-11-18T12:00:00+24:00",
    "2026-11-18T24:00:00Z",
    "2026-11-18T12:60:00Z",
    "2026-11-18T12:00:61Z",
    "2026-02-29T12:00:00Z",
])
def test_invalid_timestamp_components_reject_entire_import(client, ts):
    r = client.post("/api/memory/import", json={"messages": [msg(1), msg(2, timestamp=ts)]})
    err = assert_error(r, 422, "VALIDATION_ERROR")
    assert err["details"][0]["field"] == "messages[1].timestamp"
    assert search(client)["total"] == 0


# ------------------------------------------------------------------ search


def test_pagination_and_total(client):
    client.post("/api/memory/import", json={"messages": [msg(i) for i in range(25)]})
    p1 = search(client, limit=10, offset=0)
    p3 = search(client, limit=10, offset=20)
    past = search(client, limit=10, offset=500)
    assert [m["id"] for m in p1["messages"]] == [f"m{i:03d}" for i in range(10)]
    assert len(p3["messages"]) == 5 and p3["total"] == 25
    assert past == {"messages": [], "total": 25, "limit": 10, "offset": 500}


@pytest.mark.parametrize("offset", [2**63, 10**100])
@pytest.mark.parametrize("query", [None, "budget"])
def test_large_offsets_return_empty_page_with_correct_total(client, offset, query):
    client.post("/api/memory/import", json={"messages": [msg(1), msg(2)]})
    params = {"offset": str(offset)}
    if query is not None:
        params["q"] = query
    assert search(client, **params) == {"messages": [], "total": 2, "limit": 20, "offset": offset}


def test_query_and_conversation_filters(client):
    client.post(
        "/api/memory/import",
        json={"messages": [msg(1, content="budget review friday"), msg(2, content="budget", conversationId="c2"), msg(3, content="lunch")]},
    )
    assert [m["id"] for m in search(client, q="budget")["messages"]] == ["m001", "m002"]
    assert [m["id"] for m in search(client, q="budget friday")["messages"]] == ["m001"]  # AND
    assert search(client, q="budget", conversationId="c2")["total"] == 1
    assert search(client, q="nothing-matches")["total"] == 0
    assert search(client, q="   ")["total"] == 3  # whitespace lists history
    assert search(client, q="' OR 1=1 --")["total"] == 0  # literal, not SQL
    assert search(client, q="*")["total"] == 0  # no searchable terms


@pytest.mark.parametrize(
    "params",
    [
        {"limit": "0"},
        {"limit": "101"},
        {"limit": "abc"},
        {"limit": "1.5"},
        {"offset": "-1"},
        {"q": "x" * 501},
        {"conversationId": ""},
        {"conversationId": " c1"},
        {"userId": "owner-b"},
    ],
)
def test_search_param_validation(client, params):
    r = client.get("/api/memory/search", params=params)
    assert_error(r, 422, "VALIDATION_ERROR")


def test_repeated_query_param_rejected(client):
    assert_error(client.get("/api/memory/search?limit=1&limit=2"), 422, "VALIDATION_ERROR")


# ------------------------------------------------------------------ isolation


def test_owner_isolation_across_operations(client, ai):
    import_fixture(client, owner="owner-a")
    # Same ID under another owner neither conflicts nor grants access.
    other = copy.deepcopy(load_fixture("import_request.json"))
    other["messages"][0]["content"] = "owner-b private text"
    r = client.post("/api/memory/import", json=other, headers={OWNER_HEADER: "owner-b"})
    assert r.json() == {"importedCount": 2, "skippedCount": 0}

    assert "owner-b private" not in str(search(client, owner="owner-a"))
    assert search(client, owner="owner-c")["total"] == 0
    assert search(client, owner="owner-c", conversationId="conv_demo")["total"] == 0

    client.post("/api/reply/generate", json=GEN_BODY, headers={OWNER_HEADER: "owner-c"})
    assess_records = next(c[1][1] for c in ai.calls if c[0] == "assess")
    assert assess_records == ()


# ------------------------------------------------------------------ deletion


def test_delete_removes_only_own_history_everywhere(client, ai):
    import_fixture(client, owner="owner-a")
    import_fixture(client, owner="owner-b")
    r = client.delete("/api/memory")
    assert r.json() == {"deletedCount": 2}
    assert search(client)["total"] == 0
    assert search(client, q="documents")["total"] == 0  # search index entries gone
    assert search(client, owner="owner-b")["total"] == 2

    ai.validated = ValidatedReply(reply="r", evidence=(EvidenceLink("msg_001", "x"),), unverified_claims=())
    assert_error(client.post("/api/reply/generate", json=GEN_BODY), 502, "MODEL_ERROR")  # deleted record can't be cited
    assert next(c[1][1] for c in ai.calls if c[0] == "assess") == ()


def test_delete_when_empty(client):
    assert client.delete("/api/memory").json() == {"deletedCount": 0}


def test_delete_rejects_body_and_query(client):
    assert_error(client.request("DELETE", "/api/memory", content=b"{}", headers={"Content-Type": "application/json"}), 422, "VALIDATION_ERROR")
    assert_error(client.delete("/api/memory?conversationId=c1"), 422, "VALIDATION_ERROR")


# ------------------------------------------------------------------ storage failures


@pytest.mark.parametrize(
    "method, attr, call",
    [
        ("import", "import_messages", lambda c: c.post("/api/memory/import", json={"messages": [msg(1)]})),
        ("search", "search", lambda c: c.get("/api/memory/search")),
        ("delete", "delete_all", lambda c: c.delete("/api/memory")),
    ],
)
def test_storage_unavailable_is_503(client, memory, monkeypatch, method, attr, call):
    def boom(*a, **k):
        raise StorageUnavailableError("down")

    monkeypatch.setattr(memory, attr, boom)
    assert_error(call(client), 503, "SERVICE_UNAVAILABLE")
