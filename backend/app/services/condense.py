"""Deterministic text condensation — NO LLM.

Extractive (never abstractive): pulls the lead descriptive sentence and the key bullet
points straight out of already-extracted Markdown. Same input always yields the same
output, which is what keeps the Zoho product summary short *and* reproducible.
"""
from __future__ import annotations

import re
from typing import List

_SKIP_PREFIXES = ("#", "-", "*", "•", "|", ">")


def _clean(s: str) -> str:
    return re.sub(r"\s+", " ", (s or "")).strip()


def _truncate(text: str, max_chars: int) -> str:
    if len(text) <= max_chars:
        return text
    cut = text[:max_chars]
    for sep in (". ", "! ", "? "):
        i = cut.rfind(sep)
        if i > max_chars * 0.5:
            return cut[: i + 1].strip()
    i = cut.rfind(" ")
    return (cut[:i] if i > 0 else cut).strip() + "…"


def lead_paragraph(md: str, max_chars: int = 320) -> str:
    """First substantive prose block (skips headings/bullets/tables), sentence-trimmed."""
    for block in re.split(r"\n\s*\n", md or ""):
        lines = [
            ln.strip() for ln in block.split("\n")
            if ln.strip() and not ln.lstrip().startswith(_SKIP_PREFIXES)
        ]
        text = _clean(" ".join(lines))
        if len(text) >= 40:
            return _truncate(text, max_chars)
    return ""


def key_points(md: str, cap: int = 5, max_chars: int = 140) -> List[str]:
    """Up to `cap` distinct bullet points, cleaned of Markdown emphasis markers."""
    points: List[str] = []
    for line in (md or "").split("\n"):
        m = re.match(r"^\s*[-*•]\s+(.*)", line)
        if not m:
            continue
        text = _clean(m.group(1))
        text = re.sub(r"#+|\*+|_+|`+", "", text)          # strip md heading/bold/italic/code
        text = re.sub(r"(?i)^step\s*\d+\s*", "", text)    # drop "STEP 01" wizard prefixes
        text = _clean(text).strip(" -–—")
        if 15 <= len(text) <= max_chars and text not in points:
            points.append(text)
        if len(points) >= cap:
            break
    return points
