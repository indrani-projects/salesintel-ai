# SI-15.3 — Live UI refresh for auto-synced meetings

| Field | Value |
|---|---|
| Issue type | Story |
| Parent epic | SI-15 — Recurring Google Calendar Auto-Sync (+ graceful token expiry + live UI refresh) |
| Status | Done |
| Priority | Medium |
| Component | Integrations |
| Labels | frontend, ux, integration |

## User story
As a sales rep, I want a meeting the app auto-imports from Google Calendar to appear in my Calendar and Dashboard on its own, so that I don't have to manually refresh to see what the scheduler pulled in.

## Description
The recurring scheduler (SI-15.1) imports meetings in the background, but the UI couldn't see them arrive. The Calendar and Dashboard meetings-list query previously polled every 4s **only** while a brief was generating, then stopped once everything was ready. So a meeting imported while the list was idle didn't show until the rep manually refreshed the page.

This story closes the loop on the client. The idle case now keeps a **15s** poll (still 4s while a brief is generating), so newly-synced meetings — and their brief-status changes — surface without any user action. The faster 4s cadence during generation is retained so in-flight brief progress still feels live. The result is that the daemon-driven import (SI-15.1) and its self-healing behavior (SI-15.2) are actually visible to the rep in near real time.

## Acceptance criteria
```gherkin
Scenario: Idle list still polls so auto-synced meetings appear
  Given no brief is currently generating
  When the scheduler imports a new meeting in the background
  Then the meetings list keeps polling every 15 seconds
  And the new meeting appears without a manual refresh
```

```gherkin
Scenario: Faster polling while a brief is generating
  Given a brief is generating
  When the meetings list is shown
  Then it polls every 4 seconds so brief-status changes stay live
```

## Technical notes (reference)
- Scope: the Calendar and Dashboard meetings-list query (TanStack Query `refetchInterval`).
- Before: polled every 4s only while a brief was generating, then stopped (idle = no poll).
- After: idle keeps a 15s poll; 4s retained while a brief is generating.
- Effect: meetings imported by the SI-15.1 daemon appear within the 15s idle window with no manual refresh.

## Definition of Done
- [x] Idle meetings-list query polls every 15s (was: stopped when idle).
- [x] 4s poll retained while a brief is generating.
- [x] Auto-synced meetings appear in Calendar and Dashboard without a manual refresh.
- [x] Verified live: reconnected Google, scheduler imported 2 meetings, UI reflected them within the 15s poll.
