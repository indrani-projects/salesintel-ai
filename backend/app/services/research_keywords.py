"""Keyword taxonomy from the research guide (docs/shared/SalesIntel_Research_Guide).

Section 3 of the guide ("Search Topics & Relevant Terms by Category") is a ready-made
controlled vocabulary. It answers "what should we look for on a page?" and is used two
ways by the prep stage (NO LLM):

  1. `search_queries()`  — expands the terms into a handful of focused web queries.
  2. `match_categories()`— decides which category (if any) a passage of extracted text
                           belongs to, so only relevant passages are kept + tagged.

`{company}` / `{competitor}` are placeholders filled in per target. Matching is a plain
case-insensitive substring test — deterministic, quota-free, no model call.
"""
from __future__ import annotations

import re
from typing import Dict, List, Optional

# Section 3 of the guide, verbatim in intent. Terms carry {company}/{competitor}
# placeholders; the leading "{company} " is also matched with the prefix stripped, since
# a prepared doc is already scoped to the target company (the name is often implicit).
CATEGORIES: Dict[str, List[str]] = {
    "financial_intel": [
        "quarterly earnings", "revenue growth", "operating loss", "headcount reduction",
        "guidance lowered", "cash burn", "arr", "nrr", "net revenue retention",
        "churn", "eps", "quarterly revenue",
    ],
    "product_strategy": [
        "{company} product launch", "{company} new feature", "{company} acquisition",
        "{company} partnership", "{company} layoffs", "{company} expansion",
        "{company} vs {competitor}",
    ],
    "leadership_changes": [
        "new cto", "new cfo", "new ceo", "ceo transition", "board appointment",
        "executive hire", "appointed as", "steps down", "chief financial officer",
        "chief technology officer",
    ],
    "pain_points": [
        "{company} pricing complaint", "{company} crm issues", "{company} slow onboarding",
        "switched from {company}", "{company} alternative", "pricing complaint",
        "too expensive", "hard to use", "poor support",
    ],
    "social_signals": [
        "product mentions", "internal tools", "employee post", "job posting",
        "hiring for", "now hiring",
    ],
    # Competitor tools Zoho directly displaces — their presence is a high-intent signal.
    "job_intent": [
        "salesforce", "hubspot", "quickbooks", "workday", "slack",
    ],
}


def _norm_ws(s: str) -> str:
    return re.sub(r"\s+", " ", s or "").strip()


def _expand_term(term: str, company: str, competitors: List[str]) -> List[str]:
    """One templated term -> concrete lowercase needles for substring matching."""
    comp = (company or "").lower().strip()
    comps = [c.lower().strip() for c in (competitors or []) if c and c.strip()]

    variants = [term]
    if "{company}" in term:
        # Also match the term with the company placeholder removed (name implicit).
        variants.append(term.replace("{company}", " "))

    needles: set[str] = set()
    for v in variants:
        if "{competitor}" in v:
            for c in comps:
                needles.add(v.replace("{company}", comp).replace("{competitor}", c))
        else:
            needles.add(v.replace("{company}", comp))

    return [n for n in (_norm_ws(x) for x in needles) if len(n) >= 3]


def match_categories(
    text: str,
    company: str = "",
    competitors: Optional[List[str]] = None,
) -> List[str]:
    """Return the guide categories a passage hits (case-insensitive substring match)."""
    low = (text or "").lower()
    if not low.strip():
        return []
    hits: List[str] = []
    for category, terms in CATEGORIES.items():
        for term in terms:
            if any(_needle_in(n, low) for n in _expand_term(term, company, competitors or [])):
                hits.append(category)
                break
    return hits


def _needle_in(needle: str, low: str) -> bool:
    """Substring match, but word-bounded for short acronyms so 'arr'/'nrr'/'eps'/'cfo'
    don't match inside unrelated words (e.g. 'arr' in 'warranty')."""
    if len(needle) <= 4 and " " not in needle:
        return re.search(rf"(?<![a-z0-9]){re.escape(needle)}(?![a-z0-9])", low) is not None
    return needle in low


def search_queries(company: str, competitors: Optional[List[str]] = None) -> List[str]:
    """A small set of focused, keyless-search-friendly queries built from the guide."""
    comps = competitors or []
    q = [
        company,
        f"{company} quarterly earnings revenue growth",
        f"{company} layoffs OR acquisition OR partnership",
        f"{company} new CFO OR new CTO leadership change",
        f"{company} pricing complaint OR alternative OR review",
    ]
    if comps:
        q.append(f"{company} vs {comps[0]}")
    # De-dupe while preserving order.
    seen: set[str] = set()
    out: List[str] = []
    for item in q:
        key = item.lower()
        if key not in seen:
            seen.add(key)
            out.append(item)
    return out
