# SI-4.2 — Persona-tailored synthesis & signature sections

| Field | Value |
|---|---|
| Issue type | Story |
| Parent epic | SI-4 — Multi-Persona Briefs (AE / SDR / SE) |
| Status | Done |
| Priority | High |
| Story points | 8 |
| Component | Personas |
| Labels | backend, ai, llm |

## User story
As a sales rep in a specific role, I want the brief to be synthesized for how I actually work — a prospecting opener if I'm an SDR, a demo plan if I'm an SE, a recommended angle if I'm an AE — so that I get a usable artifact for my next action, not a generic summary re-labelled with my title.

## Description
This story makes persona a genuine input to the synthesis engine rather than a cosmetic tag. `generate_brief(persona)` now selects the persona's section set, injects a persona-specific framing into the system prompt, and asks the LLM for exactly that persona's sections in order, with per-section guidance so each signature section is produced correctly. The base analyst instruction (ground every claim in the provided sources with inline `[S#]` citations, use only the sources, flag stale/low-confidence claims) is preserved for all personas; the persona framing is appended on top.

The three framings steer emphasis in materially different directions. The **AE** framing asks for the full business picture and a sharp, synthesized recommended angle tuned to the meeting's why/agenda — its signature outputs are the recommended angle and the key stakeholders. The **SDR** framing constrains the model to cold-outbound only: be brief and action-oriented, do not pitch or write deep financial analysis, and produce a copy-paste-ready outreach opener (an email with subject and a 2–3 sentence trigger-referencing body, plus a one-line phone/LinkedIn opener) together with an explicit target contact (which role/title to approach and why, naming specific people when the sources contain them). The **SE** framing asks for a technical-fit brief centred on the current tech stack, integration landscape, and a concrete demo focus/plan — which Zoho features to show and in what order — plus the likely technical objections (scale, migration, customization limits, data residency, security) each paired with a concrete technical response.

The parsing and validation path is persona-aware and defensive. Only section ids valid for the requested persona are accepted from the model output; the persona's full ordered section set is then guaranteed, with any missing or empty section replaced by a low-confidence "verify before use" placeholder. Confidence values and flags are coerced, code fences are stripped, sources fall back to the loaded inventory when the model omits them, and key facts are captured for the at-a-glance strip. A one-shot retry covers transient parse/validation failures, and a MOCK_LLM mode returns a deterministic persona-shaped brief for tests and Playwright runs. As a deliberate POC shortcut, all source text is still concatenated into a single LLM call.

## Acceptance criteria
```gherkin
Scenario: SDR synthesis produces a ready-to-send opener and a target contact
  Given a prospect with a recent trigger event in the sources
  When generate_brief is called with persona "sdr"
  Then the brief contains a "Ready-to-Send Opener" section with a subject line and a short trigger-referencing body
  And it contains a "Who to Contact" section naming the role/title to approach
  And it does not include deep financial analysis sections
```
```gherkin
Scenario: SE synthesis produces a demo focus and technical objections
  Given a prospect with inferable tech-stack signals in the sources
  When generate_brief is called with persona "se"
  Then the brief contains a "Demo Focus — What to Show" section with an ordered demo plan
  And a "Likely Technical Objections" section pairing each objection with a concrete response
```
```gherkin
Scenario: AE synthesis leads with a recommended angle tuned to the agenda
  Given a meeting whose agenda emphasizes scaling support
  When generate_brief is called with persona "ae"
  Then the brief includes an "Analyst's Recommended Angle" section and a "Key Stakeholders" section
  And the emphasis reflects the meeting's why/agenda
```
```gherkin
Scenario: Missing or malformed persona sections degrade safely (edge case)
  Given the LLM omits a required section or returns an id not valid for the persona
  When the output is parsed
  Then the invalid id is discarded and the missing section becomes a low-confidence "verify before use" placeholder
  And the persona's full section set is still returned in order
```

## Technical notes (reference)
- Key file: `backend/app/services/brief_engine.py` — `generate_brief(company_slug, subject, why, agenda, persona)`, `_PERSONA_FRAMING`, `_SECTION_GUIDANCE`, `_section_instructions`, `_parse_brief`, `_mock_brief`.
- Section-specific guidance drives the signature sections: SDR `outreach_opener` / `target_contact`, SE `demo_focus` / `technical_objections`, AE `recommended_angle` / `pain_hypotheses`.
- LLM call uses `reasoning_effort="low"` with `response_format=json_object` and falls back progressively if the endpoint rejects those params; a one-shot retry covers parse/validation errors.
- POC shortcut: all source text is stuffed into one LLM call (no vector DB); unknown personas default to AE framing and sections.

## Definition of Done
- [x] `generate_brief` accepts a `persona` argument and selects the persona's section set.
- [x] AE / SDR / SE system-prompt framings implemented and appended to the base analyst prompt.
- [x] SDR outreach opener + target contact, SE demo focus + technical objections, and AE recommended angle + stakeholders produced via per-section guidance.
- [x] Persona-aware defensive parsing guarantees the full ordered section set with low-confidence placeholders for gaps.
- [x] MOCK_LLM path returns a deterministic persona-shaped brief; one-shot retry on parse failure.
