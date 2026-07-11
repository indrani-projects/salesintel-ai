"""Shared test fixtures.

Env is configured BEFORE importing the app so pydantic-settings picks it up:
- MOCK_LLM=1        → deterministic briefs/chat, no Gemini calls, no quota use
- DATABASE_URL      → isolated throwaway SQLite file
"""
import os

os.environ["MOCK_LLM"] = "1"
os.environ["DATABASE_URL"] = "sqlite:///./test_salesintel.db"
os.environ.setdefault("LLM_API_KEY", "test-key")

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

_DB_FILE = Path(__file__).resolve().parent.parent / "test_salesintel.db"


@pytest.fixture(scope="session")
def client():
    from app.main import app

    with TestClient(app) as c:  # triggers startup → init_db()
        yield c


@pytest.fixture(scope="session", autouse=True)
def _cleanup_db():
    yield
    try:
        if _DB_FILE.exists():
            _DB_FILE.unlink()
    except OSError:
        pass
