# EPIC SI-15 — Recurring Google Calendar Auto-Sync (+ graceful token expiry + live UI refresh)

| Field | Value |
|---|---|
| Issue type | Epic |
| Suggested key | SI-15 |
| Status | Done |
| Priority | High |
| Component | Integrations |
| Labels | backend, frontend, integration, google, ux |
| Story points (rollup) | 14 |

## Summary
Meetings added in Google Calendar now appear in the app on their own, and meetings deleted in Google now disappear from it on their own — both without clicking "Sync". A background daemon re-imports prospect events on an interval and reconciles deletions after each successful pass, an expired Google token fails soft (a clear reconnect message instead of a raw 500), and the meetings list keeps polling while idle so auto-imported and auto-removed meetings surface by themselves.

## Description
SI-10 wired up Google Calendar as a source of meetings, but importing was a manual, one-shot action: the rep had to click "Sync" for anything added on the Google side to reach the app. This epic closes that gap. A long-lived background daemon calls a single fail-soft import pass every `CALENDAR_SYNC_SECONDS` (default 30s), so prospect events created in Google Calendar are picked up, turned into meetings, and have their briefs generated automatically. The scheduler is config-gated (`CALENDAR_SYNC_ENABLED`, default true) and is turned OFF in tests and E2E so it can never race explicit-sync assertions.

The second theme is graceful failure. Google apps left in **Testing** publishing mode expire their refresh tokens roughly weekly, and the symptom was ugly: the status still reported "connected" while every sync failed with `invalid_grant` and returned a raw 500. This epic makes that legible and non-fatal. The manual sync endpoint now catches the failure and returns a clear **400** ("Google connection expired or was revoked — Disconnect, then Connect Google again") rather than a 500, other failures return **502** with the message, and the recurring loop treats any error — an expired token included — as a no-op so the daemon never dies. Once the rep reconnects, the scheduler auto-recovers on its next tick.

The third theme is a live UI. The Calendar and Dashboard meetings-list query used to poll every 4s **only** while a brief was generating, then stop — so a meeting imported by the daemon wouldn't show until a manual refresh. The idle case now keeps a 15s poll (4s while generating), so newly-synced meetings and their brief-status changes appear without the rep touching anything.

The fourth theme makes the sync two-directional for removals. Importing kept meetings *added* in Google flowing in, but deletions were dead ends — cancel an event in Google and its meeting, brief, and chat lingered in the app forever. After a successful sync, `import_calendar_events` now reconciles deletions: a meeting linked to a Google event whose id no longer appears in the calendar listing, **and** whose `start_time` is inside the sync window (`days_back=1, days_ahead=30`), is removed. The check is deliberately bounded and safe — it uses the same window `list_events()` scans, so an out-of-range meeting is never mistaken for a deletion, and `list_events()` **raises** on failure (never a partial/empty list), so a network error can't be misread as "everything was deleted." Removal reuses the shared `meetings.delete_meeting_cascade(session, meeting)` helper (meeting + briefs + chat) that also backs the DELETE endpoint, and `CalendarSyncResult` gains a `deleted` count that the sync message reports. Combined with the 30s scheduler and the 15s UI poll, a deletion in Google clears from the app within ~30–45s. Together these four stories turn a manual, brittle, one-way sync into a hands-off, self-healing, bidirectional integration.

## Stories in this epic
| Key | Story | Points | Priority |
|---|---|---|---|
| SI-15.1 | Recurring calendar-sync scheduler | 5 | High |
| SI-15.2 | Graceful expired-token handling | 3 | High |
| SI-15.3 | Live UI refresh for auto-synced meetings | 3 | Medium |
| SI-15.4 | Deletion reconciliation for meetings removed in Google | 3 | Medium |

## Epic acceptance criteria
```gherkin
Scenario: A meeting added in Google Calendar appears without clicking Sync
  Given the calendar-sync scheduler is enabled
  And a prospect event is created in Google Calendar
  When the next sync interval elapses
  Then the event is imported as a meeting and its brief is generated
  And the meeting appears in the app within the idle poll window
```

```gherkin
Scenario: An expired Google token does not crash the sync
  Given the connected Google refresh token has expired or been revoked
  When the recurring loop runs its import pass
  Then the pass returns without raising and the daemon stays alive
  And the manual sync endpoint returns a clear reconnect message, not a 500
```

```gherkin
Scenario: Auto-recovery after reconnect
  Given a previously expired Google connection is reconnected
  When the next sync interval elapses
  Then the scheduler imports the outstanding prospect events
  And their briefs are generated
```

```gherkin
Scenario: A meeting deleted in Google is removed from the app
  Given a meeting was imported from a Google Calendar event within the sync window
  And that event no longer appears in the calendar listing
  When the next successful sync pass reconciles deletions
  Then the meeting, its briefs, and its chat are deleted
  And the sync result reports the deletion count
  And the meeting disappears from the app within the idle poll window
```

## Out of scope
- Push/webhook (Google Calendar watch channels) delivery — this epic polls on an interval.
- Moving Google publishing mode out of Testing (refresh-token longevity is an operator action, not code).
- Two-way sync of app-created meetings back into Google Calendar beyond what SI-10 already covers.
- Replacing FastAPI `BackgroundTasks` / the daemon loop with a real job queue.

## Dependencies
- SI-10 (Google Calendar integration) — the OAuth connection, token store, and one-shot import this epic makes recurring.
- Brief generation epic (SI-3) — the background-safe brief generation the sync pass triggers per imported meeting.
- FastAPI app lifecycle (`main.py` startup) — where the daemon is launched when enabled.
- Test/E2E harness (conftest + `playwright.config`) — where the scheduler is disabled to keep explicit-sync assertions deterministic.

## Verification
- **Backend pytest** all green, including the **3 google tests** from PR #14 — `sync_calendar_once` returns a result under mock, is fail-soft on an expired token, and the endpoint reports a clear reconnect message (not a 500) — plus a **deletion-reconciliation test** (SI-15.4): deleting the Google event (`list_events()` returns `[]` on re-sync) removes the imported meeting (404) with `deleted >= 1`. **npm build** clean, **Playwright 7/7**.
- Live: after the user reconnected Google, the 30s scheduler auto-imported 2 meetings (`[calendar-sync] imported 2, updated 0`) and their briefs generated; the UI reflected them within the 15s poll.
- Auto-sync (SI-15.1–15.3) shipped as **PR #14** (branch `feat/calendar-autosync`); deletion reconciliation (SI-15.4) shipped as **PR #18**.
