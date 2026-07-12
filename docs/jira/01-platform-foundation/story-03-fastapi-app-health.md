# SI-1.3 — FastAPI application shell, CORS & health endpoint

| Field | Value |
|---|---|
| Issue type | Story |
| Parent epic | SI-1 — Platform Foundation & Data Contract |
| Status | Done |
| Priority | High |
| Story points | 2 |
| Component | Platform |
| Labels | backend, api |

## User story
As a frontend developer and as an operator, I want a single FastAPI application that wires up all routers, allows the browser app to call it, and exposes a health probe, so that the UI can reach the API and I can confirm the server (and its LLM config) is up.

## Description
This story assembles the FastAPI application shell — the object that ties every backend feature together into one running web server. It creates the app, registers the three routers (meetings, briefs, chat), initializes the database on startup, and configures Cross-Origin Resource Sharing so the browser-based frontend running on a different port is allowed to call the API. Without this shell there is nothing to run; with it, the whole backend comes online with one command.

CORS is driven by configuration rather than hard-coded: the allowed origins come from the `CORS_ORIGINS` setting (which lists the Vite dev server's addresses by default), so the same code works whether the frontend runs on localhost or a tunneled host without editing source. Credentials, all methods, and all headers are permitted for those origins, which is appropriate for a local POC.

The `/health` endpoint is deliberately simple but useful: it returns an "ok" status plus a boolean saying whether an LLM key is configured. That second signal matters because the app is designed to start and stay healthy even with no LLM key — the health probe is how a developer or a smoke test confirms the server is alive and whether brief generation will actually be able to call the model. This keeps the demo debuggable: a green health check with `llm_configured = false` immediately explains why briefs would end up in an error state.

## Acceptance criteria

**Scenario: The API comes online with all routers**
```gherkin
Given the FastAPI application shell
When the server is started
Then the meetings, briefs, and chat routes are all served
And the database is initialized on startup
```

**Scenario: The browser app is allowed to call the API**
```gherkin
Given CORS origins configured for the Vite dev server
When the frontend on port 5173 makes a request to the backend
Then the request is permitted by CORS
```

**Scenario: Health reports server and LLM status**
```gherkin
Given the running server
When a client calls GET /health
Then it receives status "ok"
And a llm_configured flag reflecting whether an LLM key is set
```

**Scenario: Health works even without an LLM key**
```gherkin
Given no LLM API key is configured
When a client calls GET /health
Then the server responds "ok" with llm_configured = false rather than failing
```

## Technical notes (reference)
- Key files: `backend/app/main.py`
- CORS allowed origins come from `settings.cors_list`, derived from the `CORS_ORIGINS` env value.
- On startup the app calls `init_db()` to create tables.
- `/health` returns the `HealthResponse` DTO (`status`, `llm_configured`) defined in `schemas.py`.
- Interactive API docs are available at `/docs` (FastAPI built-in).

## Definition of Done
- [x] FastAPI app created with title and CORS middleware wired from configuration.
- [x] Meetings, briefs, and chat routers registered.
- [x] Database initialized on application startup.
- [x] `/health` endpoint returns status and `llm_configured`.
- [x] Server starts and health responds even with no LLM key configured.
