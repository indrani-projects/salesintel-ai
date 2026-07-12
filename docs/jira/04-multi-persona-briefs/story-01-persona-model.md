# SI-4.1 — Persona model & per-persona section sets

| Field | Value |
|---|---|
| Issue type | Story |
| Parent epic | SI-4 — Multi-Persona Briefs (AE / SDR / SE) |
| Status | Done |
| Priority | High |
| Story points | 3 |
| Component | Personas |
| Labels | backend, data |

## User story
As a backend engineer, I want a single shared definition of the three personas and the exact sections each one gets, so that synthesis, storage, API, and UI all agree on what "an SDR brief" or "an SE brief" actually contains.

## Description
This story establishes the data backbone for multi-persona briefs. It introduces a `Persona` enum with three values — `ae` (Account Executive), `sdr` (Sales Development Rep), and `se` (Solutions Engineer) — into the shared contract module that every layer mirrors. Alongside the enum it defines the human-facing metadata every screen needs: `PERSONA_LABELS` (full-form role names) and `PERSONA_TAGLINES` (a one-line description of what that persona's brief is for).

The heart of the story is `PERSONA_SECTIONS`: an ordered, per-persona map of `(section_id, section_title)` pairs that declares exactly which sections each persona's brief is made of, and in what order. The AE persona reuses the full nine-section business brief (company snapshot, financials, trigger events, GTM model, pain hypotheses, tech stack, stakeholders, risks, recommended angle). The SDR persona gets a short prospecting set (the hook, who to contact, value hypothesis, ready-to-send opener, qualifying questions). The SE persona gets a technical set (current tech stack, integration landscape, technical fit hypotheses, demo focus, likely technical objections, open technical questions). A `sections_for(persona)` helper returns the ordered list for any persona and defaults safely to AE for unknown values.

On the persistence side, the meeting gains a `persona` column recording its primary/selected persona, and the Brief table is re-keyed so there is one Brief row per `(meeting, persona)` pair rather than one per meeting. A unique constraint on `(meeting_id, persona)` enforces that, letting a single meeting accumulate independent AE / SDR / SE briefs that are generated and cached separately. Because this module is the shared contract, its field names are kept identical to the frontend's TypeScript mirror and to the LLM's expected JSON shape.

## Acceptance criteria
```gherkin
Scenario: Persona enum and metadata are defined once and shared
  Given the shared schemas module
  When any layer reads the persona definitions
  Then Persona exposes exactly ae, sdr, and se
  And PERSONA_LABELS maps them to "Account Executive", "Sales Development Rep", and "Solutions Engineer"
  And PERSONA_TAGLINES provides a one-line description for each
```
```gherkin
Scenario: Each persona has its own ordered section set
  Given PERSONA_SECTIONS
  When sections_for("sdr") is requested
  Then it returns the SDR sections in order, including the ready-to-send opener and who-to-contact
  And sections_for("se") returns the SE sections including demo focus and technical objections
  And sections_for("ae") returns the full nine business sections in display order
```
```gherkin
Scenario: One brief row per meeting-persona pair (edge case)
  Given a meeting already has an Account Executive brief row
  When a second brief row is created for the same meeting and the same persona
  Then the unique constraint on (meeting_id, persona) rejects the duplicate
  And an unknown persona value resolves to the Account Executive section set rather than erroring
```

## Technical notes (reference)
- Key files: `backend/app/schemas.py` (Persona enum, PERSONA_LABELS, PERSONA_TAGLINES, PERSONA_SECTIONS, sections_for), `backend/app/models.py` (Meeting.persona, Brief.persona + `uq_brief_meeting_persona` unique constraint).
- `PERSONA_SECTIONS["ae"]` is derived from the existing `SECTION_ORDER` / `SECTION_TITLES` so the AE brief stays identical to the pre-persona brief.
- `BriefContent` and the meeting/brief DTOs carry a `persona` field defaulting to `ae`, keeping the change additive to the shared contract.
- POC note: statuses remain plain strings on the DB models but must match the `BriefStatus` enum values.

## Definition of Done
- [x] `Persona` enum (`ae`/`sdr`/`se`) added to the shared schemas module.
- [x] `PERSONA_LABELS` and `PERSONA_TAGLINES` defined with full-form role names.
- [x] `PERSONA_SECTIONS` ordered section sets defined for AE, SDR, and SE, with `sections_for()` helper defaulting to AE.
- [x] `Meeting.persona` column and per-persona `Brief` rows with a `(meeting_id, persona)` unique constraint.
- [x] `persona` field mirrored on the relevant API DTOs and kept in sync with the frontend types.
