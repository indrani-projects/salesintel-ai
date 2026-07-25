# SI-15.4 — Deletion reconciliation for meetings removed in Google

| Field | Value |
|---|---|
| Issue type | Story |
| Parent epic | SI-15 — Recurring Google Calendar Auto-Sync (+ graceful token expiry + live UI refresh) |
| Status | Done |
| Priority | Medium |
| Story points | 3 |
| Component | Integrations |
| Labels | backend, integration, google |

## User story
As a sales rep, I want a meeting I delete in Google Calendar to disappear from the app on its own, so that my Calendar and Dashboard stay in sync with my real schedule without me manually cleaning up stale meetings.

## Description
The recurring scheduler (SI-15.1) keeps meetings *added* in Google Calendar flowing into the app, but deletions were one-directional dead ends: cancel an event in Google and its imported meeting — plus its brief and chat — lingered in the app forever. This story closes that gap by having `import_calendar_events` reconcile deletions after a successful sync.

The logic is deliberately narrow and safe. A meeting is removed only when it is linked to a Google event whose id no longer appears in the current calendar listing **and** whose `start_time` falls inside the sync window (`days_back=1, days_ahead=30`) that `list_events()` actually scans. Bounding the check to that window means an out-of-range meeting is never mistaken for a deletion. And because `list_events()` **raises** on failure rather than returning a partial or empty list, deletions only ever fire when the event list is authoritative — a transient network error can't be misread as "everything was deleted" and wipe the rep's meetings.

Removal is handled by a shared helper, `meetings.delete_meeting_cascade(session, meeting)`, which deletes the meeting together with its briefs and chat. The same helper backs the manual DELETE endpoint and this reconciliation pass, so the two paths can't drift. `CalendarSyncResult` gains a `deleted` field carrying the count, and the sync message notes any removals. Combined with the 30s scheduler (SI-15.1) and the 15s UI poll (SI-15.3), a deletion in Google disappears from the app within roughly 30–45 seconds.

## Acceptance criteria
```gherkin
Scenario: A meeting deleted in Google is removed from the app
  Given a meeting was imported from a Google Calendar event
  And that event no longer appears in the calendar listing
  And the meeting's start_time is inside the sync window
  When import_calendar_events reconciles the sync
  Then the meeting, its briefs, and its chat are deleted
  And the deleted count is included in the sync result
```

```gherkin
Scenario: An out-of-range meeting is never mistaken for a deletion
  Given a meeting whose start_time is outside the days_back=1/days_ahead=30 window
  When import_calendar_events reconciles the sync
  Then the meeting is left untouched because it was never in scope for the listing
```

```gherkin
Scenario: A network error cannot wipe meetings
  Given list_events raises on a failed calendar fetch
  When the sync pass runs
  Then no deletion reconciliation happens
  And existing meetings are preserved
```

## Technical notes (reference)
- Key file: `backend/app/services/google.py` — `import_calendar_events` reconciles deletions after a successful sync.
- Deletion rule: meeting linked to a Google event id absent from the current listing **and** with `start_time` inside the `list_events()` window (`days_back=1, days_ahead=30`).
- Safety: bounded to the scanned window (no out-of-range false positives); `list_events()` raises on failure (never a partial/empty list), so a network error can't trigger mass deletion.
- Shared helper: `meetings.delete_meeting_cascade(session, meeting)` removes meeting + briefs + chat; reused by the DELETE endpoint and the reconciliation.
- Result: `CalendarSyncResult` gains a `deleted` field; the sync message notes removals.
- Latency: with the 30s scheduler (SI-15.1) + 15s UI poll (SI-15.3), a Google deletion clears the app within ~30–45s.

## Definition of Done
- [x] `import_calendar_events` reconciles deletions after a successful sync (linked event id gone + `start_time` in window).
- [x] Reconciliation bounded to the `list_events()` window so out-of-range meetings aren't mistaken for deletions.
- [x] Relies on `list_events()` raising on failure, so a network error can't wipe meetings.
- [x] `meetings.delete_meeting_cascade(session, meeting)` shared by the DELETE endpoint and the reconciliation (meeting + briefs + chat).
- [x] `CalendarSyncResult` gains a `deleted` field and the sync message notes removals.
- [x] Verified: pytest — deleting the Google event removes the imported meeting (404) with `deleted >= 1`; npm build green; Playwright 7/7.
