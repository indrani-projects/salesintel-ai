# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

SalesIntel AI is a POC that auto-generates a grounded, cited **9-section pre-sales
briefing** about a prospect for a sales rep, driven by a calendar → dashboard →
brief → chatbot flow. Demo scenario: **Zoho selling to The Sleep Company**. The
value being demonstrated is the *synthesis layer* — external prospect signal
(`docs/<company>/`) × internal Zoho product knowledge (`docs/zoho/`) → an actual
pre-sales angle, not a summary. See `README.md` and `docs/BUILD_PLAN.md` for the
product framing.

Deliberate POC shortcuts (documented, intentional — don't "fix" them without
reason): no vector DB (all source text is stuffed into one LLM call), a local
`docs/` folder instead of live scraping, SQLite instead of Postgres, and FastAPI
`BackgroundTasks` instead of a job queue.

## Commands

**Backend** (from `backend/`, uses the checked-in venv):
```powershell
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --port 8000
```
API docs at http://localhost:8000/docs. Requires a real key in `backend/.env`
(copy `.env.example`, set `LLM_API_KEY`). No key → briefs go to `status=error`,
but the server still runs.

**Frontend** (from `frontend/`):
```powershell
npm run dev        # Vite dev server on :5173
npm run build      # tsc -b && vite build
npm run lint       # oxlint
```

There is **no test suite** in this repo. Verify by running the app end-to-end
(add a Sleep Company meeting → brief auto-generates → open it → chat).

> Windows note: if `node`/`npm` aren't found in a fresh PowerShell, refresh PATH:
> `$env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")`

## Architecture

**Two shared contract files are the backbone** and are treated as READ-ONLY /
append-only (`backend/app/schemas.py`, `backend/app/contracts.py`). The build was
split across parallel agents with disjoint file ownership, and these define the
seam between them:
- `schemas.py` — all API request/response Pydantic DTOs + the `SECTION_ORDER` /
  `SECTION_TITLES` for the 9 sections. **Changing a field name here ripples to
  `frontend/src/api/types.ts`** (hand-mirrored, not generated) and to the LLM's
  JSON output shape. Keep all three in sync.
- `contracts.py` — the exact service function signatures the API layer imports and
  the services implement (`generate_brief`, `answer_question`, `load_company_sources`,
  `render_html`, etc.), plus the internal `SourceDoc` dataclass.

**Backend layering** (`backend/app/`):
- `api/{meetings,briefs,chat}.py` — routers. `meetings.py` also holds the
  `generate_brief_task` background job.
- `services/` — the intelligence. `sources.py` (company/doc discovery) →
  `ingestion.py` (PyMuPDF text extraction) → `brief_engine.py` (LLM synthesis) →
  `brief_render.py` (JSON→HTML). `chat_service.py` handles grounded Q&A.
  `llm_client.py` is the single OpenAI-compatible client.
- `models.py` (SQLModel tables) vs `schemas.py` (API DTOs) are **deliberately
  separate**: `Meeting`, `Brief`, `ChatMessage` persist; the brief content is
  stored as a JSON string in `Brief.content_json` and re-validated on read.

**Brief lifecycle (async state machine).** `POST /meetings` creates the Meeting +
a `pending` Brief row, then schedules `generate_brief_task` via `BackgroundTasks`.
Status flows `pending → generating → ready | error`, mirrored on **both** the
`Meeting.brief_status` and `Brief.status`. The frontend polls `GET
/meetings/{id}/brief` (TanStack Query) to watch it flip. The background task opens
its **own** DB session and must **never raise** — any failure is caught and
written as `status=error`. Regeneration (`POST .../brief/regenerate`) resets the
row to `pending` and re-schedules.

**Company resolution.** A meeting's free-text `prospect_company` is mapped to a
`docs/<slug>/` folder by `sources.resolve_company_slug` (normalizes "The Sleep
Company" → `sleep_company`). The `zoho/` folder is special-cased: it is **never** a
prospect and is always appended as shared knowledge to every brief's source set.
`COMPANY_NAMES` in `sources.py` holds slug→display-name overrides.

**LLM integration.** Single OpenAI-compatible client (`llm_client.py`), fully
swappable via `.env` (`LLM_BASE_URL` / `LLM_MODEL` / `LLM_API_KEY`) — default is
Gemini free tier; point `LLM_BASE_URL` at Ollama for offline. `brief_engine.py`
sends **all** source text in one call, requests strict JSON (`response_format`)
with `reasoning_effort="low"` (caps Gemini's slow default thinking), and **falls
back to a plain call** if the endpoint rejects those params. Output is parsed
defensively: fences stripped, confidence/flags coerced, and **all nine sections
are guaranteed** — missing ones become low-confidence placeholders. The rep's
`why`/`agenda` are injected into the prompt so the brief's emphasis shifts (e.g.
agenda = "scaling support" → Zoho Desk gets weight); this is the demo's proof that
synthesis is real.

**Frontend** (`frontend/src/`): React 19 + Vite + TS + Tailwind, React Router,
TanStack Query, FullCalendar. `api/client.ts` is the axios client (base URL
hardcoded to `http://localhost:8000`); `api/types.ts` mirrors `schemas.py`. Pages:
`Calendar` (add meetings), `Dashboard` (brief status cards + polling), `BriefView`
(9-section render + `ChatPanel`). PDF export is **client-side** via `lib/pdf.ts`
(html2pdf.js) over the server-rendered brief HTML — no server PDF deps.

## Conventions

- Keep field names identical across `schemas.py`, `frontend/src/api/types.ts`, and
  the `brief_engine` JSON shape.
- Statuses are plain strings on the DB models but must match the `BriefStatus` enum
  values (`pending`/`generating`/`ready`/`error`).
- The brief-generation background task must stay exception-safe (catch-all →
  `status=error`); never let it crash the server.
- `docs/` is data, not code — companies are added by dropping a folder of PDFs
  under `docs/<slug>/`, no code change needed.
