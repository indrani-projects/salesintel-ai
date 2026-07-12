# SalesIntel_AI — POC Build Plan

## Context

Team COSMOS defined SalesIntel_AI in the MVP PRD: auto-generate a pre-meeting
intelligence brief for a sales rep, grounded only in public data, with zero rep
effort. This POC demonstrates the **core value — the synthesis layer** — for a
concrete scenario: **Zoho selling to The Sleep Company** (a real, funded Indian
D2C mattress brand; a right-sized, credible Zoho prospect).

We deliberately fake the hard infrastructure (live LinkedIn/News/Crunchbase
scraping) and prove the intelligence instead. The "data ingestion layer" is a
local `docs/` folder of pre-fetched, citable source PDFs. This matches the PRD's
"as cheaply as possible to test the hypothesis" ethos.

The brief is built from **two knowledge sources** (PRD §13): the prospect docs
(`docs/sleep_company/`) and a first-party Zoho capability sheet (`docs/zoho/`).
External signal × internal product knowledge → an actual pre-sales angle, not a
summary.

**This POC delivers three features:** (1) a Calendar UI to add meetings, (2) a
Dashboard of brief status + downloads, (3) a Chatbot for follow-up Q&A.

## Output schema — the 9-section pre-sales brief

Every brief SalesIntel_AI produces fills this structure (already agreed):
1. Company Snapshot · 2. Financial & Funding Health · 3. Trigger Events / Recent
News · 4. GTM & Operating Model · 5. Pain Hypotheses → mapped to Zoho products ·
6. Tech Stack Signals · 7. Key Stakeholders · 8. Risks & Watch-outs ·
9. Analyst's Recommended Angle. Sections 5, 8, 9 are the "intelligence" — they
require inference across both knowledge sources.

## Architecture (high level)

```
┌────────────────────────── Frontend (React + Vite + shadcn/ui) ─────────────────────────┐
│  Calendar view (FullCalendar)   Dashboard (status + download)   Brief viewer + Chatbot   │
└───────────────────────────────────────── REST / JSON ───────────────────────────────────┘
                                              │
┌────────────────────────────────────── Backend (FastAPI) ─────────────────────────────────┐
│  API routers: /meetings  /briefs  /chat                                                   │
│  Services:                                                                                 │
│   • SourceProvider (LocalFolderProvider → docs/<company>/) — swappable for live fetch      │
│   • Ingestion (PyMuPDF text extraction + caching)                                          │
│   • BriefEngine (LLM: 9-section structured synthesis, grounded + cited)                    │
│   • ChatService (LLM: Q&A grounded in brief + source docs)                                 │
│   • Brief render (JSON → styled HTML); PDF export is client-side (browser)                 │
│  Storage: SQLite (SQLModel) — Meeting, Brief, ChatMessage                                   │
│  Async: FastAPI BackgroundTasks (auto-trigger brief on meeting create)                      │
└──────────────────────────────────────────────────────────────────────────────────────────┘
                                              │
        LLM provider (Groq / Ollama / Gemini — OpenAI-compatible)  +  docs/ (local source data)
```

**Data flow:** Rep adds meeting (subject, prospect company, "why", agenda, time)
→ backend stores + auto-schedules brief generation → ingestion loads that
company's docs + Zoho sheet → BriefEngine (Gemini) synthesizes the 9-section
brief, tailored to the meeting's *why/agenda* → stored, status=ready → Dashboard
shows ready + download (PDF/HTML) → rep opens brief → Chatbot answers follow-ups
grounded in the brief + sources.

**Meeting tailoring:** the rep's `why` and `agenda` are passed into the prompt so
the brief emphasizes the relevant angle (e.g. agenda = "scaling support" →
Zoho Desk gets weight). This justifies the calendar-input UX and makes the demo
feel intelligent.

## Tech stack

| Layer | Choice | Why |
|---|---|---|
| Frontend build | React + Vite + TypeScript | Fast, minimal config, instant HMR |
| UI kit | Tailwind + shadcn/ui | Premium modern look, drop-in components, low effort |
| Calendar | FullCalendar (React) | Best-looking calendar, event add/edit out of the box |
| Data/state | TanStack Query | API fetching + easy status polling |
| Backend | FastAPI (Python) | Async, minimal boilerplate, ideal for AI orchestration |
| LLM | OpenAI-compatible client → **Gemini free tier** (default, uses existing Google account); Ollama (local/offline) or Groq free tier as drop-in swaps | Free for a POC; provider swapped via `.env` only |
| PDF parsing | PyMuPDF (fitz) | Robust text extraction from the source PDFs |
| Brief export | html2pdf.js (client-side) | HTML→PDF in the browser; **no Windows GTK/system deps** |
| Database | SQLite + SQLModel | Zero-setup, file-based, perfect for POC |
| Async jobs | FastAPI BackgroundTasks | No extra infra (Celery/queue is the scale path) |
| Config | pydantic-settings + .env | API key management |

