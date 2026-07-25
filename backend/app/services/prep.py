"""Prospect data preparation — fetch the web, keep what the guide says matters, cache.

This is the deterministic foundation stage of the web-to-pitch engine and it uses NO
LLM. For a company it:

  1. retrieves candidate pages (keyword-guided keyless search + Wikipedia) and the
     existing keyless feeds (`web_sources`),
  2. extracts each page's clean main text (`retrieval`/`trafilatura`),
  3. keeps only passages that match the research-guide keyword taxonomy
     (`research_keywords`) and tags each by category,
  4. scores every source's credibility by domain rules (`credibility`),
  5. writes one clean Markdown doc per source + a `manifest.json` into a git-ignored,
     TTL'd cache at `backend/.cache/prepared/<slug>/`.

The LLM only runs in later stages, reading these small, grounded, pre-filtered docs —
which is also what keeps us inside the Gemini free tier. Cached + idempotent: a fresh
manifest short-circuits without re-fetching.
"""
from __future__ import annotations

import json
import re
import time
from pathlib import Path
from typing import List, Optional

from app.config import settings
from app.services import (
    company_hints,
    credibility,
    research_keywords,
    retrieval,
    sources,
    web_sources,
)
from app.services.retrieval import ExtractedPage, _domain

_BACKEND_DIR = Path(__file__).resolve().parent.parent.parent
# Git-ignored (backend/.cache/ is in .gitignore), mirrors the webintel/ cache pattern.
PREPARED_ROOT = _BACKEND_DIR / ".cache" / "prepared"

# Caps to keep prepared docs small (and later LLM calls cheap).
_MAX_PASSAGES = 40
_MIN_PASSAGE = 20

# Display order: descriptive lead first, then the guide's signal categories.
_CATEGORY_ORDER = ["overview"] + list(research_keywords.CATEGORIES.keys())


# --------------------------------------------------------------------------- #
# Slug / paths
# --------------------------------------------------------------------------- #
def company_slug(company_name: str, slug: Optional[str] = None) -> str:
    """Stable cache slug for a company (shared by writer + reader)."""
    return slug or sources.slugify(company_name)


def company_dir(slug: str) -> Path:
    return PREPARED_ROOT / slug


def _manifest_path(slug: str) -> Path:
    return company_dir(slug) / "manifest.json"


# --------------------------------------------------------------------------- #
# Passage extraction + filtering (NO LLM)
# --------------------------------------------------------------------------- #
def _norm(s: str) -> str:
    return re.sub(r"\s+", " ", (s or "").strip().lower())


def _split_passages(markdown: str) -> List[str]:
    """Break Markdown into paragraph/bullet passages worth scoring."""
    passages: List[str] = []
    for block in re.split(r"\n\s*\n", markdown or ""):
        block = block.strip()
        if not block:
            continue
        # Drop Markdown heading lines — the doc renders its own "# {title}" header, so a
        # kept "# ..." passage would just duplicate it.
        lines = [
            ln.strip() for ln in block.split("\n")
            if ln.strip() and not ln.lstrip().startswith("#")
        ]
        bullets = [ln for ln in lines if re.match(r"^[-*•]\s+", ln)]
        if len(bullets) >= 2:
            for ln in bullets:
                item = re.sub(r"^[-*•]\s+", "", ln).strip()
                if len(item) >= _MIN_PASSAGE:
                    passages.append(item)
        else:
            joined = " ".join(lines).strip()
            if len(joined) >= _MIN_PASSAGE:
                passages.append(joined)
    return passages


def _keep_passages(
    page: ExtractedPage, company: str, competitors: List[str], source_type: str,
) -> List[tuple[str, List[str]]]:
    """Return [(passage, [categories])] — keyword-matched passages, plus the descriptive
    lead of an authoritative source so firmographics survive even without a keyword hit."""
    passages = _split_passages(page.markdown)
    kept: List[tuple[str, List[str]]] = []
    seen: set[str] = set()

    # Descriptive lead of a trusted source (Wikipedia / official / SEC / tier-1) —
    # kept for firmographic context even without a keyword hit, but still carrying any
    # signal categories it does match so they aren't lost to the "overview" tag.
    if credibility.is_authoritative(source_type) and passages:
        lead = passages[0]
        seen.add(_norm(lead))
        lead_cats = research_keywords.match_categories(lead, company, competitors)
        kept.append((lead, ["overview"] + lead_cats))

    for p in passages:
        key = _norm(p)
        if key in seen:
            continue
        cats = research_keywords.match_categories(p, company, competitors)
        if not cats:
            continue
        seen.add(key)
        kept.append((p, cats))
        if len(kept) >= _MAX_PASSAGES:
            break
    return kept


