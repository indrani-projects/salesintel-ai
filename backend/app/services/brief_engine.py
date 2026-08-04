"""Core brief synthesis — persona-aware (the six Persona values in schemas.py:
Sales Rep, Sales Manager, Enablement, RevOps, VP of Sales, Admin).

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
    DEFAULT_PERSONA,
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
    display_name,
    load_company_intel,
    resolve_company_slug,
)
from app.services.textutil import strip_fences

_VALID_CONFIDENCE = {c.value for c in Confidence}

_BASE_SYSTEM = (
    "You are a B2B pre-sales intelligence analyst preparing a briefing for a "
    "**Zoho** sales rep about a prospect. Ground EVERY factual claim in the "
    "provided sources using inline `[S#]` markers. Use ONLY the sources — if "
    "something isn't in them, say so rather than inventing it. Flag stale or "
    "low-confidence claims."
)

# Persona-specific framing appended to the system prompt. Keyed by the six personas
# in docs/shared/Expected_Features_By_Persona.
_PERSONA_FRAMING = {
    "sales_rep": (
        "The reader is a SALES REPRESENTATIVE preparing to run a customer meeting. "
        "Give the full business picture and a clear, synthesized recommended angle. "
        "Tailor emphasis to the meeting's why/agenda so they can prepare fast."
    ),
    "sales_manager": (
        "The reader is a SALES MANAGER who will COACH the rep on this deal, not run "
        "the meeting themselves. Focus on where to guide the rep, the deal risks to "
        "inspect, and the questions the manager should ask the rep. Be direct and "
        "coaching-oriented; aim at improving win rates."
    ),
    "enablement": (
        "The reader is a SALES ENABLEMENT lead using this brief as a BEST-PRACTICE, "
        "teachable example to standardize how reps prepare. Emphasize repeatable prep "
        "steps, talking points, objection handling, and a readiness checklist a newly "
        "onboarded rep could follow."
    ),
    "revops": (
        "The reader is a REVENUE OPERATIONS MANAGER focused on adoption, process, and "
        "ROI — not meeting tactics. Emphasize CRM data health/gaps, workflow fit, "
        "automation opportunities, and a measurable ROI and adoption angle."
    ),
    "vp_sales": (
        "The reader is a VP OF SALES who needs the executive, board-level view. Be "
        "concise and outcome-oriented: strategic fit, revenue opportunity, win "
        "probability, competitive dynamics, and a crisp executive recommendation. "
        "Omit tactical minutiae."
    ),
    "admin": (
        "The reader is the SALESINTEL AI ADMIN responsible for platform reliability "
        "and data governance. This brief is a DATA-PROVENANCE view, NOT a sales pitch: "
        "inventory the [S#] sources that fed the brief and their type/tags, trace key "
        "facts back to their sources, and flag coverage gaps, stale data, "
        "integration/field-mapping issues, and quality risks."
    ),
}

# Extra guidance for specific section ids. Sections not listed here are
# self-explanatory from their title.
_SECTION_GUIDANCE = {
    # --- Sales Representative (full brief) ---
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
    "tech_stack": (
        "What the prospect runs today (ecommerce platform, marketplaces, any "
        "inferable CRM/helpdesk/telephony) and the inferred architecture. Note "
        "clearly what is inferred vs explicitly stated in the sources."
    ),
    # --- Sales Manager (coaching) ---
    "coaching_focus": (
        "Where the manager should coach the rep for THIS deal: the two or three "
        "skills/moves that most change the outcome (discovery depth, multithreading, "
        "value framing), tied to concrete signals in the sources."
    ),
    "deal_risks": (
        "The risks a manager should inspect: single-threaded, weak champion, "
        "budget/timing, competitor incumbency — each with what to check."
    ),
    "rep_questions": (
        "Specific questions the manager should ask the rep in a 1:1 deal review to "
        "expose gaps and next steps."
    ),
    "next_steps": "The concrete next actions to drive the deal forward, in priority order.",
    # --- Sales Enablement (best practice / onboarding) ---
    "best_practice_prep": (
        "The repeatable prep steps a rep should follow before a meeting like this — "
        "written so a newly onboarded rep could copy the process."
    ),
    "talking_points": "The 3-5 highest-leverage talking points, each grounded in a source.",
    "objection_handling": (
        "Likely objections (price, incumbent tool, switching cost) each with a crisp, "
        "on-message response the team can standardize on."
    ),
    "playbook_alignment": (
        "How this opportunity maps to the standard sales play / messaging pillars, so "
        "prep stays consistent across reps."
    ),
    "readiness_checklist": (
        "A short pre-meeting readiness checklist (research done, stakeholders "
        "identified, materials ready) the rep can tick off."
    ),
    # --- Revenue Operations Manager (adoption / ROI) ---
    "data_health": (
        "Gaps and quality issues in the account data available (missing firmographics, "
        "stale signals, unverified claims) and what CRM fields would need to be filled."
    ),
    "process_fit": (
        "Where Zoho fits the prospect's operating processes and workflows, and where "
        "process change or integration is required."
    ),
    "automation_opportunities": (
        "Concrete workflows that could be automated (lead routing, approvals, renewals) "
        "mapped to Zoho capabilities, citing sources."
    ),
    "roi_hypothesis": (
        "A measurable ROI hypothesis: the cost/efficiency lever, a rough magnitude, and "
        "the metric that would prove it — grounded, clearly labelled as an estimate."
    ),
    "adoption_angle": (
        "How to drive adoption and land-and-expand for this account (which team first, "
        "rollout sequence, governance)."
    ),
    # --- VP of Sales (executive) ---
    "strategic_fit": "Why this account matters strategically (segment, expansion, reference value).",
    "revenue_opportunity": (
        "The revenue opportunity: deal size band and expansion potential, clearly "
        "labelled as an estimate where inferred."
    ),
    "win_risk": "Win probability drivers and the top risks to the number, concisely.",
    "competitive_landscape": (
        "Incumbent/competitor tools in play and Zoho's displacement wedge, grounded in "
        "the sources."
    ),
    "exec_recommendation": (
        "A crisp executive recommendation: pursue/support level, the one thing that "
        "must go right, and the ask."
    ),
    # --- SalesIntel AI Admin (data provenance / quality) ---
    "source_inventory": (
        "Inventory the [S#] sources that fed this brief: for each, its title, type/tag "
        "(web/prospect/zoho/prepared), and URL/file if present. Note relative "
        "trustworthiness (official/regulatory/press vs forum/blog)."
    ),
    "data_lineage": (
        "Trace the brief's key factual claims back to the specific [S#] source(s) that "
        "support them, so each fact is auditable."
    ),
    "coverage_gaps": (
        "What's missing or thin: source types not present (e.g. no financial filing, no "
        "official site), unverified claims, and single-sourced facts."
    ),
    "data_freshness": (
        "How current the underlying signals appear (recent news vs undated pages) and "
        "any staleness to flag."
    ),
    "integration_status": (
        "Which channels/integrations supplied data (web feeds, prepared docs, local "
        "docs) and any field-mapping/coverage issues an admin should address."
    ),
    "quality_flags": (
        "Concrete quality/governance flags: low-credibility sources relied on, possible "
        "entity mismatches, and anything that should be reviewed before the brief is "
        "trusted."
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
        ref = s.url or s.filename or ""  # show the web URL, not the internal cache file
        lines.append(f"[{s.marker}] ({tag}) {s.title}" + (f" — {ref}" if ref else ""))
    return "\n".join(lines)


def _build_source_corpus(sources: List[SourceDoc]) -> str:
    blocks = []
    for s in sources:
        tag = (s.tags[0] if s.tags else "prospect")
        blocks.append(
            f"===== SOURCE {s.marker} | tag={tag} | title={s.title} | "
            f"src={s.url or s.filename or ''} =====\n{s.text}"
        )
    return "\n\n".join(blocks)


def _is_web_source(doc: SourceDoc) -> bool:
    """A web/prepared source — surface its URL, not the internal cache `.md` filename."""
    tags = doc.tags or []
    return bool(doc.url or "web" in tags or "prepared" in tags)


def _display_filename(doc: SourceDoc) -> Optional[str]:
    """What to show as a source's file reference. Web/prepared sources surface their URL
    instead (return None). For local docs, keep a real document name (a PDF under
    docs/<company>/) but hide bare `.md` files — those are internal/dev artifacts (e.g.
    the Zoho knowledge sheet, the prepared cache), never a user-facing reference."""
    if _is_web_source(doc):
        return None
    fn = doc.filename
    if fn and fn.lower().endswith(".md"):
        return None
    return fn


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
        BriefSource(marker=s.marker, title=s.title, filename=_display_filename(s), url=s.url)
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
    data = json.loads(strip_fences(raw))
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

    # Sources: keep the model's marker + title, but ALWAYS take url + filename from the
    # real loaded inventory (the model is never shown URLs, and the cache `.md` filename
    # is an internal artifact — web sources must surface the link, not the file).
    by_marker = {d.marker: d for d in fallback_sources}
    parsed_sources: list[BriefSource] = []
    for item in data.get("sources", []) or []:
        if not isinstance(item, dict):
            continue
        marker = str(item.get("marker", "")).strip()
        if not marker:
            continue
        doc = by_marker.get(marker)
        if doc is not None:
            parsed_sources.append(
                BriefSource(
                    marker=marker,
                    title=str(item.get("title") or doc.title),
                    filename=_display_filename(doc),
                    url=doc.url,
                )
            )
        else:
            # A marker the model invented (not in the inventory) — trust the title only,
            # never a stray `.md` filename.
            parsed_sources.append(
                BriefSource(
                    marker=marker,
                    title=str(item.get("title") or marker),
                    filename=None,
                    url=item.get("url") or None,
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
    persona: str = DEFAULT_PERSONA,
    company_name: Optional[str] = None,
) -> BriefContent:
    persona = persona if persona in PERSONA_LABELS else DEFAULT_PERSONA
    slug = resolve_company_slug(company_slug) if company_slug else None
    # Display name: prefer the meeting's free-text company (handles unknown companies
    # with no docs folder), else the slug-derived name.
    if company_name:
        company = company_name
    elif slug:
        company = COMPANY_NAMES.get(slug) or display_name(slug)
    else:
        company = display_name(company_slug) if company_slug else "Prospect"
    slug = slug or _slugify(company)
    persona_sections = sections_for(persona)

    # Web-first intel by company NAME (cached), falling back to docs/<slug>/.
    sources = load_company_intel(company, slug)

    if settings.mock_llm:
        return _mock_brief(company, slug, persona, persona_sections, sources)
    system = _BASE_SYSTEM + "\n\n" + _PERSONA_FRAMING.get(persona, _PERSONA_FRAMING[DEFAULT_PERSONA])
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