**Deliberate POC simplifications (call these out in the presentation):**
no vector DB (docs stuffed into context — RAG is the scale path); local folder
instead of live scraping; SQLite instead of Postgres; BackgroundTasks instead of
a job queue. Interfaces (`SourceProvider`) are kept clean so each can be swapped.

## Repo structure

```
SalesIntel_AI/
  docs/                      # existing source data (sleep_company/, zoho/)
  backend/
    app/
      main.py                # FastAPI app + CORS
      config.py              # settings, LLM_BASE_URL/MODEL/API_KEY (Gemini)
      db.py                  # SQLite engine/session
      models.py              # Meeting, Brief, ChatMessage (SQLModel)
      schemas.py             # request/response + 9-section brief schema (Phase-0 contract)
      api/ meetings.py briefs.py chat.py
      services/
        sources.py           # SourceProvider / LocalFolderProvider
        ingestion.py         # PyMuPDF extraction + cache
        brief_engine.py      # Gemini synthesis (9-section, grounded, cited)
        chat_service.py      # Gemini Q&A grounded in brief + docs
        brief_render.py      # brief JSON → styled HTML
    requirements.txt
    .env.example
  frontend/
    src/
      api/client.ts          # typed API client
      pages/ Calendar.tsx Dashboard.tsx BriefView.tsx
      components/ MeetingDialog.tsx BriefCard.tsx ChatPanel.tsx
      lib/pdf.ts             # html2pdf.js export
    package.json
  docs/PROJECT_TRACKER.html  # visual epic/story tracker (created first, Lead-maintained)
```

## Execution model & environment

- **Environment: native** (no Docker) — Python + Node installed and run directly
  on the machine. Fastest to iterate/debug for a single-machine POC.
- **Build team: Lead + delegated subagents.** I act as **Lead** — I own the
  Phase-0 contract, integration, verification, and the tracker. Three specialized
  subagents then build bounded epics **in parallel** against the locked contract.
- **Conflict avoidance:** file ownership is **disjoint** so parallel agents never
  touch the same files — Backend Agent = `backend/app/{main,config,db,models,api}`;
  AI-Engine Agent = `backend/app/services/`; Frontend Agent = `frontend/`. The
  shared `schemas.py` is authored by the Lead in Phase 0 and treated read-only by
  the agents. The Lead integrates and runs end-to-end verification.

## Project tracker (HTML)

`docs/PROJECT_TRACKER.html` — a **self-contained, styled page you open
in a browser** (no server, no markdown wall). Table/kanban of every epic + story
with: Owner (agent), Phase, and Status (`Not started` / `In progress` / `Done` /
`Blocked`), plus a progress bar. **Created first (Story 0.2)** and updated by the
Lead as each story completes. This is the single source of truth for progress.

## Phase-wise execution plan (epics → stories → owner)

### Phase 0 — Foundation · *Owner: Lead* · (blocks all parallel work)
- **E0 — Setup & Contract**
  - S0.1 Repo skeleton (`backend/`, `frontend/`), `.gitignore`, `README`
  - S0.2 **`PROJECT_TRACKER.html`** (visual tracker) — created first
  - S0.3 **Lock API contract + `schemas.py`** — Meeting, 9-section Brief (JSON),
    ChatMessage; endpoint list. The interface all agents build against.
  - S0.4 `.env.example` (Gemini `LLM_*` vars), baseline `requirements.txt` /
    `package.json`

### Phase 1 — Parallel build · *3 subagents, against the locked contract*

**Backend Agent** — owns `backend/app/{main,config,db,models,api}`
- **E1 — Backend skeleton & data**
  - S1.1 FastAPI app + CORS + `/health`
  - S1.2 `config.py` (pydantic-settings, `LLM_*`)
  - S1.3 SQLite + SQLModel models (Meeting, Brief, ChatMessage)
- **E2 — APIs & orchestration**
  - S2.1 Meetings router (CRUD)
  - S2.2 Briefs router (status, fetch brief HTML)
  - S2.3 Chat router (post question + per-meeting history)
  - S2.4 BackgroundTasks auto-trigger on meeting create; status transitions
    (`pending → generating → ready/error`)

