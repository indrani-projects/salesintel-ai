# SI-2.3 — Auto-trigger brief generation with a status state machine

| Field | Value |
|---|---|
| Issue type | Story |
| Parent epic | SI-2 — Calendar & Meeting Management |
| Status | Done |
| Priority | Highest |
| Story points | 5 |
| Component | Meetings |
| Labels | backend, api |

## User story
As a sales rep, I want a briefing to start generating the instant I add a meeting, so that it is ready and waiting when I open the prospect — with zero clicks and no way for a failure to break my calendar.

## Description
This is the "zero rep effort" heart of the epic. Creating a meeting does not just persist a row — it seeds one brief row per persona (AE, SDR, SE) and schedules asynchronous generation of the primary persona's brief via FastAPI `BackgroundTasks`. The rep never presses "generate"; by the time they navigate to the meeting, the brief is either ready or has a clear error state. The other personas are generated lazily on first view to keep free-tier LLM usage to roughly one request per meeting unless the rep actually toggles "View as".

Generation is a small state machine. A brief moves `pending → generating → ready | error`, and that status is mirrored on both the `Brief` row and — for the meeting's primary persona — the `Meeting.brief_status`. This dual mirroring lets the frontend poll a single meeting-brief endpoint and watch the status flip, without joining across tables. On success the brief stores its validated JSON content, rendered HTML, and a generation timestamp; on failure it records a truncated error message.

Robustness is the non-negotiable requirement. The background task opens its OWN database session (it cannot reuse the request's session, which is already closed by the time it runs) and is wrapped in a catch-all: any exception during generation is caught and written as `status=error` rather than propagating. The task must NEVER raise, because an unhandled exception in a background task would otherwise destabilize the server. Regeneration (`POST /meetings/{id}/brief/regenerate`) resets the targeted persona's brief back to `pending` — clearing prior content, HTML, error, and timestamp — mirrors `pending` onto the meeting when it targets the primary persona, and re-schedules the same background task.

Running on `BackgroundTasks` instead of a real job queue is a deliberate, documented POC shortcut; the state machine is designed so that swapping in a queue later would not change the observable contract.

## Acceptance criteria
```gherkin
Scenario: Creating a meeting auto-schedules generation
  Given a rep submits a new meeting
  When the meeting is persisted
  Then a brief row is seeded for each persona
  And the primary persona's brief generation is scheduled as a background task
  And the meeting's brief_status is set to generating
```

```gherkin
Scenario: Status is mirrored on both the meeting and the brief
  Given the primary persona's brief is generating
  When generation completes successfully
  Then the Brief.status becomes ready
  And the Meeting.brief_status also becomes ready
  And the brief stores its JSON content, rendered HTML, and generated_at timestamp
```

```gherkin
Scenario: A generation failure never crashes the server
  Given the LLM call raises an exception during generation
  When the background task catches it
  Then the brief status is written as error with a truncated message
  And the meeting's brief_status is set to error for the primary persona
  And the server keeps running normally
```

```gherkin
Scenario: Regenerate resets and re-runs
  Given a meeting whose brief is ready (or in error)
  When the rep POSTs to /meetings/{id}/brief/regenerate
  Then the targeted persona's brief is reset to pending with cleared content, html, error, and timestamp
  And a fresh generation background task is scheduled
```

## Technical notes (reference)
- Key files: `backend/app/api/meetings.py` (`create_meeting`, `_run_generation`, `generate_one_task`, `regenerate_brief`), `backend/app/services/brief_engine.py` (`generate_brief`), `backend/app/services/brief_render.py` (`render_html`), `backend/app/models.py` (`Meeting.brief_status`, `Brief.status`)
- `_run_generation` opens its own `Session(engine)`; the whole LLM call is wrapped in `try/except Exception` → `status="error"` (must never re-raise).
- Only the primary persona generates on create; AE/SDR/SE others start `pending` and generate lazily on first view. `is_primary = persona == meeting.persona` gates whether `Meeting.brief_status` is mirrored.
- Frontend polls `GET /meetings/{id}/brief` (TanStack Query) to observe the flip.
- POC shortcut: FastAPI `BackgroundTasks`, not a job queue.

## Definition of Done
- [x] `POST /meetings` seeds per-persona brief rows and schedules primary generation
- [x] Status flows `pending → generating → ready | error`
- [x] Status is mirrored on both `Meeting.brief_status` and `Brief.status` for the primary persona
- [x] Background task opens its own DB session and is catch-all safe (never raises)
- [x] Failures are recorded as `status=error` with a truncated message
- [x] `regenerate` resets the brief to `pending` and re-schedules the task
