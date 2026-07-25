"""Shared test fixtures.

Env is configured BEFORE importing the app so pydantic-settings picks it up:
- MOCK_LLM=1        → deterministic briefs/chat, no Gemini calls, no quota use
- MOCK_EMAIL=1      → "Send as email" never contacts a real mail server
- DATABASE_URL      → isolated throwaway SQLite file
"""
import os
from pathlib import Path

# Absolute path (relative to backend/) so the throwaway DB lands in the same spot
# regardless of the cwd pytest is launched from — and is therefore always cleaned
# up by _cleanup_db below. (A cwd-relative URL would strand the file wherever
# pytest happened to run, e.g. the repo root.)
_DB_FILE = Path(__file__).resolve().parent.parent / "test_salesintel.db"

os.environ["MOCK_LLM"] = "1"
os.environ["MOCK_EMAIL"] = "1"
os.environ["MOCK_GOOGLE"] = "1"
os.environ["MOCK_WEB"] = "1"
# Tests drive calendar sync explicitly; keep the boot-time auto-sync off so its
# background pass can't race the "clean first sync" assertions.
os.environ["SYNC_ON_STARTUP"] = "0"
# Auto-email: keep the master switch OFF so the on-ready hook and the reminder
# daemon never fire during unrelated tests; test_notifier.py calls the notifier
# functions directly. A recipient is set so those direct calls have a target.
os.environ["AUTO_EMAIL_ENABLED"] = "0"
os.environ["DEFAULT_RECIPIENT"] = "rep@salesintel.test"
os.environ["DATABASE_URL"] = f"sqlite:///{_DB_FILE.as_posix()}"
os.environ.setdefault("LLM_API_KEY", "test-key")

import pytest
from fastapi.testclient import TestClient


@pytest.fixture(scope="session", autouse=True)
def _isolate_prepared_cache(tmp_path_factory):
    """Point the prepared-docs cache at an empty temp dir so a real
    backend/.cache/prepared/<slug>/ (left by a live `prepare` run) can't leak into
    tests and change load_company_intel's source preference. test_prep.py monkeypatches
    this per-test on top of the empty root."""
    from app.services import prep

    prep.PREPARED_ROOT = tmp_path_factory.mktemp("prepared_empty")
    yield


@pytest.fixture(scope="session")
def client():
    from app.main import app

    with TestClient(app) as c:  # triggers startup → init_db()
        yield c


@pytest.fixture(scope="session", autouse=True)
def _cleanup_db():
    yield
    # Dispose the engine first — on Windows SQLite keeps the file locked while any
    # connection is open, so unlink() would otherwise fail and strand the file.
    try:
        from app.db import engine

        engine.dispose()
    except Exception:
        pass
    try:
        if _DB_FILE.exists():
            _DB_FILE.unlink()
    except OSError:
        pass
