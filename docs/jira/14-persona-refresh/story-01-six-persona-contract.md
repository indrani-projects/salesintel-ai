# SI-14.1 — Six-persona contract, section sets & default

| Field | Value |
|---|---|
| Issue type | Story |
| Parent epic | SI-14 — Persona Refresh: the six personas from the persona doc (supersedes SI-4) |
| Status | Done |
| Priority | High |
| Story points | 3 |
| Component | Personas |
| Labels | backend, data |

## User story
As a backend engineer, I want a single shared definition of the six personas from the persona doc and the exact sections each one gets, so that synthesis, storage, API, and UI all agree on what "a VP of Sales brief" or "an Admin brief" actually contains.

## Description
This story replaces the three-persona backbone from SI-4 with the six canonical personas defined in `docs/shared/Expected_Features_By_Persona.docx.pdf`. It rewrites the `Persona` enum in the shared contract module to expose exactly six values — `sales_rep`, `sales_manager`, `enablement`, `revops`, `vp_sales`, and `admin` — and along with it the human-facing metadata every screen needs: `PERSONA_LABELS` (full-form role names) and `PERSONA_TAGLINES` (a one-line description of what that persona's brief is for, e.g. the Sales Representative's "Prepare fast for every customer meeting.").

The heart of the story is `PERSONA_SECTIONS`: an ordered, per-persona map of `(section_id, section_title)` pairs that declares exactly which sections each persona's brief is made of, and in what order. The **Sales Representative** reuses the full nine-section pre-meeting brief unchanged (it is the old Account Executive brief). The **Sales Manager** gets a coaching set (deal snapshot, coaching focus, deal risks & watch-outs, key stakeholders, questions to ask your rep, recommended next steps). **Sales Enablement** gets an onboarding/best-practice set (company snapshot, best-practice prep steps, key talking points, objection handling, playbook & messaging alignment, pre-meeting readiness checklist). The **Revenue Operations Manager** gets an adoption/ROI set (account snapshot, CRM data health & gaps, process & workflow fit, automation opportunities, ROI hypothesis, adoption & rollout angle). The **VP of Sales** gets an executive set (executive summary, strategic fit, revenue opportunity, win probability & risks, competitive landscape, executive recommendation). The **Admin** gets a deliberately non-selling data-provenance set (source inventory & credibility, data lineage, coverage gaps & missing data, data freshness, integration & field-mapping status, quality flags) that leans on the SI-12 credibility scoring.

A `sections_for(persona)` helper returns the ordered list for any persona and defaults safely to the Sales Representative section set for unknown values, and a `DEFAULT_PERSONA = "sales_rep"` constant makes the default explicit for every layer that has to pick one. Because this module is the shared contract, its field names and persona keys are kept identical to the frontend's TypeScript mirror and to the LLM's expected JSON shape.

## Acceptance criteria
```gherkin
Scenario: The six personas and their metadata are defined once and shared
  Given the shared schemas module
  When any layer reads the persona definitions
  Then Persona exposes exactly sales_rep, sales_manager, enablement, revops, vp_sales, and admin
  And PERSONA_LABELS maps them to their full-form role names from the persona doc
  And PERSONA_TAGLINES provides a one-line description for each
  And DEFAULT_PERSONA equals "sales_rep"
```
```gherkin
Scenario: Each persona has its own ordered section set
  Given PERSONA_SECTIONS
  When sections_for("vp_sales") is requested
  Then it returns the executive sections in order, leading with the executive summary
  And sections_for("admin") returns the data-provenance sections including source inventory and quality flags
  And sections_for("sales_rep") returns the full nine pre-meeting sections in display order
```
```gherkin
Scenario: Unknown persona resolves to the default (edge case)
  Given PERSONA_SECTIONS
  When sections_for is called with an unrecognized value
  Then it returns the sales_rep section set rather than erroring
  And DEFAULT_PERSONA is used wherever a persona is not explicitly supplied
```

## Technical notes (reference)
- Key file: `backend/app/schemas.py` — rewritten `Persona` enum (six keys), `PERSONA_LABELS`, `PERSONA_TAGLINES`, `PERSONA_SECTIONS` (ordered `(id, title)` per persona), `DEFAULT_PERSONA = "sales_rep"`, and `sections_for()` defaulting to `sales_rep`.
- `PERSONA_SECTIONS["sales_rep"]` is derived from the existing `SECTION_ORDER` / `SECTION_TITLES` so the Sales Representative brief stays identical to the pre-refresh nine-section brief.
- The Admin persona's section set is intentionally a data-provenance/quality view, not a selling brief; its credibility content depends on SI-12.
- POC note: statuses remain plain strings on the DB models but must match the `BriefStatus` enum values.

## Definition of Done
- [x] `Persona` enum rewritten to the six persona-doc keys (`sales_rep`/`sales_manager`/`enablement`/`revops`/`vp_sales`/`admin`).
- [x] `PERSONA_LABELS` and `PERSONA_TAGLINES` defined with full-form role names and taglines from the persona doc.
- [x] `PERSONA_SECTIONS` ordered section sets defined for all six personas, with `sections_for()` defaulting to `sales_rep`.
- [x] `DEFAULT_PERSONA = "sales_rep"` added and used wherever a persona is not supplied.
- [x] Persona keys kept identical to `frontend/src/api/types.ts` and the LLM JSON shape.
