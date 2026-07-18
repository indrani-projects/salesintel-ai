"""Core brief synthesis — persona-aware (AE / SDR / SE).

Loads grounded sources for a prospect, prompts an OpenAI-compatible LLM to produce
a strict-JSON briefing shaped for the chosen rep persona, then parses and validates
into a BriefContent. Guarantees the persona's section set is present, in order.
"""
from __future__ import annotations

import json
import re
from datetime import datetime
from typing import List, Optional, Tuple

from app.config import settings
from app.contracts import SourceDoc
from app.schemas import (
    PERSONA_LABELS,
    BriefContent,
    BriefSection,
    BriefSource,
    Confidence,
    KeyFact,
    sections_for,
)
from app.services.llm_client import get_client, get_model
from app.services.sources import (
    COMPANY_NAMES,
    _display_name,
    load_company_intel,
    resolve_company_slug,
)

_VALID_CONFIDENCE = {c.value for c in Confidence}

_BASE_SYSTEM = (
    "You are a B2B pre-sales intelligence analyst preparing a briefing for a "
    "**Zoho** sales rep about a prospect. Ground EVERY factual claim in the "
    "provided sources using inline `[S#]` markers. Use ONLY the sources — if "
    "something isn't in them, say so rather than inventing it. Flag stale or "
    "low-confidence claims."
)

# Persona-specific framing appended to the system prompt.
_PERSONA_FRAMING = {
    "ae": (
        "The reader is an ACCOUNT EXECUTIVE preparing to run discovery and "
        "advance/close the deal. Give the full business picture and a clear, "
        "synthesized recommended angle. Tailor emphasis to the meeting's why/agenda."
    ),
    "sdr": (
        "The reader is a SALES DEVELOPMENT REP doing COLD OUTBOUND. Their ONLY "
        "goal is to earn a first meeting — NOT to pitch or close. Be brief and "
        "action-oriented. The outreach opener must be copy-paste ready. Do not "
        "write a full sales pitch or deep financial analysis."
    ),
    "se": (
        "The reader is a PRE-SALES SOLUTIONS ENGINEER (technical expert) preparing "
        "for a technical deep-dive / demo. Emphasize the current tech stack, "
        "integration surface, technical fit, and a concrete demo plan. Minimize "
        "generic business narrative; be specific and technical."
    ),
}

# Extra guidance for specific section ids. Sections not listed here are
# self-explanatory from their title.
_SECTION_GUIDANCE = {
    # AE
    "pain_hypotheses": (
        "Map the prospect's concrete situation (growth, retail expansion, "
        "D2C/omnichannel, hiring, funding pressure) to SPECIFIC Zoho "
        "products/modules, citing the `zoho`-tagged sources. Frame each as: "
        "prospect signal -> likely pain -> Zoho product that solves it."
    ),
    "recommended_angle": (
        "YOUR synthesized analyst take — the sharpest way for the rep to open and "
        "steer the meeting given the why/agenda. May connect dots but stay grounded."
    ),
    # SDR
    "hook": (
        "The single sharpest, most recent trigger event that earns a reply — one "
        "or two concrete sentences."
    ),
    "target_contact": (
        "Which role/title to target for cold outbound and WHY them; name specific "
        "people if they appear in the sources."
    ),
    "value_hypothesis": "ONE sentence: why Zoho matters to this prospect right now.",
    "outreach_opener": (
        "Write an ACTUAL outreach message the rep can copy-paste: an email with a "
        "subject line and a 2-3 sentence body referencing the trigger, PLUS a "
        "one-line phone/LinkedIn opener. Personalized, concise, no fluff."
    ),
    "qualifying_questions": (
        "3 sharp questions to qualify and book the meeting, plus a one-line "
        "pre-empt for the 'we already have a CRM' objection."
    ),
    # SE
    "tech_stack": (
        "What the prospect runs today (ecommerce platform, marketplaces, any "
        "inferable CRM/helpdesk/telephony) and the inferred architecture. Note "
        "clearly what is inferred vs explicitly stated in the sources."
    ),
    "integration_landscape": (
        "The systems Zoho must integrate with (ecommerce, marketplaces, "
        "telephony/WhatsApp, POS across stores, ERP) and the integration approach "
        "for each, grounded in the tech signals."
    ),
    "technical_fit": (
        "The technical problems (data fragmentation across channels, no single "
        "customer view, ticket volume at scale) mapped to SPECIFIC Zoho modules "
        "and HOW they'd be configured."
    ),
    "demo_focus": (
        "A tailored demo plan: which Zoho features/flows to show, in what order, "
        "given this prospect's situation (e.g. omnichannel Customer 360, Desk SLAs "
        "for warranty/returns, marketplace sync)."
    ),
    "technical_objections": (
        "Likely technical objections (scale, data migration, customization limits, "
        "data residency, security/compliance) each with a concrete technical response."
    ),
    "open_questions": (
        "Technical discovery questions the SE should ask on the call to close "
        "knowledge gaps (current CRM/helpdesk, data volumes, integration constraints)."
    ),
}


