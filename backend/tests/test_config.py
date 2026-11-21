"""Backend dotenv configuration, isolated from the developer's local files."""

from __future__ import annotations

import importlib
import os
import sys

import pytest
from fastapi.testclient import TestClient

from backend import config

from .conftest import GEN_BODY

TEST_KEYS = (
    "R2R_CONFIG_TEST_VALUE",
    "R2R_CONFIG_TEST_NEW",
    "R2R_CONFIG_TEST_PARENT_ONLY",
    "R2R_CONFIG_TEST_CWD_ONLY",
    "R2R_CONFIG_TEST_LITERAL",
    "R2R_CONFIG_TEST_QUOTED",
)


@pytest.fixture(autouse=True)
def isolated_test_values(monkeypatch):
    for key in (*TEST_KEYS, "PYTHON_DOTENV_DISABLED"):
        # Register absence as well as existing values so direct dotenv writes
        # are undone after the test, even when the key did not exist before.
        monkeypatch.setenv(key, "")
        monkeypatch.delenv(key, raising=False)


@pytest.mark.parametrize("as_string", [False, True])
def test_explicit_env_path_loads_values_without_modifying_or_logging_file(tmp_path, capsys, caplog, as_string):
    path = tmp_path / "synthetic.env"
    contents = "# Synthetic configuration only\nR2R_CONFIG_TEST_VALUE=synthetic-not-a-real-secret\n"
    path.write_text(contents, encoding="utf-8")
    before = path.read_bytes()

    assert config.load_backend_env(str(path) if as_string else path) is None

    assert os.environ["R2R_CONFIG_TEST_VALUE"] == "synthetic-not-a-real-secret"
    assert path.read_bytes() == before
    captured = capsys.readouterr()
    assert captured.out == "" and captured.err == ""
    assert caplog.text == ""


@pytest.mark.parametrize("existing", ["runtime-value", ""])
def test_existing_environment_including_empty_value_takes_precedence(tmp_path, monkeypatch, existing):
    path = tmp_path / "backend.env"
    path.write_text("R2R_CONFIG_TEST_VALUE=file-value\nR2R_CONFIG_TEST_NEW=new-file-value\n", encoding="utf-8")
    monkeypatch.setenv("R2R_CONFIG_TEST_VALUE", existing)

    config.load_backend_env(path)

    assert os.environ["R2R_CONFIG_TEST_VALUE"] == existing
    assert os.environ["R2R_CONFIG_TEST_NEW"] == "new-file-value"


def test_absolute_default_path_is_independent_of_working_directory(tmp_path, monkeypatch):
    backend = tmp_path / "project" / "backend"
    backend.mkdir(parents=True)
    default = backend / ".env"
    default.write_text("R2R_CONFIG_TEST_VALUE=backend-file\n", encoding="utf-8")
    elsewhere = tmp_path / "elsewhere"
    elsewhere.mkdir()
    (elsewhere / ".env").write_text("R2R_CONFIG_TEST_CWD_ONLY=wrong-cwd-file\n", encoding="utf-8")
    monkeypatch.setattr(config, "DEFAULT_ENV_FILE", default)
    monkeypatch.chdir(elsewhere)

    config.load_backend_env()

    assert os.environ["R2R_CONFIG_TEST_VALUE"] == "backend-file"
    assert "R2R_CONFIG_TEST_CWD_ONLY" not in os.environ


def test_missing_default_does_not_search_parent_env_files(tmp_path, monkeypatch):
    backend = tmp_path / "project" / "backend"
    backend.mkdir(parents=True)
    (backend.parent / ".env").write_text("R2R_CONFIG_TEST_PARENT_ONLY=wrong-parent-file\n", encoding="utf-8")
    monkeypatch.setattr(config, "DEFAULT_ENV_FILE", backend / ".env")
    monkeypatch.chdir(backend)

    assert config.load_backend_env() is None

    assert "R2R_CONFIG_TEST_PARENT_ONLY" not in os.environ


def test_missing_explicit_file_is_harmless(tmp_path, capsys, caplog):
    assert config.load_backend_env(tmp_path / "does-not-exist.env") is None
    assert "R2R_CONFIG_TEST_VALUE" not in os.environ
    captured = capsys.readouterr()
    assert captured.out == "" and captured.err == "" and caplog.text == ""


