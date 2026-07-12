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
os.environ["DATABASE_URL"] = f"sqlite:///{_DB_FILE.as_posix()}"
os.environ.setdefault("LLM_API_KEY", "test-key")

import pytest
from fastapi.testclient import TestClient


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
