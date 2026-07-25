# SI-10.3 — Two-way Google Calendar sync

| Field | Value |
|---|---|
| Issue type | Story |
| Parent epic | SI-10 — Google Workspace Integration |
| Status | Done |
| Priority | High |
| Story points | 8 |
| Component | Integrations |
| Labels | backend, api, google, calendar, data |

## User story
As a sales rep, I want my Google Calendar and the app's calendar to stay in sync both ways, so that prospect meetings I book in Google show up as briefs in the app, and meetings I add in the app appear on my Google Calendar.

## Description
This story makes the calendar two-way. **Inbound:** `POST /integrations/google/calendar/sync` pulls upcoming events from the connected account's **primary** calendar. Each event whose title matches a known prospect becomes a meeting + brief. Matching is **lenient** — the event summary is normalized and compared against known company names, so "Discovery call with Sleep Company" resolves to the prospect "The Sleep Company." Events that don't match a prospect are skipped.

Import is **idempotent**: each created meeting records the source `google_event_id`, and re-running the sync dedupes against it, so nothing is duplicated on repeated syncs. Meeting + brief creation reuses the existing `build_meeting_with_briefs` helper, so imported meetings get the same brief-generation lifecycle as manually added ones. The endpoint returns a `CalendarSyncResult` summarizing what was imported/skipped.

**Outbound:** when a meeting is created in the app (`api/meetings.py`), it is pushed **out** to Google Calendar via `google_service.insert_event`, and the returned event id / html link are stored on the meeting. This push is **best-effort**: any failure (Google not connected, API error, mock mode) is swallowed so it can never break meeting creation.

Two new columns support this: `Meeting.google_event_id` (indexed, for dedupe) and `Meeting.google_html_link`. Because SQLModel's `create_all` does not `ALTER` existing tables, they are added by an **idempotent `_ensure_columns()` migration** in `db.py` that checks the live schema and adds any missing columns on startup — safe to run every boot. New DTOs `GoogleStatus` and `CalendarSyncResult` are added to `schemas.py`.

Under `mock_google`, the pull returns a deterministic set of events and the push is a no-op success, so the whole two-way flow is exercised hermetically in tests and E2E.

## Acceptance criteria
```gherkin
Scenario: Inbound — a prospect event becomes a meeting + brief
  Given a Google account is connected
  And the primary calendar has an upcoming event "Discovery call with Sleep Company"
  When the rep calls POST /integrations/google/calendar/sync
  Then a meeting is created for the prospect "The Sleep Company"
  And a brief is generated for it via build_meeting_with_briefs
```

```gherkin
Scenario: Inbound sync is idempotent
  Given a prospect event was already imported once
  When the sync runs again
  Then no duplicate meeting is created
  And dedupe is matched on google_event_id
```

```gherkin
Scenario: Non-prospect events are skipped
  Given the primary calendar has an event that matches no known prospect
  When the sync runs
  Then no meeting is created for that event
  And it is reported as skipped in the CalendarSyncResult
```

```gherkin
Scenario: Outbound — app meetings are pushed to Google, best-effort
  Given a Google account is connected
  When the rep creates a meeting in the app
  Then the meeting is inserted into Google Calendar
  And its google_event_id and google_html_link are stored
  And a push failure never blocks meeting creation
```

```gherkin
Scenario: New columns are added without dropping data
  Given an existing SQLite database without the Google columns
  When the app starts
  Then _ensure_columns() adds google_event_id and google_html_link if missing
  And re-running it makes no further changes
```

## Technical notes (reference)
- Key files: `backend/app/api/google.py`, `backend/app/api/meetings.py`, `backend/app/services/google_service.py`, `backend/app/models.py`, `backend/app/db.py`, `backend/app/schemas.py`.
- Inbound: `POST /integrations/google/calendar/sync` pulls primary-calendar events, lenient normalized name match to a known prospect, dedupe by `google_event_id`, reuses `build_meeting_with_briefs`, returns `CalendarSyncResult`.
- Outbound: `google_service.insert_event` called on meeting creation in `api/meetings.py`; best-effort (swallowed on failure); stores returned event id + html link.
- `models.py`: `Meeting.google_event_id` (indexed) + `Meeting.google_html_link`.
- `db.py`: idempotent `_ensure_columns()` migration adds the columns since `create_all` does not ALTER.
- `schemas.py`: `GoogleStatus`, `CalendarSyncResult`.
- Deterministic pull + no-op push under `mock_google`.

## Definition of Done
- [x] `POST /integrations/google/calendar/sync` imports matching prospect events as meetings + briefs.
- [x] Lenient normalized name match resolves e.g. "Discovery call with Sleep Company" → "The Sleep Company".
- [x] Import deduped by `google_event_id` so re-sync is idempotent.
- [x] App-created meetings are pushed to Google via `insert_event`, best-effort and non-breaking.
- [x] `Meeting.google_event_id` (indexed) + `google_html_link` added via idempotent `_ensure_columns()` migration.
- [x] `GoogleStatus` and `CalendarSyncResult` DTOs added to `schemas.py`.
- [x] Whole two-way flow deterministic under `MOCK_GOOGLE`.