def _section_instructions(persona_sections: List[Tuple[str, str]]) -> str:
    lines = [f'{i}. id="{sid}" — {title}' for i, (sid, title) in enumerate(persona_sections, start=1)]
    guide = "\n".join(lines)
    extras = [
        f'- "{sid}": {_SECTION_GUIDANCE[sid]}'
        for sid, _ in persona_sections
        if sid in _SECTION_GUIDANCE
    ]
    if extras:
        guide += "\n\nSection-specific guidance:\n" + "\n".join(extras)
    return guide


def _build_source_inventory(sources: List[SourceDoc]) -> str:
    lines = []
    for s in sources:
        tag = (s.tags[0] if s.tags else "prospect")
        lines.append(f"[{s.marker}] ({tag}) {s.title} — file: {s.filename}")
    return "\n".join(lines)


def _build_source_corpus(sources: List[SourceDoc]) -> str:
    blocks = []
    for s in sources:
        tag = (s.tags[0] if s.tags else "prospect")
        blocks.append(
            f"===== SOURCE {s.marker} | tag={tag} | title={s.title} | "
            f"file={s.filename} =====\n{s.text}"
        )
    return "\n\n".join(blocks)


def _user_prompt(
    company: str,
    subject: str,
    why: str,
    agenda: str,
    sources: List[SourceDoc],
    persona_sections: List[Tuple[str, str]],
) -> str:
    inventory = _build_source_inventory(sources)
    corpus = _build_source_corpus(sources)
    n = len(persona_sections)
    first_id, first_title = persona_sections[0]
    ids = ", ".join(sid for sid, _ in persona_sections)
    json_shape = (
        '{\n'
        '  "headline": "one-line TL;DR",\n'
        '  "key_facts": [ {"label": "ARR", "value": "₹700 Cr", "note": "60% YoY"} ],\n'
        '  "sections": [\n'
        f'    {{"id": "{first_id}", "title": "{first_title}", '
        '"content_md": "markdown with inline [S#] citations", '
        '"confidence": "high|medium|low", "flags": ["optional notes"]}\n'
        f'    // ... all {n} sections, in the exact order listed above\n'
        '  ],\n'
        '  "sources": [\n'
        '    {"marker": "S1", "title": "...", "filename": "...", "url": null}\n'
        '  ]\n'
        '}'
    )
    return (
        f"PROSPECT COMPANY: {company}\n"
        f"MEETING SUBJECT: {subject or '(not specified)'}\n"
        f"WHY THIS MEETING: {why or '(not specified)'}\n"
        f"AGENDA: {agenda or '(not specified)'}\n\n"
        f"Produce a briefing with EXACTLY these {n} sections, in this order:\n"
        f"{_section_instructions(persona_sections)}\n\n"
        "SOURCE INVENTORY (cite these markers inline as [S#]):\n"
        f"{inventory}\n\n"
        "FULL SOURCE TEXT:\n"
        f"{corpus}\n\n"
        "Return STRICT JSON only (no prose, no code fences) with this shape:\n"
        f"{json_shape}\n\n"
        f"Rules: every section id must be one of: {ids}; include ALL {n}; every "
        'factual claim needs an inline [S#] marker; set confidence to "low" '
        "(and add a flag) for anything stale, thin, or inferred; list the sources "
        'you actually used in "sources". Also include 3-5 "key_facts" — the '
        "headline metrics a rep wants at a glance (e.g. revenue/ARR, latest funding, "
        "retail/scale, growth rate, offline mix): short label + short value, grounded."
    )


