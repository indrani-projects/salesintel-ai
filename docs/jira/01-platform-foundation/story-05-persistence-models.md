# SI-1.5 — SQLite persistence layer (Meeting, Brief, ChatMessage)

| Field | Value |
|---|---|
| Issue type | Story |
| Parent epic | SI-1 — Platform Foundation & Data Contract |
| Status | Done |
| Priority | High |
| Story points | 3 |
| Component | Platform |
| Labels | backend, data |

## User story
As the application, I want to durably store meetings, their generated briefs, and chat history in a local database, so that briefs survive across requests and the frontend can poll for status as generation progresses.

## Description
This story delivers the persistence layer: the database engine setup plus the three tables that hold the app's state. It uses SQLModel over a local SQLite file — an intentional POC shortcut chosen for zero-setup portability (no database server to install or run for the demo). The database module owns the engine, session creation, and a one-shot table-creation routine called on server startup.

Three tables model the domain. **Meeting** holds what the rep entered on the calendar — subject, prospect company (both the free-text name and its resolved folder slug), the "why" and "agenda" that steer the brief, the start time, and the meeting's primary persona. It also carries a `brief_status` string mirroring where the primary brief is in its lifecycle, so the dashboard can show status without loading the whole brief. **Brief** holds the generated content: one row per (meeting, persona) pair, its own status, the serialized brief content, the rendered HTML, an optional error message, and a generated-at timestamp. **ChatMessage** stores the grounded Q&A history (user and assistant turns) for a meeting so a conversation with Scout persists.

A deliberate architectural decision runs through this story: the **persistence models are kept separate from the API DTOs**. `models.py` defines database tables; `schemas.py` defines the shapes sent over the wire. They are allowed to diverge. The clearest example is the brief content — it is stored as a **JSON string** in `Brief.content_json` and re-validated back into the typed schema on read, rather than being spread across many columns. This keeps the flexible, evolving brief structure out of the rigid table definition. Statuses are stored as plain strings, but they always match the values of the `BriefStatus` enum from the contract (`pending` / `generating` / `ready` / `error`), so the two layers agree without the database importing the enum type.

## Acceptance criteria

**Scenario: Tables are created on startup**
```gherkin
Given a fresh SQLite database file
When the server starts and initializes the database
Then the Meeting, Brief, and ChatMessage tables exist and are ready to use
```

**Scenario: A brief round-trips through JSON storage**
```gherkin
Given a generated brief with its structured content
When it is saved to the Brief row and later read back
Then the content_json is re-validated into the typed brief schema without loss
```

**Scenario: Status strings match the contract enum**
```gherkin
Given a brief moving through its lifecycle
When its status is written to the database as a string
Then the value is always one of pending, generating, ready, or error
And the meeting's brief_status mirrors its primary brief
```

**Scenario: One brief per meeting and persona**
```gherkin
Given a meeting that can have AE, SDR, and SE briefs
When briefs are stored for that meeting
Then each (meeting, persona) pair maps to exactly one brief row
```

## Technical notes (reference)
- Key files: `backend/app/db.py`, `backend/app/models.py`
- SQLModel tables over local SQLite (intentional POC shortcut vs. Postgres).
- `Brief.content_json` stores the serialized `BriefContent`; it is re-validated against the schema on read.
- `models.py` (persistence) is deliberately separate from `schemas.py` (API DTOs) — they may diverge.
- Statuses are plain strings that must match `schemas.BriefStatus` values; `Meeting.brief_status` mirrors the primary persona's brief.
- A unique constraint enforces one Brief per (meeting_id, persona).

## Definition of Done
- [x] Database engine, session, and startup table creation implemented in `db.py`.
- [x] Meeting, Brief, and ChatMessage SQLModel tables defined in `models.py`.
- [x] Brief content persisted as a JSON string and re-validated on read.
- [x] Persistence models kept separate from API DTOs.
- [x] Status strings align with the `BriefStatus` enum values; unique (meeting, persona) brief enforced.
