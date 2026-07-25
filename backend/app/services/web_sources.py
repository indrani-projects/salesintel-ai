"""Generic web prospect intel — fetch, keyword-filter (NO LLM), cache.

For a company NAME, query keyless public sources (Google News RSS, SEC EDGAR
full-text, Reddit), keyword-filter toward sales-relevant signals, and return a
short text block per source. Cached on disk with a TTL so repeated briefs/chats for
the same company don't re-fetch (Gemini usage is unchanged — this adds no LLM call;
the existing brief/chat calls synthesize this text like they do the local docs).

`settings.mock_web` returns deterministic canned intel (tests/E2E, no network).
Every fetch is fail-soft: any source can error and the rest still return.
"""
from __future__ import annotations

import hashlib
import html
import json
import re
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import List, Optional

import httpx

from app.config import settings
from app.services import company_hints

_BACKEND_DIR = Path(__file__).resolve().parent.parent.parent
_CACHE_DIR = _BACKEND_DIR / ".cache" / "webintel"
# SEC and Reddit block requests without a descriptive User-Agent.
_UA = "SalesIntelAI/1.0 (pre-sales research tool)"
_TIMEOUT = 8.0

# Sales-relevant terms from the research guide (docs/shared) — used to float the
# most useful snippets to the top before capping (keyword-guided extraction).
_KEYWORDS = [
    "earnings", "revenue", "guidance", "layoffs", "headcount", "cash burn", "loss",
    "arr", "churn", "acquisition", "partnership", "launch", "feature", "expansion",
    "cfo", "cto", "ceo", "hire", "pricing", "complaint", "alternative", "switched",
    "salesforce", "hubspot", "quickbooks", "workday",
]


@dataclass
class WebDoc:
    source: str        # "Google News" | "SEC EDGAR" | "Reddit" | "Zoho Angle"
    url: str
    text: str


# --------------------------------------------------------------------------- #
# Keyword-priority filtering
# --------------------------------------------------------------------------- #
def _prioritize(text: str, cap: int) -> str:
    parts = [p for p in text.split("\n") if p.strip()]
    header = parts[0] if (parts and not parts[0].startswith("- ")) else ""
    items = [p for p in parts if p.startswith("- ")]
    items.sort(key=lambda l: -sum(1 for k in _KEYWORDS if k in l.lower()))
    out = [header] if header else []
    total = len(header)
    for line in items:
        if total + len(line) + 1 > cap:
            break
        out.append(line)
        total += len(line) + 1
    return "\n".join(out)


def _clean(s: str) -> str:
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", s or ""))).strip()


# --------------------------------------------------------------------------- #
# Keyless source fetchers (each returns a WebDoc or None; may raise → skipped)
# --------------------------------------------------------------------------- #
def _fetch_news(company: str) -> Optional[WebDoc]:
    r = httpx.get(
        "https://news.google.com/rss/search",
        params={"q": f'"{company}"', "hl": "en-US", "gl": "US", "ceid": "US:en"},
        headers={"User-Agent": _UA}, timeout=_TIMEOUT, follow_redirects=True,
    )
    r.raise_for_status()
    lines = []
    for item in re.findall(r"<item>(.*?)</item>", r.text, re.S)[:15]:
        m = re.search(r"<title>(.*?)</title>", item, re.S)
        d = re.search(r"<pubDate>(.*?)</pubDate>", item, re.S)
        title = _clean(m.group(1)) if m else ""
        date = (d.group(1).strip()[:16]) if d else ""
        if title:
            lines.append(f"- {title}" + (f" ({date})" if date else ""))
    if not lines:
        return None
    return WebDoc("Google News", "https://news.google.com/search",
                  "Recent news headlines:\n" + "\n".join(lines))


def _fetch_sec(company: str) -> Optional[WebDoc]:
    r = httpx.get(
        "https://efts.sec.gov/LATEST/search-index",
        params={"q": f'"{company}"', "forms": "8-K,10-Q,10-K"},
        headers={"User-Agent": _UA}, timeout=_TIMEOUT,
    )
    r.raise_for_status()
    hits = (r.json().get("hits", {}) or {}).get("hits", [])[:10]
    lines = []
    for h in hits:
        src = h.get("_source", {}) or {}
        form = src.get("root_form") or src.get("file_type") or "filing"
        date = src.get("file_date", "")
        names = "; ".join(src.get("display_names", []) or [])
        lines.append(f"- {form} filed {date} — {names}".strip())
    if not lines:
        return None
    return WebDoc("SEC EDGAR", "https://efts.sec.gov/LATEST/search-index",
                  "Recent SEC filings (material events / financials):\n" + "\n".join(lines))


