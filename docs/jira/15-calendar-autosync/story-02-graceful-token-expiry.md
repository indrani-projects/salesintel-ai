# SI-15.2 — Graceful expired-token handling

| Field | Value |
|---|---|
| Issue type | Story |
| Parent epic | SI-15 — Recurring Google Calendar Auto-Sync (+ graceful token expiry + live UI refresh) |
| Status | Done |
| Priority | High |
| Story points | 3 |
| Component | Integrations |
| Labels | backend, integration, google, reliability |

## User story
As a sales rep, when my Google connection quietly expires, I want the app to tell me to reconnect instead of throwing a server error, so that I know exactly what to do and the auto-sync recovers once I do it.

## Description
Google apps left in **Testing** publishing mode expire their refresh tokens roughly weekly. The old behavior hid this: the connection status still reported "connected" while every sync failed with `invalid_grant` and surfaced as a raw **500**. This story makes the failure legible and non-fatal.

The recurring loop is now fail-soft at its core: `sync_calendar_once()` returns `None` on any error — an expired token included — so `calendar_sync_loop()` treats a failed pass as a no-op and the daemon never dies. This also gives auto-recovery for free: once the rep reconnects, the very next tick succeeds.

The manual `POST /integrations/google/calendar/sync` endpoint now catches failures and translates them. An expired or revoked connection returns a clear **400** — "Google connection expired or was revoked — Disconnect, then Connect Google again" — instead of a raw 500. Any other failure returns **502** carrying the error message. The result is a failure the rep can act on and a scheduler that heals itself.

## Acceptance criteria
```gherkin
Scenario: Expired token returns an actionable 400
  Given the connected Google refresh token has expired or been revoked
  When the manual calendar sync endpoint is called
  Then it returns 400 with "Google connection expired or was revoked — Disconnect, then Connect Google again"
  And it does not return a raw 500
```

```gherkin
Scenario: Other failures return 502 with the message
  Given a sync fails for a reason other than an expired token
  When the manual calendar sync endpoint is called
  Then it returns 502 carrying the failure message
```

```gherkin
Scenario: The recurring loop is fail-soft
  Given a sync pass fails (for example, an expired token)
  When sync_calendar_once runs inside the loop
  Then it returns None instead of raising
  And the daemon stays alive for the next interval
```

```gherkin
Scenario: Auto-recovery after reconnect
  Given the connection was expired and is then reconnected
  When the next sync interval elapses
  Then the pass succeeds and outstanding events are imported
```

## Technical notes (reference)
- Key file: `backend/app/services/google.py` — `sync_calendar_once()` returns `None` on any error (fail-soft).
- Endpoint: `POST /integrations/google/calendar/sync` — catches failures; 400 with the reconnect message for expired/revoked, 502 for other failures.
- Root cause: Google apps in **Testing** publishing mode expire refresh tokens ~weekly (`invalid_grant`); status read "connected" while every sync 500'd.
- Auto-recovery: the loop's next tick succeeds once the rep reconnects Google.

## Definition of Done
- [x] `sync_calendar_once()` returns `None` on any error so the loop never dies.
- [x] Manual sync endpoint returns a clear 400 reconnect message for expired/revoked tokens (not a 500).
- [x] Other sync failures return 502 with the failure message.
- [x] Scheduler auto-recovers on the next tick after reconnect.
- [x] Covered by a google test asserting the endpoint reports a clear reconnect message, not a 500.
