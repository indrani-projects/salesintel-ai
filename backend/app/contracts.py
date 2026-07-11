"""
Service interface contract (Phase-0, Lead-authored).

Defines the EXACT function signatures the Backend Agent imports and the AI-Engine
Agent implements. Both agents must honor these names/signatures so integration is
a no-op. The stub bodies live in app/services/* and raise NotImplementedError
until the AI-Engine Agent implements them.

Backend orchestration (BackgroundTasks) calls:
    from app.services.sources import list_companies, resolve_company_slug, load_company_sources
    from app.services.brief_engine import generate_brief
    from app.services.brief_render import render_html
    from app.services.chat_service import answer_question

Signatures:

    list_companies() -> list[CompanyRead]
        Scan DOCS_ROOT for company folders (excluding "zoho"); return dropdown list.

    resolve_company_slug(name_or_slug: str) -> str | None
        Map a free-text company name (from the meeting) to a docs/<slug> folder.

    load_company_sources(slug: str) -> list[SourceDoc]
        Extract + cache text from every doc under docs/<slug>/ (+ the shared
        docs/zoho/ knowledge). Returns SourceDoc(marker, title, filename, url, text).

    generate_brief(company_slug: str, subject: str, why: str, agenda: str) -> BriefContent
        The core synthesis. Loads sources, calls the LLM with the 9-section grounded
        prompt tailored to why/agenda, returns a validated BriefContent.

    render_html(brief: BriefContent) -> str
        Render BriefContent → styled, self-contained HTML (for the brief view +
        client-side PDF export).

    answer_question(company_slug, brief, history, question) -> ChatResponse
        Grounded follow-up Q&A over the brief + source docs. Declines gracefully
        ("not in the sources") when unsupported.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class SourceDoc:
    """Internal representation of one ingested source document."""
    marker: str                # "S1", "S2", ...
    title: str
    filename: Optional[str] = None
    url: Optional[str] = None
    text: str = ""
    tags: List[str] = field(default_factory=list)  # e.g. ["prospect"] or ["zoho"]
