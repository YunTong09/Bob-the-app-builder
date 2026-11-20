"""SqliteMemoryService: persistence, atomicity, FTS consistency, isolation."""

from __future__ import annotations

import sqlite3

import pytest

from backend.application.errors import MemoryIdConflictError, OwnershipError, StorageUnavailableError
from backend.application.ports import MemoryRecord, OwnerContext
from backend.memory.sqlite_store import SqliteMemoryService

A = OwnerContext("owner-a", "authenticated")
B = OwnerContext("owner-b", "authenticated")


def rec(i, content="note about the budget", conv="c1", ts=None, source=None, sender="Manager"):
    return MemoryRecord(id=f"m{i:03d}", conversation_id=conv, sender=sender, content=content, timestamp=ts, source=source)


@pytest.fixture
def db(tmp_path):
    return SqliteMemoryService(tmp_path / "mem.sqlite3")


def fts_rows(db) -> int:
    conn = sqlite3.connect(db._path)
    try:
        conn.execute("INSERT INTO messages_fts(messages_fts) VALUES('integrity-check')")
        return conn.execute("SELECT COUNT(*) FROM messages_fts").fetchone()[0]
    finally:
        conn.close()


def test_persists_across_instances_with_nulls(tmp_path):
    path = tmp_path / "mem.sqlite3"
    SqliteMemoryService(path).import_messages(A, [rec(1), rec(2, ts="2026-11-18T10:30:00+10:00", source="Slack export")])
    page = SqliteMemoryService(path).search(A, query=None, conversation_id=None, limit=10, offset=0)
    assert page.records == (rec(1), rec(2, ts="2026-11-18T10:30:00+10:00", source="Slack export"))
    assert page.records[0].timestamp is None and page.records[0].source is None


def test_content_verbatim(db):
    content = "  Keep   spacing\nand 'quotes' — exactly  "
    db.import_messages(A, [rec(1, content=content)])
    assert db.search(A, query=None, conversation_id=None, limit=1, offset=0).records[0].content == content


def test_skip_identical_and_conflict_is_atomic(db):
    assert db.import_messages(A, [rec(1)]).imported_count == 1
    r = db.import_messages(A, [rec(1), rec(2)])
    assert (r.imported_count, r.skipped_count) == (1, 1)
    with pytest.raises(MemoryIdConflictError) as exc:
        db.import_messages(A, [rec(3), rec(1, source="different")])
    assert exc.value.conflicting_ids == ("m001",)
    assert db.search(A, query=None, conversation_id=None, limit=10, offset=0).total == 2  # m003 not stored
    assert fts_rows(db) == 2


def test_same_id_other_owner_no_conflict(db):
    db.import_messages(A, [rec(1, content="alpha secret plan")])
    assert db.import_messages(B, [rec(1, content="bravo")]).imported_count == 1
    assert db.search(B, query="alpha", conversation_id=None, limit=10, offset=0).total == 0
    assert db.retrieve(B, queries=["alpha secret plan"], conversation_id=None, limit=10) == ()


def test_search_and_terms_ranking_pagination(db):
    db.import_messages(
        A,
        [
            rec(1, "budget review on friday"),
            rec(2, "budget budget budget"),
            rec(3, "lunch plans", conv="c2"),
            rec(4, "budget", conv="c2"),
        ],
    )
    page = db.search(A, query="budget", conversation_id=None, limit=2, offset=0)
    assert page.total == 3 and [r.id for r in page.records] == ["m002", "m001"]  # tf, then id
    assert [r.id for r in db.search(A, query="budget", conversation_id=None, limit=2, offset=2).records] == ["m004"]
    assert db.search(A, query="BUDGET friday", conversation_id=None, limit=10, offset=0).total == 1
    assert db.search(A, query="budget", conversation_id="c2", limit=10, offset=0).total == 1
    assert db.search(A, query=None, conversation_id="c2", limit=10, offset=0).total == 2
    assert db.search(A, query="budget", conversation_id=None, limit=10, offset=50).records == ()


@pytest.mark.parametrize("q", ['" OR 1=1 --', "budget*", "NEAR(budget review)", "budget OR lunch", "-budget", "col:budget", "'; DROP TABLE messages; --", "***"])
def test_search_treats_fts_and_sql_syntax_literally(db, q):
    db.import_messages(A, [rec(1, "budget review"), rec(2, "lunch")])
    page = db.search(A, query=q, conversation_id=None, limit=10, offset=0)
    # Only literal terms are matched; operators are never interpreted.
    assert all("budget" in r.content or "lunch" in r.content for r in page.records)
    assert db.search(A, query=None, conversation_id=None, limit=10, offset=0).total == 2  # table intact
    if q == "budget OR lunch":
        assert page.total == 0  # AND of literal terms "budget", "or", "lunch"


def test_retrieve_is_owner_and_conversation_scoped(db):
    db.import_messages(A, [rec(1, "documents uploaded to the shared drive"), rec(2, "shared drive password", conv="c2")])
    db.import_messages(B, [rec(9, "documents shared drive password")])
    got = db.retrieve(A, queries=["shared drive documents"], conversation_id=None, limit=10)
    assert [r.id for r in got] == ["m001", "m002"]
    assert [r.id for r in db.retrieve(A, queries=["password"], conversation_id="c1", limit=10)] == []
    assert db.retrieve(A, queries=["the and of"], conversation_id=None, limit=10) == ()


def test_delete_removes_rows_and_index_for_owner_only(db):
    db.import_messages(A, [rec(1, "budget"), rec(2, "budget")])
    db.import_messages(B, [rec(1, "budget")])
    assert db.delete_all(A) == 2
    assert db.delete_all(A) == 0
    assert db.search(A, query="budget", conversation_id=None, limit=10, offset=0).total == 0
    assert db.search(B, query="budget", conversation_id=None, limit=10, offset=0).total == 1
    assert fts_rows(db) == 1


def test_invalid_owner_never_searches_globally(db):
    db.import_messages(A, [rec(1)])
    for call in (
        lambda o: db.search(o, query=None, conversation_id=None, limit=10, offset=0),
        lambda o: db.retrieve(o, queries=["budget"], conversation_id=None, limit=10),
        lambda o: db.delete_all(o),
        lambda o: db.import_messages(o, [rec(5)]),
    ):
        with pytest.raises(OwnershipError):
            call(None)


def test_storage_failure_maps_to_unavailable(tmp_path):
    db = SqliteMemoryService(tmp_path / "mem.sqlite3")
    conn = sqlite3.connect(db._path)
    conn.execute("DROP TABLE messages")
    conn.commit()
    conn.close()
    with pytest.raises(StorageUnavailableError):
        db.search(A, query=None, conversation_id=None, limit=10, offset=0)
    with pytest.raises(StorageUnavailableError):
        db.retrieve(A, queries=["budget"], conversation_id=None, limit=5)
