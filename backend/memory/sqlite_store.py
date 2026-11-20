"""SQLite + FTS5 implementation of ``MemoryService`` (Developer 3).

Design notes
* Only explicitly imported messages are stored: owner, id, conversation,
  sender, content (verbatim), timestamp and source (NULL when unknown).
* ``messages_fts`` is an external-content FTS5 index kept in sync by triggers,
  so every insert/delete of a message updates the index in the same
  transaction.
* Every read query filters by ``owner_id`` (and optional conversation) inside
  SQL. Ranking is then computed over that owner-scoped result only -- FTS5's
  bm25() is not used because its statistics span all owners' rows, which would
  let other users' data influence ordering.
* User search text is never passed to FTS5 as syntax: it is split into
  alphanumeric terms and each term is double-quoted.
* Any sqlite error becomes ``StorageUnavailableError``; an invalid owner raises
  ``OwnershipError``. There is no unscoped code path.
"""

from __future__ import annotations

import re
import sqlite3
import threading
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator, Sequence

from backend.application.errors import MemoryIdConflictError, OwnershipError, StorageUnavailableError
from backend.application.ports import ImportResult, MemoryRecord, OwnerContext, SearchPage

_TERM = re.compile(r"[^\W_]+", re.UNICODE)
MAX_SEARCH_TERMS = 32
MAX_RETRIEVAL_TERMS = 64

# Common words ignored for evidence retrieval only (not for explicit search).
_STOPWORDS = frozenset(
    """a an and are as at be been but by can can't could did do does don't for from had has
    have haven't he her him his how i i'm i've if in into is it it's its just me my no not of
    on or our please she so still than that the their them then there they this to too up us
    was we were what when where which who why will with would yet you your""".split()
)

_SCHEMA = """
CREATE TABLE IF NOT EXISTS messages (
    pk              INTEGER PRIMARY KEY,
    owner_id        TEXT NOT NULL,
    id              TEXT NOT NULL,
    conversation_id TEXT NOT NULL,
    sender          TEXT NOT NULL,
    content         TEXT NOT NULL,
    timestamp       TEXT,
    source          TEXT,
    UNIQUE (owner_id, id)
);
CREATE INDEX IF NOT EXISTS messages_owner_conv ON messages (owner_id, conversation_id, id);
CREATE VIRTUAL TABLE IF NOT EXISTS messages_fts USING fts5(
    content,
    content='messages',
    content_rowid='pk',
    tokenize='unicode61 remove_diacritics 2'
);
CREATE TRIGGER IF NOT EXISTS messages_ai AFTER INSERT ON messages BEGIN
    INSERT INTO messages_fts(rowid, content) VALUES (new.pk, new.content);
END;
CREATE TRIGGER IF NOT EXISTS messages_ad AFTER DELETE ON messages BEGIN
    INSERT INTO messages_fts(messages_fts, rowid, content) VALUES ('delete', old.pk, old.content);
END;
CREATE TRIGGER IF NOT EXISTS messages_au AFTER UPDATE ON messages BEGIN
    INSERT INTO messages_fts(messages_fts, rowid, content) VALUES ('delete', old.pk, old.content);
    INSERT INTO messages_fts(rowid, content) VALUES (new.pk, new.content);
END;
"""

_COLUMNS = "m.id, m.conversation_id, m.sender, m.content, m.timestamp, m.source"


def search_terms(text: str) -> list[str]:
    """Literal, deduplicated, lower-cased search terms (no FTS syntax)."""
    seen: dict[str, None] = {}
    for t in _TERM.findall(text):
        seen.setdefault(t.casefold(), None)
    return list(seen)


def _fts_literal(term: str) -> str:
    return '"' + term.replace('"', '""') + '"'


def _owner_id(owner: OwnerContext) -> str:
    if not isinstance(owner, OwnerContext) or not owner.owner_id:
        raise OwnershipError("owner context missing")
    return owner.owner_id


def _row(r: sqlite3.Row) -> MemoryRecord:
    return MemoryRecord(
        id=r["id"],
        conversation_id=r["conversation_id"],
        sender=r["sender"],
        content=r["content"],
        timestamp=r["timestamp"],
        source=r["source"],
    )


def _tf(content: str, terms: Sequence[str]) -> tuple[int, int]:
    """(distinct terms matched, total occurrences) over the record's own text."""
    words = [w.casefold() for w in _TERM.findall(content)]
    counts = [words.count(t) for t in terms]
    return sum(1 for c in counts if c), sum(counts)


