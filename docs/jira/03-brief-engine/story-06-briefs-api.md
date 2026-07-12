# SI-3.6 — Briefs API (status, fetch content/HTML, regenerate)

| Field | Value |
|---|---|
| Issue type | Story |
| Parent epic | SI-3 — AI Brief Generation Engine |
| Status | Done |
| Priority | High |
| Story points | 3 |
| Component | Brief Engine |
| Labels | backend, api |

## User story
As the frontend, I want a single endpoint to fetch a meeting's brief that tells me its status and, when ready, its content and HTML, so that I can poll while it generates and render it the moment it's done — per persona.

## Description
This story is the HTTP seam between the intelligence core and the UI. The frontend never calls the engine directly; it calls the Briefs API, which reads the persisted brief for a given meeting and persona and returns a status-shaped response. When a brief is still `generating` the response carries just the status so the frontend can keep polling; when it is `ready` the response includes the parsed `BriefContent` and the rendered HTML; when it `error`ed it includes the error message. This one shape is what lets the dashboard show live status cards and the brief view flip to content the instant generation finishes.

The endpoint also handles lazy, on-demand generation per persona. A brief lives in one of the lifecycle states (`pending` / `generating` / `ready` / `error`), and each persona (AE/SDR/SE) has its own row. If a persona's brief has never been started — no row yet, or a `pending` row — the first fetch flips it to `generating`, persists that immediately so repeated polls don't re-schedule the same work, and hands the actual generation to a background task. This makes personas cheap: only the ones a rep actually opens get generated, and the API is the thing that kicks them off.

Because briefs are stored per (meeting, persona) with the content persisted as JSON and re-validated on read, the API is also the natural home for actions over a ready brief — in this build it additionally composes and (demo- or SMTP-) sends the persona-tailored brief email, and a regenerate path resets a brief to `pending` and re-schedules it so a rep can force a fresh synthesis after the source docs change. Errors are explicit HTTP responses: a missing meeting is a 404, and asking for a brief that isn't ready for the requested persona is a 409 rather than a half-empty 200.

## Acceptance criteria
```gherkin
Scenario: Status while generating, content when ready
  Given a meeting whose brief for a persona is still generating
  When the frontend fetches the brief
  Then the response reports status "generating" with no content
  And once status is "ready" the response includes the BriefContent and rendered HTML
```

```gherkin
Scenario: First view of an un-started persona generates lazily
  Given a persona brief that has no row or is "pending"
  When it is fetched for the first time
  Then it flips to "generating" and is persisted immediately
  And a background task is scheduled to generate it
  And repeated polls do not re-schedule the work
```

```gherkin
Scenario: Explicit errors for missing or not-ready briefs (edge case)
  Given a request for a brief
  When the meeting does not exist
  Then the API returns 404
  And when the brief is not ready for the requested persona, actions over it return 409
```

## Technical notes (reference)
- Key files: `backend/app/api/briefs.py`, `backend/app/models.py` (`Brief` with `content_json`/`html`/`status`/`persona`), `backend/app/schemas.py` (`BriefRead`, `BriefContent`, `Persona`)
- `GET /meetings/{id}/brief?persona=` returns `BriefRead` (status, and on ready the `content` + `html`, on error the message); lazy-generates by flipping `pending`/absent → `generating` and scheduling `generate_one_task`.
- Content is stored as a JSON string on the `Brief` row and re-validated via `BriefContent.model_validate_json` on read; briefs are keyed per (meeting, persona).
- Also exposes email preview/send over a ready brief (`_ready_brief_content` raises 404 for missing meeting, 409 when not ready). Regeneration resets the row to `pending` and re-schedules.
- POC shortcut: generation runs on FastAPI `BackgroundTasks` rather than a job queue.

## Definition of Done
- [x] `GET .../brief` returns status, plus content + HTML when ready and error message when failed
- [x] Lazy per-persona generation: `pending`/absent flips to `generating`, persists, schedules a background task
- [x] Repeated polls don't re-schedule in-flight generation
- [x] Content persisted as JSON and re-validated on read, keyed per (meeting, persona)
- [x] Missing meeting → 404, not-ready brief → 409
