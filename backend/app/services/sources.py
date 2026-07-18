"""Company + source discovery (AI-Engine Agent, Epic E3, S3.1).

Scans `settings.docs_root_path` for prospect company folders, resolves free-text
company names to folder slugs, and loads/extracts source documents (prospect docs
plus the shared Zoho product knowledge) into `SourceDoc` records.
"""
from __future__ import annotations

from pathlib import Path
from typing import List, Optional

from app.config import settings
from app.contracts import SourceDoc
from app.schemas import CompanyRead
from app.services.ingestion import extract_text

# Extensions we treat as ingestable source documents.
_DOC_EXTS = {".pdf", ".md", ".txt", ".html", ".htm"}

# Folders that are never prospect companies.
_ZOHO_SLUG = "zoho"

# Per-document text truncation to control token usage / latency.
_MAX_DOC_CHARS = 8000

# Known slug -> display-name overrides. Other slugs are prettified generically.
COMPANY_NAMES: dict[str, str] = {
    "sleep_company": "The Sleep Company",
}


def _display_name(slug: str) -> str:
    if slug in COMPANY_NAMES:
        return COMPANY_NAMES[slug]
    return slug.replace("_", " ").replace("-", " ").title()


def _prettify_stem(stem: str) -> str:
    """Turn a filename stem into a readable title."""
    s = stem.replace("_", " ").replace("-", " ").strip()
    # Collapse whitespace.
    s = " ".join(s.split())
    return s or stem


def _is_company_folder(p: Path) -> bool:
    if not p.is_dir():
        return False
    name = p.name
    if name.startswith(".") or name.startswith("_"):
        return False
    if name.lower() == _ZOHO_SLUG:
        return False
    return True


def _doc_files(folder: Path) -> list[Path]:
    if not folder.exists():
        return []
    files = [
        f for f in folder.iterdir()
        if f.is_file() and f.suffix.lower() in _DOC_EXTS
    ]
    return sorted(files, key=lambda f: f.name.lower())


def list_companies() -> List[CompanyRead]:
    """Scan docs_root for prospect company folders (excluding zoho/hidden)."""
    root = settings.docs_root_path
    companies: list[CompanyRead] = []
    if not root.exists():
        return companies
    for entry in sorted(root.iterdir(), key=lambda p: p.name.lower()):
        if not _is_company_folder(entry):
            continue
        count = len(_doc_files(entry))
        companies.append(
            CompanyRead(
                slug=entry.name,
                name=_display_name(entry.name),
                doc_count=count,
            )
        )
    return companies


def _normalize(name_or_slug: str) -> str:
    s = (name_or_slug or "").strip().lower()
    if s.startswith("the "):
        s = s[4:]
    s = s.strip()
    # Non-alphanumeric -> spaces, then spaces -> underscore.
    cleaned = []
    for ch in s:
        if ch.isalnum():
            cleaned.append(ch)
        else:
            cleaned.append(" ")
    s = " ".join("".join(cleaned).split())
    return s.replace(" ", "_")


def resolve_company_slug(name_or_slug: str) -> Optional[str]:
    """Map a free-text company name (or slug) to an existing docs/<slug> folder."""
    if not name_or_slug:
        return None
    root = settings.docs_root_path
    if not root.exists():
        return None

    folders = [p for p in root.iterdir() if _is_company_folder(p)]

    # Exact slug match first.
    raw = name_or_slug.strip()
    for f in folders:
        if f.name == raw or f.name.lower() == raw.lower():
            return f.name

    target = _normalize(name_or_slug)
    if not target:
        return None

    # Normalized match against folder name and its known display name.
    for f in folders:
        if _normalize(f.name) == target:
            return f.name
        if _normalize(_display_name(f.name)) == target:
            return f.name

    return None


def _load_folder_docs(
    folder: Path,
    tag: str,
    start_index: int,
) -> tuple[list[SourceDoc], int]:
    docs: list[SourceDoc] = []
    idx = start_index
    for f in _doc_files(folder):
        text = extract_text(f)
        if len(text) > _MAX_DOC_CHARS:
            text = text[:_MAX_DOC_CHARS]
        docs.append(
            SourceDoc(
                marker=f"S{idx}",
                title=_prettify_stem(f.stem),
                filename=f.name,
                url=None,
                text=text,
                tags=[tag],
            )
        )
        idx += 1
    return docs, idx


def load_company_sources(slug: str) -> List[SourceDoc]:
    """Collect + extract prospect docs (docs/<slug>/) and shared Zoho docs."""
    root = settings.docs_root_path
    sources: list[SourceDoc] = []
    idx = 1

    prospect_docs, idx = _load_folder_docs(root / slug, "prospect", idx)
    sources.extend(prospect_docs)

    zoho_docs, idx = _load_folder_docs(root / _ZOHO_SLUG, "zoho", idx)
    sources.extend(zoho_docs)

    return sources


def load_company_intel(company_name: str, slug: Optional[str] = None) -> List[SourceDoc]:
    """Web-first prospect intel for `company_name` (cached web sources), falling back
    to docs/<slug>/ only when the web returns nothing. Shared Zoho docs are always
    appended. Both the brief engine and Scout use this so they share one prepared
    intel set. Web sources are tagged ["web", …] so provenance shows in citations.
    """
    from app.services import web_sources  # local import keeps module load order simple

    root = settings.docs_root_path
    sources: list[SourceDoc] = []
    idx = 1

    web_docs = web_sources.fetch_intel(company_name) if settings.web_intel_enabled else []
    if web_docs:
        for wd in web_docs:
            sources.append(
                SourceDoc(
                    marker=f"S{idx}",
                    title=f"{wd.source} — {company_name}",
                    filename=None,
                    url=(wd.url or None),
                    text=wd.text,
                    tags=["web", "prospect"],
                )
            )
            idx += 1
    elif slug:  # no web intel — fall back to local prospect docs
        prospect_docs, idx = _load_folder_docs(root / slug, "prospect", idx)
        sources.extend(prospect_docs)

    zoho_docs, idx = _load_folder_docs(root / _ZOHO_SLUG, "zoho", idx)
    sources.extend(zoho_docs)
    return sources
