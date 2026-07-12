# SI-4.4 — Persona selector, "View as" toggle & badges

| Field | Value |
|---|---|
| Issue type | Story |
| Parent epic | SI-4 — Multi-Persona Briefs (AE / SDR / SE) |
| Status | Done |
| Priority | Medium |
| Story points | 5 |
| Component | Personas |
| Labels | frontend, ux |

## User story
As a sales rep, I want to pick my role when I schedule a meeting and switch between the AE / SDR / SE views on the brief, so that I can see the same prospect through whichever lens fits the moment without leaving the page.

## Description
This story surfaces personas throughout the UI so the multi-persona capability is visible and usable end to end. When creating a meeting, the meeting dialog includes a persona selector that sets the meeting's primary persona — the one generated immediately. Every persona is shown by its full-form label (Account Executive, Sales Development Rep, Solutions Engineer) rather than an abbreviation, so the choice is unambiguous.

On the brief itself, a "View as AE / SDR / SE" segmented toggle lets the rep switch the viewed persona. The view initializes to the meeting's primary persona and, on switch, fetches that persona's brief with per-persona polling: because secondary personas generate lazily on first view, the toggle drives a live "generating" state that flips to "ready" and renders that persona's section set once the background task completes — no page reload. Each persona's brief renders its own ordered sections, so switching from AE to SDR to SE visibly changes the document, not just a label.

Persona is reinforced with consistent visual cues. Dashboard cards carry a persona badge, and the brief header shows the active persona's label/badge, using a subtle per-persona accent (indigo for AE, emerald for SDR, amber for SE) for at-a-glance differentiation while the app's primary accent stays indigo. Labels and taglines are sourced from the shared persona metadata so wording stays identical between the UI and the backend contract. The server-rendered brief HTML also carries a persona label/badge so exported and emailed briefs are self-identifying.

## Acceptance criteria
```gherkin
Scenario: Persona is chosen when scheduling a meeting
  Given the new-meeting dialog is open
  When the rep selects a persona from the selector and saves
  Then the meeting is created with that persona as its primary
  And the persona is shown by its full-form label in the dialog
```
```gherkin
Scenario: "View as" toggle switches personas with per-persona polling
  Given a brief is open and initialized to its primary persona
  When the rep switches the "View as" toggle to a persona that has not generated yet
  Then the view shows a generating state and polls that persona's brief
  And when generation completes the persona's own section set renders without a page reload
```
```gherkin
Scenario: Persona badges are shown on dashboard cards and the brief header
  Given meetings exist with different primary personas
  When the rep views the dashboard and opens a brief
  Then each dashboard card shows a full-form persona badge
  And the brief header shows the active persona's label with its accent colour
```
```gherkin
Scenario: Switching to a persona whose generation failed (edge case)
  Given a persona's brief finished in an error state
  When the rep switches the "View as" toggle to that persona
  Then the view shows the error state for that persona
  And the other personas remain viewable and unaffected
```

## Technical notes (reference)
- Key files: `frontend/src/pages/BriefView.tsx` ("View as" segmented toggle, `activePersona`/`viewPersona`, per-persona polling), the meeting dialog (persona selector), dashboard cards (persona badge), `frontend/src/lib/persona.ts` (`PERSONAS`, `PERSONA_LABELS`, `PERSONA_TAGLINES`, `PERSONA_ACCENTS`), `frontend/src/api/types.ts` (Persona type + label/tagline mirror).
- Persona accents are full literal Tailwind class strings (indigo AE / emerald SDR / amber SE) so the JIT scanner retains them; do not build them via string concatenation.
- The brief view queries per persona so the toggle leverages the lazy-generation API (`GET brief?persona=`) and its generating→ready polling.
- `brief_render.py` renders a persona label/badge in the server-side HTML so exported/emailed briefs are self-identifying.

## Definition of Done
- [x] Persona selector added to the meeting dialog, using full-form labels, setting the primary persona.
- [x] "View as AE / SDR / SE" toggle on the brief with per-persona fetch and generating→ready polling.
- [x] Persona badges on dashboard cards and the brief header with per-persona accent colours.
- [x] Full-form persona labels/taglines sourced from shared metadata and kept in sync with the backend contract.
- [x] Persona label/badge rendered into the server-side brief HTML.
