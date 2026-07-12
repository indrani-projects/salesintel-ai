# SI-1.1 — Repository skeleton, environment & tooling setup

| Field | Value |
|---|---|
| Issue type | Story |
| Parent epic | SI-1 — Platform Foundation & Data Contract |
| Status | Done |
| Priority | High |
| Story points | 3 |
| Component | Platform |
| Labels | infra, backend, frontend |

## User story
As a developer joining the SalesIntel AI POC, I want a ready-to-run repository with the backend and frontend scaffolded and their dependencies pinned, so that I can start the whole app end to end in minutes without hunting for setup steps.

## Description
This story sets up the shape of the project: a Python FastAPI backend and a React + Vite + TypeScript frontend living side by side in one repository, plus the top-level documentation and ignore rules that make the checkout clean and self-explanatory. The goal is that a reviewer can go from a fresh clone to a running demo (add a Sleep Company meeting, watch a brief generate, open it, chat with Scout) by following the README alone.

The backend dependencies are pinned in `requirements.txt` (FastAPI, SQLModel, pydantic-settings, the OpenAI-compatible client, PyMuPDF for PDF ingestion, and the uvicorn server). The frontend dependencies and scripts live in `package.json` (React 19, Vite, TypeScript, Tailwind, React Router, TanStack Query, FullCalendar, html2pdf.js), exposing the standard `dev`, `build`, and `lint` commands. The README frames the product and gives the exact PowerShell commands to run each half.

Two deliberate POC conventions are baked in here, both intentional and documented. First, the environment is **native Windows** (not Docker): the commands are PowerShell, and there is a note about refreshing PATH in a fresh shell if `node`/`npm` aren't found. Second, the backend uses a **checked-in virtual environment** so the demo runs against a known-good set of packages without a separate install step. The `.gitignore` is tuned to keep the repo clean (build artifacts, caches, the local SQLite database, and secret `.env` files stay out) while allowing the demo to remain reproducible.

## Acceptance criteria

**Scenario: Backend starts from the checked-in environment**
```gherkin
Given a fresh clone on a Windows machine
When the developer runs the documented uvicorn command from the backend directory
Then the FastAPI server starts and serves interactive API docs at /docs
```

**Scenario: Frontend dev server starts**
```gherkin
Given the frontend dependencies from package.json
When the developer runs the dev script from the frontend directory
Then the Vite dev server serves the app on port 5173
```

**Scenario: The README is enough to run the demo**
```gherkin
Given only the README in the repository root
When a new reviewer follows it
Then they can start both halves and complete the calendar to brief to chat flow without other instructions
```

**Scenario: Secrets and local artifacts are not committed**
```gherkin
Given the .gitignore rules
When a developer builds the app and creates a local .env and SQLite database
Then those files are ignored and never appear in version control
```

## Technical notes (reference)
- Key files: `README.md`, `.gitignore`, `backend/requirements.txt`, `frontend/package.json`
- Native-Windows demo: commands are PowerShell; PATH-refresh note in the README for fresh shells.
- POC shortcut (intentional): a checked-in Python venv under `backend/.venv` so the demo runs against a known-good dependency set.
- Frontend scaffolded with Vite (React + TS); exposes `npm run dev` / `npm run build` (tsc -b && vite build) / `npm run lint` (oxlint).

## Definition of Done
- [x] Backend `requirements.txt` pins FastAPI, SQLModel, pydantic-settings, the OpenAI-compatible client, PyMuPDF, and uvicorn.
- [x] Frontend `package.json` defines React 19 + Vite + TS + Tailwind stack with dev/build/lint scripts.
- [x] `README.md` documents the product and the exact run commands for both halves.
- [x] `.gitignore` excludes build artifacts, caches, the local SQLite DB, and `.env` secrets.
- [x] A fresh clone runs the full calendar to brief to chat flow following the README alone.
