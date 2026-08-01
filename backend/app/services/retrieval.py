"""Keyless web retrieval + main-content extraction — NO LLM, no API key.

`search()`  -> candidate result URLs (DuckDuckGo HTML SERP + the Wikipedia page),
              queries built from the research-guide keyword taxonomy.
`fetch_and_extract()` -> one URL's clean main text as Markdown via `trafilatura`
              (strips nav/ads/boilerplate). `extract_page()` is the pure, network-free
              core so it can be unit-tested on fixture HTML.

Everything is fail-soft: a dead SERP, a 404, or an un-extractable page yields nothing
and the caller carries on with the other sources. `settings.mock_web` disables all
network so tests/E2E never reach out.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import List, Optional
from urllib.parse import parse_qs, quote, unquote, urlparse

import httpx
import trafilatura

from app.config import settings
from app.services import research_keywords

# Reuse the polite conventions the existing web fetchers use.
_UA = "SalesIntelAI/1.0 (pre-sales research tool)"
_TIMEOUT = 8.0

# Domains that are never useful as an evidence page (logins, trackers, aggregators).
_SKIP_DOMAINS = {
    "duckduckgo.com", "google.com", "bing.com", "youtube.com", "facebook.com",
    "twitter.com", "x.com", "instagram.com", "pinterest.com", "tiktok.com",
    "accounts.google.com", "doubleclick.net",
}


@dataclass
class ExtractedPage:
    url: str
    domain: str
    title: str
    markdown: str


def _domain(url: str) -> str:
    host = (urlparse(url).hostname or "").lower()
    return host[4:] if host.startswith("www.") else host


# Public alias so other modules don't import the underscore-private name (C1).
domain = _domain


def _decode_ddg_href(href: str) -> Optional[str]:
    """DuckDuckGo HTML wraps results in /l/?uddg=<encoded-url> redirects."""
    if href.startswith("//"):
        href = "https:" + href
    if "duckduckgo.com/l/" in href:
        target = parse_qs(urlparse(href).query).get("uddg", [""])[0]
        return unquote(target) or None
    if href.startswith("http"):
        return href
    return None


def _ddg_search(query: str, cap: int) -> List[str]:
    """Parse result links from the keyless DuckDuckGo HTML endpoint."""
    try:
        r = httpx.post(
            "https://html.duckduckgo.com/html/",
            data={"q": query},
            headers={"User-Agent": _UA}, timeout=_TIMEOUT, follow_redirects=True,
        )
        r.raise_for_status()
    except Exception:  # noqa: BLE001 — SERP may rate-limit / change; caller degrades
        return []

    urls: List[str] = []
    # Result anchors carry class="result__a"; attribute order varies, so match either way.
    for m in re.finditer(r'<a\b[^>]*\bhref="([^"]+)"[^>]*>', r.text):
        if 'result__a' not in m.group(0):
            continue
        target = _decode_ddg_href(m.group(1))
        if target:
            urls.append(target)
        if len(urls) >= cap:
            break
    return urls


def _wikipedia_url(company: str) -> Optional[str]:
    """Resolve the company's Wikipedia article via the keyless REST search endpoint."""
    try:
        r = httpx.get(
            "https://en.wikipedia.org/w/rest.php/v1/search/title",
            params={"q": company, "limit": 1},
            headers={"User-Agent": _UA}, timeout=_TIMEOUT,
        )
        r.raise_for_status()
        pages = r.json().get("pages", []) or []
        if pages:
            return "https://en.wikipedia.org/wiki/" + quote(pages[0]["key"])
    except Exception:  # noqa: BLE001
        pass
    return "https://en.wikipedia.org/wiki/" + quote(company.replace(" ", "_"))


def search(company: str, competitors: Optional[List[str]] = None) -> List[str]:
    """Top candidate URLs: keyword-guided DuckDuckGo results + the Wikipedia page."""
    if settings.mock_web:
        return []

    cap = max(1, settings.prep_max_results)
    per_query = max(2, cap // 2)
    seen: set[str] = set()
    out: List[str] = []

    for query in research_keywords.search_queries(company, competitors):
        for url in _ddg_search(query, per_query):
            dom = _domain(url)
            if not dom or dom in _SKIP_DOMAINS:
                continue
            if url in seen:
                continue
            seen.add(url)
            out.append(url)
            if len(out) >= cap:
                break
        if len(out) >= cap:
            break

    wiki = _wikipedia_url(company)
    if wiki and wiki not in seen:
        out.append(wiki)
    return out


def extract_page(html: str, url: str) -> Optional[ExtractedPage]:
    """Pure (no network): raw HTML -> ExtractedPage with clean Markdown, or None."""
    if not html:
        return None
    try:
        md = trafilatura.extract(
            html, output_format="markdown",
            include_comments=False, include_tables=True, favor_recall=True,
        )
    except Exception:  # noqa: BLE001 — malformed markup shouldn't crash the run
        md = None
    if not md or not md.strip():
        return None

    title = ""
    try:
        meta = trafilatura.extract_metadata(html)
        if meta and getattr(meta, "title", None):
            title = meta.title
    except Exception:  # noqa: BLE001
        pass

    return ExtractedPage(url=url, domain=_domain(url), title=title or url, markdown=md)


def fetch_and_extract(url: str) -> Optional[ExtractedPage]:
    """Network wrapper: download a URL and extract its main content."""
    if settings.mock_web:
        return None
    try:
        html = trafilatura.fetch_url(url)
    except Exception:  # noqa: BLE001
        html = None
    if not html:
        return None
    return extract_page(html, url)
