# EPIC SI-2 — Calendar & Meeting Management

| Field | Value |
|---|---|
| Issue type | Epic |
| Suggested key | SI-2 |
| Status | Done |
| Priority | High |
| Component | Meetings |
| Labels | backend, frontend, api, data, ux |
| Story points (rollup) | 17 |

## Summary
The rep's entry point: a calendar where a sales rep adds an upcoming meeting, which persists it and automatically kicks off pre-sales brief generation with zero extra effort.

## Description
Calendar & Meeting Management is the front door of SalesIntel AI. A sales rep lives in their calendar, so that is where the product meets them. The rep clicks a day, fills in a short dialog (subject, prospect company, a free-text "why" and "agenda", target persona, and time), and saves. From that single action the system does two things: it persists the meeting to the database, and it immediately schedules an asynchronous job that generates the grounded, cited 9-section pre-sales brief for that prospect. The rep never presses a "generate" button — the brief is simply waiting for them by the time they open the meeting.

This epic covers the full meeting object lifecycle: a REST API to create, list, fetch, and delete meetings; the company-resolution layer that maps a rep's free-text company name (e.g. "The Sleep Company") to the correct `docs/<slug>/` knowledge folder; and the asynchronous brief-generation state machine that flows a meeting from `pending` through `generating` to `ready` or `error`. Status is mirrored on both the Meeting row and the Brief row so the frontend can poll a single endpoint and watch the brief flip to ready.

The demo value lives in two of the dialog fields. The "why" and "agenda" are free text and are injected directly into the LLM prompt, which shifts the emphasis of the resulting brief (for example, an agenda about "scaling support" pulls Zoho Desk to the foreground). This is what makes the brief feel intelligent rather than templated, and it proves the synthesis layer is real. A small seeded dropdown of known prospects keeps the POC demo frictionless while still supporting free-text entry.

Deliberate POC shortcuts apply here: brief generation runs on FastAPI `BackgroundTasks` rather than a real job queue, persistence is SQLite via SQLModel, and company knowledge is a local `docs/` folder rather than live scraping. These are intentional and documented.

## Stories in this epic
| Key | Story | Points | Priority |
|---|---|---|---|
| SI-2.1 | Meetings API (create, list, get, delete) | 3 | High |
| SI-2.2 | Company resolution & seeded prospect dropdown | 3 | Medium |
| SI-2.3 | Auto-trigger brief generation with a status state machine | 5 | Highest |
| SI-2.4 | Calendar UI (FullCalendar) | 3 | High |
| SI-2.5 | Add-meeting dialog (subject, company, why, agenda, persona, time) | 3 | High |

## Epic acceptance criteria
```gherkin
Scenario: Adding a meeting auto-generates a brief with zero extra rep effort
  Given a sales rep is on the calendar
  When they click a day and save a meeting for "The Sleep Company"
  Then the meeting is persisted
  And a brief-generation job is scheduled automatically
  And no explicit "generate" action is required from the rep
```

```gherkin
Scenario: Brief status is observable end to end
  Given a meeting has just been created
  When the frontend polls the meeting's brief endpoint
  Then it sees the status progress from pending to generating to ready
  And the same status is reflected on both the meeting and the brief
```

```gherkin
Scenario: Free-text company resolves to the correct knowledge folder
  Given the rep types "The Sleep Company" as the prospect
  When the meeting is created
  Then it is mapped to the docs/sleep_company folder
  And the shared Zoho knowledge is always included as well
```

## Out of scope
- Live web scraping of prospect signal (uses a local `docs/` folder instead)
- A production job queue (uses FastAPI `BackgroundTasks`)
- Multi-user auth, calendar sync with Google/Outlook, and recurring meetings
- Editing an existing meeting in place (delete + re-create for the POC)

## Dependencies
- SI-3 — Brief generation engine (the background task calls `brief_engine.generate_brief`)
- Shared contracts in `backend/app/schemas.py` and `backend/app/contracts.py`
