"""Rule-based source credibility scoring — NO LLM.

Every fetched page carries a trust weight so later stages (and the UI) can prefer
authoritative sources over blogs/forums. This is pure domain heuristics: government /
SEC filings and encyclopedic/official/tier-1-press sources rank high; social, forum,
and self-published blog domains rank low; everything else is middling "web".

`score(url, company)` -> (credibility_0_100, source_type).
"""
from __future__ import annotations

import re
from typing import Optional, Tuple
from urllib.parse import urlparse

# Tier-1 business/tech press + primary wires (authoritative secondary sources).
_TIER1_PRESS = {
    "reuters.com", "bloomberg.com", "wsj.com", "ft.com", "cnbc.com", "forbes.com",
    "techcrunch.com", "theguardian.com", "nytimes.com", "businessinsider.com",
    "fortune.com", "axios.com", "theverge.com", "zdnet.com", "venturebeat.com",
    "businesswire.com", "prnewswire.com", "globenewswire.com", "nasdaq.com",
    "marketwatch.com", "seekingalpha.com",
}

# Self-publish / social / forum domains — unfiltered, low individual trust.
_LOW_TRUST = {
    "reddit.com", "quora.com", "medium.com", "substack.com", "blogspot.com",
    "wordpress.com", "tumblr.com", "facebook.com", "twitter.com", "x.com",
    "youtube.com", "pinterest.com", "glassdoor.com", "indeed.com",
}


def _registrable(host: str) -> str:
    """Best-effort registrable domain (last two labels). Good enough for tiering."""
    host = (host or "").lower().strip().lstrip(".")
    if host.startswith("www."):
        host = host[4:]
    parts = host.split(".")
    return ".".join(parts[-2:]) if len(parts) >= 2 else host


def _compact_name(company: str) -> str:
    """Company name -> comparable domain form: lowercase, drop leading 'the', alnum only.
    'The Sleep Company' -> 'sleepcompany'; 'Sprout Social' -> 'sproutsocial'."""
    name = re.sub(r"^the\s+", "", (company or "").strip().lower())
    return re.sub(r"[^a-z0-9]", "", name)


def _is_official_domain(reg: str, company: str) -> bool:
    """True only when the domain's primary label matches the whole compacted company
    name — so 'thesleepcompany.in' is official for The Sleep Company, but the unrelated
    'sleepnumber.com' is NOT (a loose 'sleep' token match would wrongly claim it)."""
    compact = _compact_name(company)
    if len(compact) < 5:
        return False
    label = reg.split(".")[0]  # 'sleepnumber' from 'sleepnumber.com'
    return compact in label or label in compact


def score(url: str, company: Optional[str] = None) -> Tuple[int, str]:
    """Return (credibility 0-100, source_type) for a URL."""
    if not url:
        return 50, "web"
    host = (urlparse(url).hostname or "").lower()
    if not host:
        return 50, "web"
    reg = _registrable(host)

    # Government / regulatory filings — highest trust.
    if host.endswith(".gov") or reg == "sec.gov" or "sec.gov" in host:
        return 95, "regulatory"

    # Encyclopedic.
    if reg == "wikipedia.org":
        return 85, "encyclopedia"

    # Official company domain (primary label matches the whole company name).
    if company and _is_official_domain(reg, company):
        return 90, "official"

    # Tier-1 press / primary wires.
    if reg in _TIER1_PRESS:
        return 80, "tier1_press"

    # Low-trust social / forum / self-publish.
    if reg in _LOW_TRUST:
        return 35, "social"

    # Unknown press / company blog / generic web.
    return 55, "web"


def is_authoritative(source_type: str) -> bool:
    """High-trust types whose descriptive lead is worth keeping even without a keyword hit."""
    return source_type in {"regulatory", "encyclopedia", "official", "tier1_press"}