def test_windows_utf8_bom_and_crlf_are_supported(tmp_path):
    path = tmp_path / "windows.env"
    path.write_bytes("R2R_CONFIG_TEST_VALUE=caf\u00e9\r\nR2R_CONFIG_TEST_NEW=second-value\r\n".encode("utf-8-sig"))

    config.load_backend_env(path)

    assert os.environ["R2R_CONFIG_TEST_VALUE"] == "caf\u00e9"
    assert os.environ["R2R_CONFIG_TEST_NEW"] == "second-value"
    assert "\ufeffR2R_CONFIG_TEST_VALUE" not in os.environ


def test_dollar_references_remain_literal(tmp_path, monkeypatch):
    path = tmp_path / "literal.env"
    path.write_text(
        "R2R_CONFIG_TEST_VALUE=file-value\n"
        "R2R_CONFIG_TEST_LITERAL=${R2R_CONFIG_TEST_VALUE}\n"
        'R2R_CONFIG_TEST_QUOTED="${R2R_CONFIG_TEST_VALUE}/suffix"\n',
        encoding="utf-8",
    )
    monkeypatch.setenv("R2R_CONFIG_TEST_VALUE", "runtime-value")

    config.load_backend_env(path)

    assert os.environ["R2R_CONFIG_TEST_VALUE"] == "runtime-value"
    assert os.environ["R2R_CONFIG_TEST_LITERAL"] == "${R2R_CONFIG_TEST_VALUE}"
    assert os.environ["R2R_CONFIG_TEST_QUOTED"] == "${R2R_CONFIG_TEST_VALUE}/suffix"


def clear_runtime_config(monkeypatch):
    for key in (
        "R2R_SERVICES", "R2R_AI_MODE", "R2R_DB_PATH", "R2R_IDENTITY_MODE", "R2R_WEB_ORIGIN",
        "ANTHROPIC_MODEL", "SLACK_BOT_TOKEN", "R2R_SLACK_CHANNEL_ID",
    ):
        monkeypatch.setenv(key, "")
        monkeypatch.delenv(key, raising=False)


def fresh_main(monkeypatch):
    monkeypatch.delitem(sys.modules, "backend.api.main", raising=False)
    return importlib.import_module("backend.api.main")


def test_build_app_loads_backend_file_before_factories_and_web_origin(tmp_path, monkeypatch):
    clear_runtime_config(monkeypatch)
    path = tmp_path / "backend.env"
    database = tmp_path / "configured.sqlite3"
    origin = "http://127.0.0.1:3000"
    path.write_text(
        "R2R_SERVICES=real\nR2R_AI_MODE=mock\nR2R_IDENTITY_MODE=demo_local\n"
        f"R2R_DB_PATH={database.as_posix()}\nR2R_WEB_ORIGIN={origin}\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(config, "DEFAULT_ENV_FILE", path)

    main = fresh_main(monkeypatch)

    assert database.is_file()
    with TestClient(main.app, base_url="http://127.0.0.1:8000", client=("127.0.0.1", 50000)) as client:
        response = client.post("/api/reply/generate", json=GEN_BODY, headers={"Origin": origin})
        assert response.status_code == 200, response.text
        assert response.json()["reply"].startswith("[Mock reply")
        assert response.headers["access-control-allow-origin"] == origin
        assert client.get("/api/memory/search").json()["total"] == 0


def test_build_app_preserves_runtime_config_over_file_values(tmp_path, monkeypatch):
    clear_runtime_config(monkeypatch)
    path = tmp_path / "backend.env"
    wrong_database = tmp_path / "must-not-be-created.sqlite3"
    runtime_database = tmp_path / "runtime.sqlite3"
    path.write_text(
        "R2R_SERVICES=stub\nR2R_AI_MODE=claude\nR2R_IDENTITY_MODE=authenticated\n"
        f"R2R_DB_PATH={wrong_database.as_posix()}\nR2R_WEB_ORIGIN=https://wrong.example\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(config, "DEFAULT_ENV_FILE", path)
    for key, value in {
        "R2R_SERVICES": "real", "R2R_AI_MODE": "mock", "R2R_IDENTITY_MODE": "demo_local",
        "R2R_DB_PATH": str(runtime_database), "R2R_WEB_ORIGIN": "",
    }.items():
        monkeypatch.setenv(key, value)

    main = fresh_main(monkeypatch)

    assert runtime_database.is_file() and not wrong_database.exists()
    assert os.environ["R2R_WEB_ORIGIN"] == ""
    with TestClient(main.app, client=("127.0.0.1", 50000)) as client:
        response = client.post("/api/reply/generate", json=GEN_BODY)
        assert response.status_code == 200, response.text
        assert response.json()["reply"].startswith("[Mock reply")
