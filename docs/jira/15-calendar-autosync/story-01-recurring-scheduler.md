# SI-15.1 — Recurring calendar-sync scheduler

| Field | Value |
|---|---|
| Issue type | Story |
| Parent epic | SI-15 — Recurring Google Calendar Auto-Sync (+ graceful token expiry + live UI refresh) |
| Status | Done |
| Priority | High |
| Story points | 5 |
| Component | Integrations |
| Labels | backend, integration, google |

## User story
As a sales rep, I want meetings I add in Google Calendar to show up in the app on their own, so that I don't have to remember to click "Sync" every time my schedule changes.

## Description
This story introduces a background daemon that re-imports Google Calendar prospect events on an interval, replacing the one-shot manual import from SI-10. Two config knobs govern it: `CALENDAR_SYNC_ENABLED` (default true) turns the scheduler on or off, and `CALENDAR_SYNC_SECONDS` (default 30) sets the interval.

Two functions in `backend/app/services/google.py` carry the work. `sync_calendar_once()` performs a single import pass — one Google Calendar import plus background-safe brief generation for any newly imported meetings — and returns a small result summary. `calendar_sync_loop()` is the long-lived daemon that calls `sync_calendar_once()` every `CALENDAR_SYNC_SECONDS`.

`main.py` starts `calendar_sync_loop` as a daemon task on application startup, but only when `CALENDAR_SYNC_ENABLED` is set. The scheduler is deliberately turned **OFF** in tests and E2E (via conftest and `playwright.config`) so it can never race the explicit-sync assertions that those suites depend on. Each successful pass logs a line such as `[calendar-sync] imported 2, updated 0`.

## Acceptance criteria
```gherkin
Scenario: Scheduler runs on the configured interval
  Given CALENDAR_SYNC_ENABLED is true and CALENDAR_SYNC_SECONDS is 30
  When the app starts
  Then calendar_sync_loop runs as a daemon and calls sync_calendar_once every 30 seconds
```

```gherkin
Scenario: A single pass imports and generates
  Given prospect events exist in the connected Google Calendar
  When sync_calendar_once runs
  Then the new events are imported as meetings
  And their briefs are generated background-safely
  And the pass returns a result summary
```

```gherkin
Scenario: Scheduler is disabled in tests and E2E
  Given the test/E2E configuration disables the scheduler
  When the suites run
  Then no background sync fires
  And explicit-sync assertions are not raced by the daemon
```

## Technical notes (reference)
- Key file: `backend/app/services/google.py` — `sync_calendar_once()` and `calendar_sync_loop()`.
- Config: `CALENDAR_SYNC_ENABLED` (default true), `CALENDAR_SYNC_SECONDS` (default 30).
- Startup: `main.py` launches `calendar_sync_loop` as a daemon when enabled.
- Test/E2E: scheduler disabled in conftest + `playwright.config` so it can't race explicit-sync assertions.
- Log line: `[calendar-sync] imported N, updated M` per successful pass.

## Definition of Done
- [x] `CALENDAR_SYNC_ENABLED` / `CALENDAR_SYNC_SECONDS` config added (defaults true / 30s).
- [x] `sync_calendar_once()` does one import pass plus background-safe brief generation and returns a result.
- [x] `calendar_sync_loop()` is a long-lived daemon calling it every interval.
- [x] `main.py` starts the loop as a daemon on startup when enabled.
- [x] Scheduler is OFF in tests/E2E (conftest + `playwright.config`).