**AI-Engine Agent** — owns `backend/app/services/`
- **E3 — Ingestion**
  - S3.1 `SourceProvider` + `LocalFolderProvider` (`docs/<company>/`)
  - S3.2 PyMuPDF text extraction + per-company cache
- **E4 — Brief synthesis**
  - S4.1 Gemini client (OpenAI-compatible) wrapper
  - S4.2 9-section prompt: grounded + cited, confidence flags, tailored to
    meeting `why`/`agenda`
  - S4.3 Brief JSON → styled HTML render (`brief_render.py`)
- **E5 — Chatbot**
  - S5.1 `ChatService` grounded in brief + docs; graceful "not in sources" decline

**Frontend Agent** — owns `frontend/`
- **E6 — Scaffold & shell**
  - S6.1 Vite + React + TS + Tailwind + shadcn/ui init
  - S6.2 Typed API client + TanStack Query
  - S6.3 App layout + nav
- **E7 — Calendar**
  - S7.1 FullCalendar integration
  - S7.2 Add-meeting dialog (subject, company dropdown, why, agenda, time)
- **E8 — Dashboard**
  - S8.1 Meeting/brief status cards + polling
  - S8.2 Download brief (`html2pdf.js`) + HTML view
- **E9 — Brief view + Chatbot**
  - S9.1 Brief renderer (9 sections, citations, confidence flags)
  - S9.2 Chat panel

### Phase 2 — Integration & demo readiness · *Owner: Lead*
- **E10 — Integration & E2E**
  - S10.1 Wire FE ↔ BE, status polling, CORS
  - S10.2 End-to-end run: add Sleep Company meeting → brief → download → chat
  - S10.3 Empty / loading / error states, demo polish
- **E11 — Demo readiness**
  - S11.1 Known-company dropdown seeded (The Sleep Company → `docs/sleep_company`)
  - S11.2 README run steps; dry-run the demo narrative
  - S11.3 Final tracker update → all `Done`

**Critical path:** Phase 0 (Lead) → Phase 1 (3 agents in parallel) → Phase 2
(Lead). Frontend can build against the contract with mock data before the backend
is wired, so it need not wait on Phase 1 backend completion.

## LLM provider (cost-conscious, swappable)
Backend uses a single **OpenAI-compatible client**; provider chosen via `.env`
(`LLM_BASE_URL`, `LLM_MODEL`, `LLM_API_KEY`). No code change to switch.
- **Default: Google Gemini free tier** — no new account (uses existing Google
  login), key from AI Studio, OpenAI-compatible endpoint. Model: Gemini Flash
  (2.5/3 Flash). Free-tier limits (~10–15 RPM, 250K–1M TPM, 1,500 req/day) vastly
  exceed POC needs; 1M-token context fits all docs in one call. Note: free tier
  may use prompts for model improvement — fine here (public data only).
- **Local/offline swap: Ollama** — `$0`, private, no account; point base_url at
  `http://localhost:11434/v1`. Best on a GPU; small models are weaker at strict
  citation grounding.
- **Alt: Groq free tier** — free (needs signup), very fast, Llama 3.3 70B-class.
- Anthropic Claude remains a one-line swap if higher brief quality is ever wanted
  (~$0.01–0.15 per brief — cheap, but not needed for the POC).

## Prerequisites & setup (who does what)
- **Python 3.12 + Node.js LTS** — *Lead installs* via winget (confirmed available,
  v1.29; Python/Node currently absent). `winget install Python.Python.3.12` and
  `winget install OpenJS.NodeJS.LTS`. User may need to approve a Windows UAC prompt.
- **Gemini API key** — *user provides* (only true blocker): create at
  aistudio.google.com/apikey, paste into `backend/.env` (`LLM_API_KEY=...`). Lead
  scaffolds `.env` with the single line to fill. Offline alternative: Ollama.
- Company-name → folder convention (`docs/sleep_company/`); a small dropdown of
  known prospects seeded in the meeting dialog for the POC.

## Verification
- `uvicorn app.main:app --reload` + `npm run dev`; open the app.
- Add a meeting "Meeting with The Sleep Company" (why + agenda) in the Calendar.
- Confirm brief auto-generates (status pending→ready) and fills all 9 sections
  with citations to the real source PDFs; download the PDF.
- Change the agenda and regenerate — verify the emphasis shifts (e.g. Desk vs CRM).
- Ask the Chatbot a question answerable from the docs (e.g. "who led their last
  round?") and one that isn't — verify it grounds/cites and declines gracefully.
```