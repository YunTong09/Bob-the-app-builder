"""Zero-arg factory so the API test-suite can run against the real SQLite store:

    R2R_TEST_MEMORY_FACTORY=backend.tests.sqlite_factory:make python -m pytest backend
"""

from __future__ import annotations

import tempfile
from pathlib import Path

from backend.memory.sqlite_store import SqliteMemoryService


def make() -> SqliteMemoryService:
    return SqliteMemoryService(Path(tempfile.mkdtemp(prefix="r2r-test-")) / "memory.sqlite3")