class SqliteMemoryService:
    def __init__(self, db_path: str | Path) -> None:
        self._path = str(db_path)
        if self._path != ":memory:":
            Path(self._path).parent.mkdir(parents=True, exist_ok=True)
        self._write_lock = threading.Lock()
        with self._connect() as conn:
            conn.execute("PRAGMA journal_mode=WAL")
            conn.executescript(_SCHEMA)

    # ------------------------------------------------------------ plumbing
    @contextmanager
    def _connect(self) -> Iterator[sqlite3.Connection]:
        try:
            conn = sqlite3.connect(self._path, timeout=5.0, isolation_level=None)
        except sqlite3.Error as exc:
            raise StorageUnavailableError("cannot open database") from exc
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        except sqlite3.Error as exc:
            raise StorageUnavailableError(type(exc).__name__) from exc
        finally:
            conn.close()

    # ------------------------------------------------------------ import
    def import_messages(self, owner: OwnerContext, records: Sequence[MemoryRecord]) -> ImportResult:
        owner_id = _owner_id(owner)
        with self._write_lock, self._connect() as conn:
            conn.execute("BEGIN IMMEDIATE")
            try:
                new: list[MemoryRecord] = []
                conflicts: list[str] = []
                for rec in records:
                    row = conn.execute(
                        f"SELECT {_COLUMNS} FROM messages m WHERE m.owner_id = ? AND m.id = ?",
                        (owner_id, rec.id),
                    ).fetchone()
                    if row is None:
                        new.append(rec)
                    elif _row(row) != rec:
                        conflicts.append(rec.id)
                if conflicts:
                    raise MemoryIdConflictError(tuple(conflicts))
                conn.executemany(
                    "INSERT INTO messages (owner_id, id, conversation_id, sender, content, timestamp, source) "
                    "VALUES (?, ?, ?, ?, ?, ?, ?)",
                    [(owner_id, r.id, r.conversation_id, r.sender, r.content, r.timestamp, r.source) for r in new],
                )
                conn.execute("COMMIT")
            except BaseException:
                conn.execute("ROLLBACK")
                raise
        return ImportResult(imported_count=len(new), skipped_count=len(records) - len(new))

    # ------------------------------------------------------------ search
    def search(
        self,
        owner: OwnerContext,
        *,
        query: str | None,
        conversation_id: str | None,
        limit: int,
        offset: int,
    ) -> SearchPage:
        owner_id = _owner_id(owner)
        conv_sql = " AND m.conversation_id = ?" if conversation_id is not None else ""
        conv_args: tuple = (conversation_id,) if conversation_id is not None else ()

        with self._connect() as conn:
            if query is None:
                total = conn.execute(
                    f"SELECT COUNT(*) FROM messages m WHERE m.owner_id = ?{conv_sql}",
                    (owner_id, *conv_args),
                ).fetchone()[0]
                rows = conn.execute(
                    f"SELECT {_COLUMNS} FROM messages m WHERE m.owner_id = ?{conv_sql} "
                    "ORDER BY m.id LIMIT ? OFFSET ?",
                    (owner_id, *conv_args, limit, offset),
                ).fetchall()
                return SearchPage(records=tuple(_row(r) for r in rows), total=total)

            terms = search_terms(query)[:MAX_SEARCH_TERMS]
            if not terms:
                return SearchPage(records=(), total=0)
            match = " AND ".join(_fts_literal(t) for t in terms)
            rows = conn.execute(
                f"SELECT {_COLUMNS} FROM messages_fts JOIN messages m ON m.pk = messages_fts.rowid "
                f"WHERE messages_fts MATCH ? AND m.owner_id = ?{conv_sql}",
                (match, owner_id, *conv_args),
            ).fetchall()

        ranked = sorted((_row(r) for r in rows), key=lambda rec: (-_tf(rec.content, terms)[1], rec.id))
        return SearchPage(records=tuple(ranked[offset : offset + limit]), total=len(ranked))

    # ------------------------------------------------------------ retrieval
    def retrieve(
        self,
        owner: OwnerContext,
        *,
        queries: Sequence[str],
        conversation_id: str | None,
        limit: int,
    ) -> tuple[MemoryRecord, ...]:
        owner_id = _owner_id(owner)
        terms: list[str] = []
        for q in queries:
            for t in search_terms(q):
                if t not in _STOPWORDS and len(t) > 1 and t not in terms:
                    terms.append(t)
        terms = terms[:MAX_RETRIEVAL_TERMS]
        if not terms or limit <= 0:
            return ()
        conv_sql = " AND m.conversation_id = ?" if conversation_id is not None else ""
        conv_args: tuple = (conversation_id,) if conversation_id is not None else ()
        match = " OR ".join(_fts_literal(t) for t in terms)
        with self._connect() as conn:
            rows = conn.execute(
                f"SELECT {_COLUMNS} FROM messages_fts JOIN messages m ON m.pk = messages_fts.rowid "
                f"WHERE messages_fts MATCH ? AND m.owner_id = ?{conv_sql}",
                (match, owner_id, *conv_args),
            ).fetchall()
        records = [_row(r) for r in rows]

        def score(rec: MemoryRecord) -> tuple:
            distinct, total = _tf(rec.content, terms)
            return (-distinct, -total, rec.id)

        return tuple(sorted(records, key=score)[:limit])

    # ------------------------------------------------------------ deletion
    def delete_all(self, owner: OwnerContext) -> int:
        owner_id = _owner_id(owner)
        with self._write_lock, self._connect() as conn:
            conn.execute("BEGIN IMMEDIATE")
            try:
                cur = conn.execute("DELETE FROM messages WHERE owner_id = ?", (owner_id,))
                conn.execute("COMMIT")
            except BaseException:
                conn.execute("ROLLBACK")
                raise
        return cur.rowcount