def _strip_fences(raw: str) -> str:
    raw = raw.strip()
    if raw.startswith("```"):
        raw = re.sub(r"^```[a-zA-Z0-9]*\s*", "", raw)
        raw = re.sub(r"\s*```$", "", raw)
    return raw.strip()


def _coerce_confidence(value) -> Confidence:
    if isinstance(value, str) and value.strip().lower() in _VALID_CONFIDENCE:
        return Confidence(value.strip().lower())
    return Confidence.medium


def _coerce_flags(value) -> list[str]:
    if isinstance(value, list):
        return [str(x) for x in value if str(x).strip()]
    if isinstance(value, str) and value.strip():
        return [value.strip()]
    return []


def _placeholder_section(sid: str, title: str) -> BriefSection:
    return BriefSection(
        id=sid,
        title=title,
        content_md=(
            "_No grounded information was produced for this section from the "
            "available sources. Verify before use._"
        ),
        confidence=Confidence.low,
        flags=["verify before use"],
    )


def _sources_from_docs(sources: List[SourceDoc]) -> list[BriefSource]:
    return [
        BriefSource(marker=s.marker, title=s.title, filename=s.filename, url=s.url)
        for s in sources
    ]


def _parse_brief(
    raw: str,
    company: str,
    company_slug: str,
    persona: str,
    persona_sections: List[Tuple[str, str]],
    fallback_sources: List[SourceDoc],
) -> BriefContent:
    data = json.loads(_strip_fences(raw))
    if not isinstance(data, dict):
        raise ValueError("Top-level JSON is not an object")

    headline = str(data.get("headline", "") or "")
    title_by_id = {sid: title for sid, title in persona_sections}

    # Index whatever sections the model returned (only valid ids for this persona).
    returned: dict[str, BriefSection] = {}
    for item in data.get("sections", []) or []:
        if not isinstance(item, dict):
            continue
        sid = str(item.get("id", "")).strip()
        if sid not in title_by_id:
            continue
        returned[sid] = BriefSection(
            id=sid,
            title=str(item.get("title") or title_by_id[sid]),
            content_md=str(item.get("content_md", "") or ""),
            confidence=_coerce_confidence(item.get("confidence")),
            flags=_coerce_flags(item.get("flags")),
        )

    # Guarantee the persona's full section set, in order.
    sections: list[BriefSection] = []
    for sid, title in persona_sections:
        sec = returned.get(sid)
        if sec is None or not sec.content_md.strip():
            sections.append(_placeholder_section(sid, title))
        else:
            sections.append(sec)

    # Sources: prefer model-declared, else fall back to the loaded inventory.
    parsed_sources: list[BriefSource] = []
    for item in data.get("sources", []) or []:
        if not isinstance(item, dict):
            continue
        marker = str(item.get("marker", "")).strip()
        if not marker:
            continue
        parsed_sources.append(
            BriefSource(
                marker=marker,
                title=str(item.get("title") or marker),
                filename=item.get("filename"),
                url=item.get("url"),
            )
        )
    if not parsed_sources:
        parsed_sources = _sources_from_docs(fallback_sources)

    key_facts: list[KeyFact] = []
    for item in data.get("key_facts", []) or []:
        if not isinstance(item, dict):
            continue
        label = str(item.get("label", "")).strip()
        value = str(item.get("value", "")).strip()
        if not label or not value:
            continue
        note = item.get("note")
        key_facts.append(KeyFact(label=label, value=value, note=str(note) if note else None))

    return BriefContent(
        company=company,
        company_slug=company_slug,
        persona=persona,
        headline=headline,
        key_facts=key_facts[:5],
        sections=sections,
        sources=parsed_sources,
        generated_at=datetime.utcnow(),
    )


