"""Small text helpers shared by more than one service (C4 — single source of truth)."""
from __future__ import annotations

import json
import re
from typing import Optional

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


def extract_json_object(raw: str) -> Optional[dict]:
    """Best-effort parse of a JSON object from an LLM response — tolerant of code
    fences and any stray text/backticks around it (e.g. a `{...}` followed by a lone
    ``` the model appended). Returns the dict, or None if nothing parses. Prevents the
    raw JSON blob from ever leaking to the user."""
    s = strip_fences(raw or "")
    # 1) the whole (de-fenced) string; 2) just the outermost {...} span.
    candidates = [s]
    i, j = s.find("{"), s.rfind("}")
    if 0 <= i < j:
        candidates.append(s[i : j + 1])
    for cand in candidates:
        try:
            obj = json.loads(cand)
        except Exception:  # noqa: BLE001 — not valid JSON, try the next candidate
            continue
        if isinstance(obj, dict):
            return obj
    return None
