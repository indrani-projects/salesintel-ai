# SalesIntel AI — POC

Pre-sales intelligence for a sales rep: auto-generate a grounded, cited **9-section
briefing** about a prospect from public source documents, delivered through a
calendar → dashboard → brief → chatbot flow.

**Demo scenario:** Zoho selling to **The Sleep Company** (a real, funded Indian D2C
mattress brand). Source docs live in `docs/sleep_company/` (prospect) and
`docs/zoho/` (our product knowledge). The brief synthesizes *external signal ×
internal product knowledge* into an actual pre-sales angle.

## Architecture

- **Frontend** — React + Vite + TypeScript + Tailwind, FullCalendar, TanStack Query (`frontend/`)
- **Backend** — FastAPI + SQLite (SQLModel), background brief generation (`backend/`)
- **LLM** — OpenAI-compatible client → Google Gemini (`gemini-flash-latest`), swappable via `.env`
- **Ingestion** — PyMuPDF over the local `docs/<company>/` folder (stands in for live scraping)

See [docs/BUILD_PLAN.md](docs/BUILD_PLAN.md) for the full plan and
[PROJECT_TRACKER.html](PROJECT_TRACKER.html) for build status.

## Prerequisites

- Python 3.12+ and Node.js LTS (installed)
- A Gemini API key in `backend/.env` (`LLM_API_KEY=...`) — get one at
  https://aistudio.google.com/apikey

## Run

Open two terminals.

**1) Backend** (http://localhost:8000)
```powershell
cd backend
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --port 8000
```
API docs at http://localhost:8000/docs

**2) Frontend** (http://localhost:5173)
```powershell
cd frontend
npm run dev
```
Open http://localhost:5173

> Note: if `node`/`npm` aren't found in a fresh PowerShell, refresh PATH first:
> `$env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")`

## Demo flow

1. **Calendar** — click a day, add a meeting: subject, prospect = *The Sleep
   Company*, a "why", and an agenda. Save.
2. The brief **auto-generates** in the background (status pending → generating → ready).
3. **Dashboard** — watch the card flip to *ready*; open the brief.
4. **Brief** — 9 sections, each claim cited `[S#]`, low-confidence items flagged.
   Download as PDF.
5. **Chatbot** — ask a follow-up ("Who led their last funding round?"). It answers
   grounded in the sources, or declines when the answer isn't there.

Changing the **agenda** shifts the brief's emphasis (e.g. support-scaling → Zoho
Desk; pipeline → Zoho CRM), which shows the synthesis is real, not canned.

## Configuration (`backend/.env`)

| Var | Purpose |
|---|---|
| `LLM_BASE_URL` | OpenAI-compatible endpoint (default: Gemini) |
| `LLM_MODEL` | e.g. `gemini-flash-latest` |
| `LLM_API_KEY` | your provider key |
| `DOCS_ROOT` | source docs root (default `../docs`) |
| `CORS_ORIGINS` | allowed frontend origins |

To run fully offline, point `LLM_BASE_URL` at a local Ollama
(`http://localhost:11434/v1`) — no other code changes.
