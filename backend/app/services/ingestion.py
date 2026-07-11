"""Text extraction with a per-file cache (AI-Engine Agent, Epic E3, S3.2).

- `.pdf`   -> PyMuPDF (fitz)
- `.md`/`.txt` -> plain read
- `.html`/`.htm` -> crude tag stripping

Extracted text is cached under backend/.cache/ keyed on the absolute filepath +
mtime + size so re-runs are fast and stale cache entries are ignored.
"""
from __future__ import annotations

import hashlib
import re
from pathlib import Path

# backend/ directory (this file lives in backend/app/services/)
_BACKEND_DIR = Path(__file__).resolve().parent.parent.parent
_CACHE_DIR = _BACKEND_DIR / ".cache"


def _cache_key(path: Path) -> str:
    """Stable key based on absolute path + mtime + size."""
    try:
        st = path.stat()
        sig = f"{path.resolve()}|{int(st.st_mtime)}|{st.st_size}"
    except OSError:
        sig = str(path.resolve())
    return hashlib.sha256(sig.encode("utf-8")).hexdigest()


def _cache_path(path: Path) -> Path:
    return _CACHE_DIR / f"{_cache_key(path)}.txt"


def _read_cache(path: Path) -> str | None:
    cp = _cache_path(path)
    if cp.exists():
        try:
            return cp.read_text(encoding="utf-8")
        except OSError:
            return None
    return None


def _write_cache(path: Path, text: str) -> None:
    try:
        _CACHE_DIR.mkdir(parents=True, exist_ok=True)
        _cache_path(path).write_text(text, encoding="utf-8")
    except OSError:
        # Caching is best-effort; never fail extraction because of it.
        pass


def _clean(text: str) -> str:
    """Normalize whitespace: collapse runs of blank lines and trailing spaces."""
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    # Strip trailing spaces on each line.
    text = re.sub(r"[ \t]+\n", "\n", text)
    # Collapse 3+ newlines into 2.
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def _extract_pdf(path: Path) -> str:
    import fitz  # PyMuPDF

    parts: list[str] = []
    with fitz.open(str(path)) as doc:
        for page in doc:
            parts.append(page.get_text("text"))
    return "\n".join(parts)


def _strip_html(raw: str) -> str:
    # Drop script/style blocks entirely.
    raw = re.sub(r"(?is)<(script|style)[^>]*>.*?</\1>", " ", raw)
    # Turn block-ish tags into newlines for readability.
    raw = re.sub(r"(?i)<(br|/p|/div|/li|/tr|/h[1-6])[^>]*>", "\n", raw)
    # Remove all remaining tags.
    raw = re.sub(r"(?s)<[^>]+>", " ", raw)
    # Decode a few common entities.
    for ent, rep in (
        ("&nbsp;", " "), ("&amp;", "&"), ("&lt;", "<"), ("&gt;", ">"),
        ("&quot;", '"'), ("&#39;", "'"), ("&rsquo;", "'"), ("&lsquo;", "'"),
        ("&ldquo;", '"'), ("&rdquo;", '"'), ("&mdash;", "-"), ("&ndash;", "-"),
    ):
        raw = raw.replace(ent, rep)
    return raw


def extract_text(path: str | Path) -> str:
    """Extract clean plain text from a document, using the on-disk cache."""
    p = Path(path)
    if not p.exists():
        return ""

    cached = _read_cache(p)
    if cached is not None:
        return cached

    suffix = p.suffix.lower()
    try:
        if suffix == ".pdf":
            raw = _extract_pdf(p)
        elif suffix in (".md", ".txt"):
            raw = p.read_text(encoding="utf-8", errors="replace")
        elif suffix in (".html", ".htm"):
            raw = _strip_html(p.read_text(encoding="utf-8", errors="replace"))
        else:
            # Best-effort plain read for unknown types.
            raw = p.read_text(encoding="utf-8", errors="replace")
    except Exception:
        raw = ""

    text = _clean(raw)
    _write_cache(p, text)
    return text
