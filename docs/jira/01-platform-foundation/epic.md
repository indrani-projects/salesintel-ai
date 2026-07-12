# EPIC SI-1 — Platform Foundation & Data Contract

| Field | Value |
|---|---|
| Issue type | Epic |
| Suggested key | SI-1 |
| Status | Done |
| Priority | Highest |
| Component | Platform |
| Labels | backend, frontend, infra, api, data |
| Story points (rollup) | 16 |

## Summary
Establish the repository, tooling, locked API/data contract, FastAPI application shell, configuration, and SQLite persistence layer that every other part of SalesIntel AI is built on.

## Description
SalesIntel AI auto-generates a grounded, cited 9-section pre-sales briefing about a prospect so a sales rep can walk into a meeting prepared. Before any of that intelligence can be built, the product needs a solid foundation: a runnable repository, a shared "language" that the backend, the AI engine, and the frontend all agree on, a live web server, environment-driven configuration, and somewhere to store meetings and briefs. This epic delivers that foundation.

The centerpiece is the **shared data contract**. The product was built by several agents working in parallel with disjoint file ownership, so the seam between them had to be nailed down first and then frozen. Two files — `schemas.py` (all API request/response shapes plus the canonical order and titles of the 9 brief sections) and `contracts.py` (the exact service function signatures) — are treated as read-only / append-only. Every field name in `schemas.py` is hand-mirrored in the frontend's TypeScript types and in the JSON shape the LLM is asked to return; keeping those three in sync is the single most important discipline in the codebase.

Around that contract sits the plumbing: a FastAPI app that wires CORS and a health probe, a `pydantic-settings` configuration layer that makes the LLM provider swappable via `.env` (default Google Gemini flash, but pointable at any OpenAI-compatible endpoint including a local Ollama), and a SQLite persistence layer (via SQLModel) holding Meeting, Brief, and ChatMessage rows. The brief's structured content is stored as a JSON string on the Brief row and re-validated on read, keeping the persistence tables deliberately separate from the API DTOs.

Value delivered: a stable, self-consistent platform on which the calendar, dashboard, brief-generation, and chatbot features can all be built independently without stepping on each other. The deliberate POC shortcuts here (SQLite instead of Postgres, a local `docs/` folder instead of live scraping, a checked-in Python venv for a native-Windows demo) are intentional and documented, chosen to keep the demo simple and reproducible.

## Stories in this epic
| Key | Story | Points | Priority |
|---|---|---|---|
| SI-1.1 | Repository skeleton, environment & tooling setup | 3 | High |
| SI-1.2 | Shared API contract & 9-section brief schema | 5 | Highest |
| SI-1.3 | FastAPI application shell, CORS & health endpoint | 2 | High |
| SI-1.4 | Configuration & swappable LLM provider settings | 3 | High |
| SI-1.5 | SQLite persistence layer (Meeting, Brief, ChatMessage) | 3 | High |

## Epic acceptance criteria

**Scenario: The application runs end to end from a clean checkout**
```gherkin
Given a fresh clone of the repository on a Windows machine
When a developer starts the backend with uvicorn and the frontend with the Vite dev server
Then the FastAPI server serves interactive API docs and a working /health endpoint
And the Vite app loads in the browser and can reach the backend across CORS
```

**Scenario: The data contract is single-sourced and self-consistent**
```gherkin
Given the shared schemas define the 9 brief sections and all API DTOs
When the backend, the AI engine, and the frontend each produce or consume a brief
Then all three use identical field names and the same section order and titles
And the brief content stored in the database re-validates cleanly against the schema on read
```

**Scenario: The server survives a missing LLM key**
```gherkin
Given no LLM API key is configured in the environment
When the server starts and a brief is requested
Then the server starts and stays healthy
And the health endpoint reports llm_configured = false
And brief generation fails gracefully to status = error rather than crashing the server
```

## Out of scope
- The actual intelligence (source ingestion, LLM synthesis, chatbot answers) — built on this foundation in later epics.
- Production-grade persistence (Postgres) — SQLite is an intentional POC shortcut.
- Live web scraping of prospect data — replaced by a local `docs/` folder for the POC.
- A job queue for background generation — FastAPI BackgroundTasks is used instead, intentionally.
- Authentication / multi-tenant user accounts.

## Dependencies
- None. This is the foundational epic that all other epics depend on.