def _fetch_reddit(company: str) -> Optional[WebDoc]:
    r = httpx.get(
        "https://www.reddit.com/search.json",
        params={"q": f'"{company}"', "limit": 12, "sort": "relevance", "t": "year"},
        headers={"User-Agent": _UA}, timeout=_TIMEOUT,
    )
    r.raise_for_status()
    lines = []
    for p in (r.json().get("data", {}) or {}).get("children", [])[:12]:
        d = p.get("data", {}) or {}
        title = _clean(d.get("title", ""))
        body = _clean(d.get("selftext", ""))[:180]
        sub = d.get("subreddit_name_prefixed", "")
        if title:
            lines.append(f"- [{sub}] {title}" + (f" — {body}" if body else ""))
    if not lines:
        return None
    return WebDoc("Reddit", "https://www.reddit.com/search",
                  "Reddit discussions (sentiment / pain points):\n" + "\n".join(lines))


_FETCHERS = (_fetch_news, _fetch_sec, _fetch_reddit)


def _hint_doc(company: str) -> Optional[WebDoc]:
    hint = company_hints.hint_for(company)
    if not hint:
        return None
    text = (
        f"Zoho pitch angle (from the research guide): {hint['why']} "
        f"Lead with: {', '.join(hint['zoho_products'])}. "
        f"Ticker: {hint['ticker']}. Competitor tools to displace: "
        f"{', '.join(hint['competitors'])}."
    )
    return WebDoc("Zoho Angle", "", text)


# --------------------------------------------------------------------------- #
# Cache
# --------------------------------------------------------------------------- #
def _cache_file(company: str) -> Path:
    key = hashlib.sha256(company_hints._norm(company).encode()).hexdigest()[:24]
    return _CACHE_DIR / f"{key}.json"


def _read_cache(company: str) -> Optional[List[WebDoc]]:
    try:
        data = json.loads(_cache_file(company).read_text(encoding="utf-8"))
        if (time.time() - data["fetched_at"]) / 3600 < settings.web_ttl_hours:
            return [WebDoc(**d) for d in data["docs"]]
    except Exception:
        pass
    return None


def _write_cache(company: str, docs: List[WebDoc]) -> None:
    try:
        _CACHE_DIR.mkdir(parents=True, exist_ok=True)
        _cache_file(company).write_text(
            json.dumps({"fetched_at": time.time(), "docs": [asdict(d) for d in docs]}),
            encoding="utf-8",
        )
    except OSError:
        pass


# --------------------------------------------------------------------------- #
# Public API
# --------------------------------------------------------------------------- #
def fetch_intel(company_name: str, force: bool = False) -> List[WebDoc]:
    """Web intel for a company (cached). Empty list ⇒ caller should fall back to docs."""
    if settings.mock_web:
        return _mock_docs(company_name)
    if not force:
        cached = _read_cache(company_name)
        if cached is not None:
            return cached

    docs: List[WebDoc] = []
    for fetch in _FETCHERS:
        try:
            doc = fetch(company_name)
            if doc and doc.text.strip():
                doc.text = _prioritize(doc.text, settings.web_max_chars)
                docs.append(doc)
        except Exception:  # noqa: BLE001 — any source may fail; keep the rest
            continue

    hint = _hint_doc(company_name)
    if hint:
        docs.append(hint)

    _write_cache(company_name, docs)
    return docs


def _mock_docs(company: str) -> List[WebDoc]:
    return [
        WebDoc(
            "Google News", "https://news.google.com/search",
            f"Recent news headlines:\n- {company} reports Q2 revenue growth, raises "
            f"guidance\n- {company} announces new CFO amid expansion\n- {company} "
            f"layoffs reported in support org",
        ),
        WebDoc(
            "Reddit", "https://www.reddit.com/search",
            f"Reddit discussions (sentiment / pain points):\n- [r/sales] {company} "
            f"pricing complaint — users exploring an alternative after Salesforce costs",
        ),
    ]
