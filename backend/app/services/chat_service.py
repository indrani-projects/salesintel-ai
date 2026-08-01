"""Grounded follow-up Q&A over a brief + its sources (AI-Engine Agent, Epic E5).

Answers ONLY from the generated brief and the freshly-loaded source docs, citing
[S#] markers. Sets grounded=False and declines gracefully when unsupported.
"""
from __future__ import annotations

import json
import re
from typing import List

from app.config import settings
from app.contracts import SourceDoc
from app.schemas import (
    BriefContent,
    BriefSource,
    ChatMessageRead,
    ChatResponse,
)
from app.services.llm_client import get_client, get_model
from app.services.sources import load_company_intel
from app.services.textutil import MAX_DOC_CHARS, strip_fences

SYSTEM_PROMPT = (
    "You are a grounded pre-sales assistant answering a Zoho sales rep's follow-up "
    "questions about a prospect. Answer ONLY from the provided brief and sources; "
    "cite `[S#]` markers for every claim. If the answer isn't supported by the "
    "brief or sources, set grounded=false and say it's not in the available "
    "sources rather than guessing."
)

# Keep chat context lean relative to brief generation.
_MAX_HISTORY = 10


def _brief_context(brief: BriefContent) -> str:
    parts = [f"BRIEF HEADLINE: {brief.headline}"]
    for sec in brief.sections:
        parts.append(f"\n## {sec.title} ({sec.id})\n{sec.content_md}")
    return "\n".join(parts)


def _source_context(sources: List[SourceDoc]) -> str:
    blocks = []
    for s in sources:
        tag = (s.tags[0] if s.tags else "prospect")
        text = s.text[:MAX_DOC_CHARS]
        blocks.append(
            f"===== SOURCE {s.marker} | tag={tag} | title={s.title} | "
            f"file={s.filename} =====\n{text}"
        )
    return "\n\n".join(blocks)


def _referenced_markers(text: str) -> set[str]:
    return set(re.findall(r"\[(S\d+)\]", text or ""))


def _citations_for(
    answer_md: str,
    brief: BriefContent,
) -> list[BriefSource]:
    markers = _referenced_markers(answer_md)
    if markers:
        matched = [s for s in brief.sources if s.marker in markers]
        if matched:
            return matched
    return list(brief.sources)


def answer_question(
    company_slug: str,
    brief: BriefContent,
    history: List[ChatMessageRead],
    question: str,
) -> ChatResponse:
    if settings.mock_llm:
        q = (question or "").lower()
        if any(w in q for w in ("color", "colour", "favourite", "favorite")):
            return ChatResponse(
                answer_md="That is not in the sources for this account.",
                citations=[],
                grounded=False,
            )
        return ChatResponse(
            answer_md="Mock grounded answer [S1].",
            citations=list(brief.sources[:1]),
            grounded=True,
        )

    # Web-first intel by the brief's company name (cached — no re-fetch per turn),
    # falling back to docs/<slug>/. Same prepared intel the brief used.
    sources = load_company_intel(getattr(brief, "company", "") or company_slug, company_slug)

    context = (
        "=== BRIEF ===\n"
        f"{_brief_context(brief)}\n\n"
        "=== SOURCE DOCUMENTS ===\n"
        f"{_source_context(sources)}\n\n"
        "Answer the user's question using ONLY the brief and sources above. "
        "Return STRICT JSON only (no code fences) with this shape:\n"
        '{"answer_md": "markdown answer with inline [S#] citations", '
        '"grounded": true}\n'
        "Set grounded=false if the question cannot be answered from the material."
    )

    messages: list[dict] = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "system", "content": context},
    ]
    for msg in (history or [])[-_MAX_HISTORY:]:
        role = "assistant" if msg.role == "assistant" else "user"
        messages.append({"role": role, "content": msg.content})
    messages.append({"role": "user", "content": question})

    client = get_client()
    model = get_model()
    try:
        resp = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=0.2,
            response_format={"type": "json_object"},
            reasoning_effort="low",
        )
    except Exception:
        resp = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=0.2,
        )
    raw = resp.choices[0].message.content or ""

    answer_md = ""
    grounded = True
    try:
        data = json.loads(strip_fences(raw))
        if isinstance(data, dict):
            answer_md = str(data.get("answer_md", "") or "")
            grounded = bool(data.get("grounded", True))
        else:
            answer_md = raw.strip()
    except Exception:
        # Not JSON — treat the raw text as the answer.
        answer_md = strip_fences(raw)

    if not answer_md.strip():
        answer_md = "That isn't covered by the available sources."
        grounded = False

    citations = _citations_for(answer_md, brief)
    return ChatResponse(answer_md=answer_md, citations=citations, grounded=grounded)
