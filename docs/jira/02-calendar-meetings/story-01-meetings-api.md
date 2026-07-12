# SI-2.1 — Meetings API (create, list, get, delete)

| Field | Value |
|---|---|
| Issue type | Story |
| Parent epic | SI-2 — Calendar & Meeting Management |
| Status | Done |
| Priority | High |
| Story points | 3 |
| Component | Meetings |
| Labels | backend, api |

## User story
As a sales rep, I want a reliable way to create, list, view, and remove my prospect meetings, so that the calendar always reflects my real pipeline and each meeting carries the context needed to brief me.

## Description
This story delivers the REST surface for the meeting object — the core record that everything else in SalesIntel AI hangs off. A meeting captures the subject, the free-text prospect company, the rep's "why" and "agenda", the target persona, and the start time. Creating a meeting persists it to the database and returns the saved record (including its generated id and initial brief status) so the frontend can immediately show it on the calendar.

The API exposes four operations. `POST /meetings` creates a meeting; `GET /meetings` lists all meetings ordered by start time so the calendar can render them chronologically; `GET /meetings/{id}` fetches a single meeting; and `DELETE /meetings/{id}` removes a meeting. Delete is a cascade: it also removes the meeting's associated briefs (one per persona) and any chat messages, so no orphaned rows are left behind.

Request and response shapes are defined by shared Pydantic DTOs (`MeetingCreate`, `MeetingRead`) so the frontend's hand-mirrored types stay in lockstep with the backend. Persistence is SQLModel over SQLite — a deliberate POC choice. Note that `POST /meetings` does more than persist: it also seeds the per-persona brief rows and schedules brief generation, which is specified in detail in SI-2.3.

## Acceptance criteria
```gherkin
Scenario: Create a meeting
  Given a valid meeting payload with subject, prospect company, why, agenda, persona, and start time
  When the rep POSTs to /meetings
  Then a meeting row is persisted
  And the response contains the new meeting id and an initial brief status
```

```gherkin
Scenario: List meetings in chronological order
  Given several meetings exist with different start times
  When the client GETs /meetings
  Then all meetings are returned ordered by start time ascending
```

```gherkin
Scenario: Delete cascades to briefs and chat
  Given a meeting that has generated briefs and chat messages
  When the client DELETEs that meeting
  Then the meeting, its briefs, and its chat messages are all removed
  And the endpoint returns 204 No Content
```

```gherkin
Scenario: Fetching a missing meeting is a clean 404
  Given no meeting exists with id 9999
  When the client GETs /meetings/9999
  Then the API responds 404 with a "Meeting not found" detail
```

## Technical notes (reference)
- Key files: `backend/app/api/meetings.py` (router: `create_meeting`, `list_meetings`, `get_meeting`, `delete_meeting`), `backend/app/schemas.py` (`MeetingCreate`, `MeetingRead`), `backend/app/models.py` (`Meeting`, `Brief`, `ChatMessage`)
- Delete explicitly deletes child `Brief` and `ChatMessage` rows before the meeting (no DB-level cascade relied upon).
- List is sorted by `Meeting.start_time`; `GET /companies` is also served from this router via `sources.list_companies()`.
- POC shortcut: SQLite via SQLModel; no pagination on list (fine for demo volumes).

## Definition of Done
- [x] `POST /meetings` persists a meeting and returns the saved `MeetingRead`
- [x] `GET /meetings` returns all meetings ordered by start time
- [x] `GET /meetings/{id}` returns a meeting or a 404 when absent
- [x] `DELETE /meetings/{id}` cascades to briefs + chat and returns 204
- [x] Request/response shapes are backed by shared Pydantic DTOs
