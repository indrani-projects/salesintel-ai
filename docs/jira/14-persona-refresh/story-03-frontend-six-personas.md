# SI-14.3 — Frontend: six-persona types, colours, selector grid, tabs & badges

| Field | Value |
|---|---|
| Issue type | Story |
| Parent epic | SI-14 — Persona Refresh: the six personas from the persona doc (supersedes SI-4) |
| Status | Done |
| Priority | High |
| Story points | 5 |
| Component | Personas |
| Labels | frontend, ux |

## User story
As a sales rep using the app, I want to pick and switch between all six personas with each one clearly and distinctly labelled, so that choosing "VP of Sales" or "Admin" is obvious at a glance and the brief header always tells me which lens I'm reading.

## Description
This story updates the frontend to mirror the six-persona contract end to end. `api/types.ts` is updated so the `Persona` union, `PERSONA_ORDER`, `PERSONA_LABELS`, and `PERSONA_TAGLINES` all reflect the six persona-doc keys, kept identical to `schemas.py`. A `lib/persona.ts` helper assigns one distinct Tailwind colour per persona — `sales_rep` = brand, `sales_manager` = emerald, `enablement` = amber, `revops` = sky, `vp_sales` = violet, `admin` = slate — expressed as literal class strings so Tailwind's compiler keeps them.

The persona selector in the create-meeting dialog becomes a responsive **3×2 grid** so all six personas are visible and pickable at once rather than a cramped row. On the brief view, the persona tabs and badges render all six personas, each carrying its own colour from `lib/persona.ts`, so the currently-viewed lens is unmistakable. The sidebar/user title is updated to match the refreshed persona set. Per-persona polling and the lazy "generating → ready" flip from SI-4 are preserved unchanged.

## Acceptance criteria
```gherkin
Scenario: The frontend mirrors the six personas
  Given api/types.ts
  When the persona metadata is read
  Then the Persona union, PERSONA_ORDER, PERSONA_LABELS, and PERSONA_TAGLINES all contain exactly the six persona-doc keys
  And they match schemas.py
```
```gherkin
Scenario: Each persona is visually distinct
  Given lib/persona.ts
  When a persona badge or tab is rendered
  Then sales_rep is brand, sales_manager emerald, enablement amber, revops sky, vp_sales violet, and admin slate
  And each colour is a literal Tailwind class string that survives compilation
```
```gherkin
Scenario: All six personas are selectable and viewable
  Given the create-meeting dialog
  When the persona selector is shown
  Then it renders as a responsive 3×2 grid of the six personas
  And the brief view exposes tabs and badges for all six, each in its persona colour
  And switching persona polls that persona and flips generating to ready without a reload
```

## Technical notes (reference)
- Key files: `frontend/src/api/types.ts` (Persona union, `PERSONA_ORDER`, `PERSONA_LABELS`, `PERSONA_TAGLINES`), `frontend/src/lib/persona.ts` (per-persona literal Tailwind colour strings), the create-meeting dialog persona selector (3×2 grid), the brief-view persona tabs/badges, and the sidebar/user title.
- Colours are written as literal class strings (not interpolated) so Tailwind's content scanner does not purge them.
- Per-persona polling and the lazy generation flip are carried over from SI-4 unchanged.

## Definition of Done
- [x] `api/types.ts` mirrors the six personas (union, order, labels, taglines) in sync with `schemas.py`.
- [x] `lib/persona.ts` gives each persona one distinct literal Tailwind colour (brand/emerald/amber/sky/violet/slate).
- [x] Create-meeting dialog persona selector is a responsive 3×2 grid.
- [x] Brief-view persona tabs and badges render all six personas in their colours.
- [x] Sidebar/user title updated for the refreshed persona set; per-persona polling preserved.
