"""Load optional local backend settings without searching frontend directories."""

from __future__ import annotations

from pathlib import Path

from dotenv import load_dotenv


DEFAULT_ENV_FILE = Path(__file__).resolve().parent / ".env"


def load_backend_env(path: str | Path | None = None) -> None:
    """Load backend/.env once needed by startup; process variables take priority.

    The explicit path is independent of the working directory. Values remain
    literal (no variable interpolation), and no settings or secrets are logged.
    Missing files are fine: deployments may supply all settings externally.
    """
    load_dotenv(
        dotenv_path=DEFAULT_ENV_FILE if path is None else Path(path),
        override=False,
        interpolate=False,
        encoding="utf-8-sig",
    )
