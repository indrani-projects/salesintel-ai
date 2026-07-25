# SI-16.3 — Automation status + Settings card surfacing

| Field | Value |
|---|---|
| Issue type | Story |
| Parent epic | SI-16 — Scheduled 1-Hour-Before Persona Email (+ per-persona routing) |
| Status | Done |
| Priority | Medium |
| Component | Brief Delivery |
| Labels | backend, frontend, api, email |

## User story
As a user checking Settings, I want the Automated emails card to tell me when briefs are sent before a meeting and that they go to each persona's address, so that I can confirm the automation is configured the way I expect.

## Description
This story surfaces the pre-meeting timing and per-persona routing so they are visible in the app, not just in `.env`. On the backend, `automation_status()` reports `enabled`, `lead_minutes` (the pre-meeting window, default 60), `recipient`, `transport`, and `personalized` (true when at least one persona has its own `PERSONA_EMAILS` address).

The `EmailAutomationStatus` DTO carries these fields, kept in sync across `schemas.py` and `frontend/src/api/types.ts` per the shared-contract convention. (An earlier iteration exposed `day_before_enabled` / `day_before_minutes`; those were removed when the day-before tier was dropped in favour of the 1-hour pre-meeting send.)

On the frontend, the Settings "Automated emails" card renders the state: a "Before the meeting: within {lead_minutes} min of the start time" line, and "Sent to each meeting's persona address" when `personalized` is true. This is what the Playwright test asserts (7/7).

## Acceptance criteria
```gherkin
Scenario: Automation status reports the pre-meeting window
  Given the automation is configured
  When automation_status() is read
  Then it returns lead_minutes 60 and a personalized flag
  And it does not expose any day-before fields
```

```gherkin
Scenario: Settings card shows the pre-meeting window
  Given the automation status
  When the Settings "Automated emails" card renders
  Then it shows "Before the meeting: within 60 min of the start time"
```

```gherkin
Scenario: Settings card shows per-persona routing
  Given automation status has personalized true
  When the Settings card renders
  Then it shows "Sent to each meeting's persona address"
```

## Technical notes (reference)
- Backend: `automation_status()` exposes `enabled`, `lead_minutes`, `recipient`, `transport`, `personalized` (no day-before fields).
- DTO: `EmailAutomationStatus` carries `personalized`, mirrored in `schemas.py` and `frontend/src/api/types.ts`.
- Frontend: Settings "Automated emails" card renders the pre-meeting window line and "Sent to each meeting's persona address" when personalized.
- Verified by Playwright (7/7): the Settings card shows the "Before the meeting: within 60 min" line.

## Definition of Done
- [x] `automation_status()` returns `enabled` / `lead_minutes` / `recipient` / `transport` / `personalized` (no day-before fields).
- [x] `EmailAutomationStatus` DTO kept in sync across `schemas.py` + `frontend/src/api/types.ts`.
- [x] Settings card shows the "Before the meeting: within {lead_minutes} min" line.
- [x] Settings card shows "Sent to each meeting's persona address" when personalized.
- [x] npm build clean; Playwright 7/7 with the reworded card.