def _primary_category(cats: List[str]) -> str:
    # Prefer a concrete guide signal over the generic "overview" tag.
    for c in _CATEGORY_ORDER:
        if c != "overview" and c in cats:
            return c
    return "overview"


def _render_doc(
    page: ExtractedPage, cred: int, source_type: str,
    kept: List[tuple[str, List[str]]],
) -> str:
    """Group kept passages under their category and render a clean Markdown doc."""
    by_cat: dict[str, List[str]] = {}
    for passage, cats in kept:
        by_cat.setdefault(_primary_category(cats), []).append(passage)

    src = page.url or page.domain or "n/a"
    out = [
        f"# {page.title}",
        "",
        f"_Source: {src} — credibility {cred}/100 ({source_type})_",
    ]
    for cat in _CATEGORY_ORDER:
        items = by_cat.get(cat)
        if not items:
            continue
        out.append("")
        out.append(f"## {cat}")
        for it in items:
            out.append(f"- {it}")
    return "\n".join(out).strip() + "\n"


def _source_slug(page: ExtractedPage) -> str:
    base = page.domain or page.title or "source"
    s = re.sub(r"[^a-z0-9]+", "-", base.lower()).strip("-")
    return (s or "source")[:30]


# --------------------------------------------------------------------------- #
# Cache read
# --------------------------------------------------------------------------- #
def _read_manifest(slug: str) -> Optional[dict]:
    try:
        return json.loads(_manifest_path(slug).read_text(encoding="utf-8"))
    except Exception:  # noqa: BLE001 — missing/corrupt cache => treat as absent
        return None


def _is_fresh(manifest: dict) -> bool:
    try:
        age_h = (time.time() - float(manifest["prepared_at"])) / 3600
        return age_h < settings.prep_ttl_hours
    except Exception:  # noqa: BLE001
        return False


# --------------------------------------------------------------------------- #
# Public API
# --------------------------------------------------------------------------- #
def _gather_pages(company_name: str, competitors: List[str]) -> List[ExtractedPage]:
    pages: List[ExtractedPage] = []
    if settings.prep_enabled:
        for url in retrieval.search(company_name, competitors):
            page = retrieval.fetch_and_extract(url)
            if page:
                pages.append(page)
    # Existing keyless feeds (News RSS / SEC / Reddit / Zoho-angle) as extra evidence.
    try:
        for wd in web_sources.fetch_intel(company_name):
            if wd.text and wd.text.strip():
                pages.append(ExtractedPage(
                    url=wd.url or "", domain=_domain(wd.url or ""),
                    title=wd.source, markdown=wd.text,
                ))
    except Exception:  # noqa: BLE001 — feeds are best-effort
        pass
    return pages


def prepare_company(
    company_name: str, slug: Optional[str] = None, force: bool = False,
) -> dict:
    """Fetch + filter + cache prepared docs for a company. Returns the manifest dict."""
    slug = company_slug(company_name, slug)

    if not force:
        existing = _read_manifest(slug)
        if existing and _is_fresh(existing):
            return existing

    hint = company_hints.hint_for(company_name)
    competitors = list(hint["competitors"]) if hint else []

    # Build every doc in memory first, so a failed fetch pass never wipes a good cache.
    built: List[tuple[str, str, dict]] = []  # (filename, content, meta)
    n = 0
    for page in _gather_pages(company_name, competitors):
        cred, source_type = credibility.score(page.url, company_name)
        kept = _keep_passages(page, company_name, competitors, source_type)
        if not kept:
            continue
        n += 1
        doc_md = _render_doc(page, cred, source_type, kept)
        if len(doc_md) > settings.prep_max_doc_chars:
            doc_md = doc_md[: settings.prep_max_doc_chars]
        filename = f"{n:02d}-{_source_slug(page)}.md"
        categories = sorted({c for _, cats in kept for c in cats})
        built.append((filename, doc_md, {
            "file": filename,
            "url": page.url or None,
            "domain": page.domain,
            "title": page.title,
            "credibility": cred,
            "source_type": source_type,
            "categories": categories,
            "char_count": len(doc_md),
        }))

    if not built:
        # Nothing usable this run — keep any prior cache rather than clobbering it.
        prior = _read_manifest(slug)
        if prior:
            return prior

    cdir = company_dir(slug)
    cdir.mkdir(parents=True, exist_ok=True)
    # Clear stale docs so removed sources don't linger.
    for old in cdir.glob("*.md"):
        try:
            old.unlink()
        except OSError:
            pass

    for filename, content, _meta in built:
        (cdir / filename).write_text(content, encoding="utf-8")

    manifest = {
        "prepared_at": time.time(),
        "company": company_name,
        "slug": slug,
        "docs": [meta for _f, _c, meta in built],
    }
    _manifest_path(slug).write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return manifest
