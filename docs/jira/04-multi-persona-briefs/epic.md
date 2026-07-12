# EPIC SI-4 — Multi-Persona Briefs (AE / SDR / SE)

| Field | Value |
|---|---|
| Issue type | Epic |
| Suggested key | SI-4 |
| Status | Done |
| Priority | High |
| Component | Personas |
| Labels | backend, frontend, ai, llm, api, data, ux |
| Story points (rollup) | 21 |

## Summary
One prospect, three sales-role lenses: the same company can be briefed for an Account Executive, a Sales Development Rep, or a Solutions Engineer, each getting a persona-tailored brief with distinct emphasis and its own signature sections.

## Description
SalesIntel AI already turns external prospect signal and internal Zoho product knowledge into a grounded, cited pre-sales briefing. But a briefing that is perfect for an Account Executive running discovery is the wrong artifact for an SDR writing a cold opener, or for a Solutions Engineer prepping a technical demo. Each role reads for different things, acts on different next steps, and wants a different shape of document. This epic makes the persona a first-class dimension of a brief so the same prospect research is re-synthesized — not just re-labelled — for the role that is actually reading it.

Three personas are supported. The **Account Executive (AE)** gets the full nine-section business brief whose headline sections are the recommended angle and the key stakeholders. The **Sales Development Rep (SDR)** gets a short prospecting brief whose signature output is a copy-paste-ready outreach opener plus the exact target contact to approach. The **Solutions Engineer (SE)** gets a technical-fit brief whose signature output is a concrete demo focus/plan plus the likely technical objections and how to answer them. Each persona has its own ordered set of sections, its own label and tagline, and its own LLM framing so emphasis genuinely shifts between roles.

Persona is chosen when a meeting is created (the "primary" persona) and can be switched on the brief itself via a "View as AE / SDR / SE" toggle. Generation is deliberately lazy to respect free-tier LLM limits: the primary persona's brief is synthesized immediately on meeting create, and the other two personas are generated on first view of that toggle. Persistence stores one Brief row per (meeting, persona) pair, so a fully-explored meeting ends up with three independently-generated, independently-cached briefs. The API is persona-scoped end to end — `GET brief?persona=` and `regenerate?persona=` — and the frontend polls per persona so switching roles shows a live "generating" state that flips to "ready" without a page reload.

This is a POC, so the usual deliberate shortcuts still apply: all source text is stuffed into one LLM call (no vector DB) and sources come from a local `docs/` folder rather than live scraping. Persona support is layered cleanly on top of that existing single-call synthesis pipeline rather than changing it.

## Stories in this epic
| Key | Story | Points | Priority |
|---|---|---|---|
| SI-4.1 | Persona model & per-persona section sets | 3 | High |
| SI-4.2 | Persona-tailored synthesis & signature sections | 8 | High |
| SI-4.3 | Lazy per-persona generation & persona-scoped API | 5 | High |
| SI-4.4 | Persona selector, "View as" toggle & badges | 5 | Medium |

## Epic acceptance criteria
```gherkin
Scenario: The same prospect yields three role-specific briefs
  Given a meeting exists for "The Sleep Company"
  When the brief is viewed as an Account Executive, then as a Sales Development Rep, then as a Solutions Engineer
  Then each persona shows its own ordered section set
  And the SDR brief includes a copy-paste outreach opener and a target contact
  And the SE brief includes a demo focus and likely technical objections
  And the AE brief leads with a recommended angle and key stakeholders
```
```gherkin
Scenario: Lazy generation keeps LLM usage minimal
  Given a meeting is created with Account Executive as its primary persona
  When the meeting is saved
  Then only the Account Executive brief is generated immediately
  And the SDR and SE briefs are generated only when their persona is first viewed
```
```gherkin
Scenario: Persona is visible and switchable across the UI
  Given a meeting with a chosen primary persona
  When the rep views the dashboard and the brief
  Then a full-form persona label/badge is shown on the dashboard card and the brief header
  And a "View as AE / SDR / SE" toggle switches the viewed persona with per-persona polling
```

## Out of scope
- Custom or user-defined personas beyond AE / SDR / SE.
- Cross-persona diffing or a combined "all personas" export.
- Per-persona chatbot (Scout) tuning — chat remains shared across personas.
- Vector retrieval or per-persona source selection (all personas share the single-call corpus).

## Dependencies
- Depends on the base brief-generation pipeline (sources → ingestion → brief_engine → brief_render) and the async brief lifecycle state machine.
- Shares the `schemas.py` / `frontend/src/api/types.ts` contract seam; persona fields are additive to those DTOs.
