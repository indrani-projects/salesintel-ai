# SI-16.3 — Automation status + Settings card surfacing

| Field | Value |
|---|---|
| Issue type | Story |
| Parent epic | SI-16 — Scheduled Day-Before Persona Email (+ per-persona routing) |
| Status | Done |
| Priority | Medium |
| Story points | 3 |
| Component | Brief Delivery |
| Labels | backend, frontend, api, email |

## User story
As a user checking Settings, I want the Automated emails card to tell me that the day-before send is on and that briefs go to each persona's address, so that I can confirm the automation is configured the way I expect.

## Description
This story surfaces the new day-before trigger and per-persona routing so they are visible in the app, not just in `.env`. On the backend, `automation_status()` gains three fields — `day_before_enabled`, `day_before_minutes`, and `personalized` — reflecting the config and resolver from SI-16.1 and SI-16.2.

The `EmailAutomationStatus` DTO is extended with the matching `day_before_enabled` / `day_before_minutes` / `personalized` fields, kept in sync across `schemas.py` and `frontend/src/api/types.ts` per the shared-contract convention.

On the frontend, the Settings "Automated emails" card renders the new state: a "Day before ~24h" line when the day-before trigger is enabled, and "Sent to each meeting's persona address" when `personalized` is true. This is what the Playwright screenshot asserts (6/6), confirming the card shows the day-before line end to end.

## Acceptance criteria
```gherkin
Scenario: Automation status reports the day-before trigger
  Given the day-before trigger is enabled
  When automation_status() is read
  Then it returns day_before_enabled true and day_before_minutes 1440
```

```gherkin
Scenario: Settings card shows the day-before line
  Given the automation status has day_before_enabled true
  When the Settings "Automated emails" card renders
  Then it shows a "Day before ~24h" line
```

```gherkin
Scenario: Settings card shows per-persona routing
  Given automation status has personalized true
  When the Settings card renders
  Then it shows "Sent to each meeting's persona address"
```

## Technical notes (reference)
- Backend: `automation_status()` exposes `day_before_enabled`, `day_before_minutes`, `personalized`.
- DTO: `EmailAutomationStatus` gains `day_before_enabled` / `day_before_minutes` / `personalized`, mirrored in `schemas.py` and `frontend/src/api/types.ts`.
- Frontend: Settings "Automated emails" card renders the "Day before ~24h" line and "Sent to each meeting's persona address" when personalized.
- Verified by Playwright (6/6): the Settings card screenshot shows the day-before line.

## Definition of Done
- [x] `automation_status()` returns `day_before_enabled` / `day_before_minutes` / `personalized`.
- [x] `EmailAutomationStatus` DTO extended and kept in sync across `schemas.py` + `frontend/src/api/types.ts`.
- [x] Settings card shows the "Day before ~24h" line when enabled.
- [x] Settings card shows "Sent to each meeting's persona address" when personalized.
- [x] npm build clean; Playwright 6/6 with the day-before line in the card screenshot.
