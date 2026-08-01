"""Small text helpers shared by more than one service (C4 — single source of truth)."""
from __future__ import annotations

import re

# Max characters of a single source doc stuffed into an LLM prompt — keeps the
# one-call context bounded. Shared by sources.py and chat_service.py.
MAX_DOC_CHARS = 8000


def strip_fences(raw: str) -> str:
    """Strip a leading/trailing ```lang … ``` markdown code fence from LLM output."""
    raw = raw.strip()
    if raw.startswith("```"):
        raw = re.sub(r"^```[a-zA-Z0-9]*\s*", "", raw)
        raw = re.sub(r"\s*```$", "", raw)
    return raw.strip()