# Gemini flash models "think" by default, which is very slow over large context
# (~458s). reasoning_effort="low" caps thinking and cuts generation to ~35-60s with
# no meaningful quality loss for this grounded-synthesis task.
_REASONING_EFFORT = "low"


def _call_llm(system: str, user: str) -> str:
    client = get_client()
    model = get_model()
    messages = [
        {"role": "system", "content": system},
        {"role": "user", "content": user},
    ]
    try:
        resp = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=0.2,
            response_format={"type": "json_object"},
            reasoning_effort=_REASONING_EFFORT,
        )
    except Exception:
        # Lite / non-thinking models may reject reasoning_effort — keep JSON mode.
        try:
            resp = client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=0.2,
                response_format={"type": "json_object"},
            )
        except Exception:
            # Last resort: plain call (some providers reject response_format too).
            resp = client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=0.2,
            )
    return resp.choices[0].message.content or ""


def _mock_brief(company, company_slug, persona, persona_sections, sources) -> BriefContent:
    """Deterministic brief for MOCK_LLM mode (tests / Playwright)."""
    srcs = _sources_from_docs(sources) or [BriefSource(marker="S1", title="Mock source")]
    sections = [
        BriefSection(
            id=sid,
            title=title,
            content_md=f"Mock **{title}** for {company}, grounded in the sources [S1].",
            confidence=Confidence.high,
            flags=[],
        )
        for sid, title in persona_sections
    ]
    return BriefContent(
        company=company,
        company_slug=company_slug,
        persona=persona,
        headline=f"Mock brief for {company} — {PERSONA_LABELS.get(persona, persona)} view.",
        key_facts=[
            KeyFact(label="ARR", value="₹700 Cr", note="60% YoY"),
            KeyFact(label="Last raise", value="₹480 Cr", note="Series D"),
            KeyFact(label="Retail outlets", value="150+", note="45+ cities"),
            KeyFact(label="Offline mix", value="70%", note="of sales"),
        ],
        sections=sections,
        sources=srcs,
        generated_at=datetime.utcnow(),
    )


def _slugify(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", (name or "").lower()).strip("_") or "prospect"


def generate_brief(
    company_slug: Optional[str],
    subject: str,
    why: str,
    agenda: str,
    persona: str = "ae",
    company_name: Optional[str] = None,
) -> BriefContent:
    persona = persona if persona in PERSONA_LABELS else "ae"
    slug = resolve_company_slug(company_slug) if company_slug else None
    # Display name: prefer the meeting's free-text company (handles unknown companies
    # with no docs folder), else the slug-derived name.
    if company_name:
        company = company_name
    elif slug:
        company = COMPANY_NAMES.get(slug) or _display_name(slug)
    else:
        company = _display_name(company_slug) if company_slug else "Prospect"
    slug = slug or _slugify(company)
    persona_sections = sections_for(persona)

    # Web-first intel by company NAME (cached), falling back to docs/<slug>/.
    sources = load_company_intel(company, slug)

    if settings.mock_llm:
        return _mock_brief(company, slug, persona, persona_sections, sources)
    system = _BASE_SYSTEM + "\n\n" + _PERSONA_FRAMING.get(persona, _PERSONA_FRAMING["ae"])
    user = _user_prompt(company, subject, why, agenda, sources, persona_sections)

    last_err: Optional[Exception] = None
    for _ in range(2):  # initial attempt + one retry on parse/validation error
        raw = _call_llm(system, user)
        try:
            return _parse_brief(raw, company, slug, persona, persona_sections, sources)
        except Exception as e:  # noqa: BLE001 - retry on any parse/validation issue
            last_err = e
            continue

    raise RuntimeError(f"Failed to generate a valid brief: {last_err}")
