# SalesIntel AI — Operations Runbook

Practical guide to set up, run, verify, and troubleshoot the app. For architecture
see [`../CLAUDE.md`](../CLAUDE.md); for product framing see [`BUILD_PLAN.md`](BUILD_PLAN.md).

The stack is two processes: a **FastAPI backend** (`:8000`) and a **Vite frontend**
(`:5173`). SQLite is the only datastore (a file, `backend/salesintel.db`). All
commands below are PowerShell on Windows.

---

## 1. Prerequisites

| Need | Check | Get it |
|---|---|---|
| Python 3.12+ | `python --version` | `winget install Python.Python.3.12` |
| Node.js LTS | `node --version` | `winget install OpenJS.NodeJS.LTS` |
| LLM API key | — | Gemini free key at https://aistudio.google.com/apikey |

> If `node`/`npm` are "not recognized" in a fresh terminal, refresh PATH first:
> ```powershell
> $env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")
> ```

---

## 2. First-time setup

**Backend** — a virtualenv is already checked in at `backend/.venv`. Verify deps
and create the `.env`:

```powershell
cd backend
.\.venv\Scripts\python.exe -m pip install -r requirements.txt   # only if venv is stale/missing
Copy-Item .env.example .env
```

Then edit `backend/.env` and set your key:
```
LLM_API_KEY=<your-gemini-key>
```
`.env` is gitignored — never commit it. Without a real key the server still starts,
but every brief lands in `status=error`.

**Frontend** — install packages:
```powershell
cd frontend
npm install
```

---

## 3. Start the app

Open **two terminals**.

**Terminal 1 — backend:**
```powershell
cd backend
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --port 8000
```

**Terminal 2 — frontend:**
```powershell
cd frontend
npm run dev
```

Then open **http://localhost:5173**.

| Surface | URL |
|---|---|
| App (frontend) | http://localhost:5173 |
| API root | http://localhost:8000 |
| Interactive API docs (Swagger) | http://localhost:8000/docs |
| Health check | http://localhost:8000/health |

The SQLite DB and tables are created automatically on backend startup
(`init_db()`), so no migration step is needed.

---

## 4. Health & readiness checks

```powershell
# Is the API up and is the LLM key configured?
Invoke-RestMethod http://localhost:8000/health
# -> status = "ok", llm_configured = true   (false means .env key is missing/placeholder)

# Are prospect companies discoverable from docs/?
Invoke-RestMethod http://localhost:8000/companies
# -> should include slug "sleep_company"
```

If `llm_configured` is `false`, briefs will fail — fix `backend/.env` and restart
the backend.

---

## 5. Demo / smoke-test flow

This is both the demo script and the end-to-end verification.

1. **Calendar** — click a day, add a meeting: subject, prospect = *The Sleep
   Company*, a "why", an agenda, and time. Save.
2. The brief **auto-generates** in the background. Watch status go
   `pending → generating → ready` (typically ~35s with Gemini flash).
3. **Dashboard** — the card flips to *ready*; open the brief.
4. **Brief** — confirm all **9 sections** render, claims carry `[S#]` citations,
   and low-confidence items are flagged. Download as PDF (client-side).
5. **Chatbot** — ask something answerable from the docs ("Who led their last
   funding round?") and something not in the docs — verify it grounds/cites the
   first and gracefully declines the second.
6. **Tailoring proof** — change the agenda and regenerate; the emphasis should
   shift (e.g. support-scaling → Zoho Desk; pipeline → Zoho CRM).

---

## 6. Common operations

**Reset the database** (wipe all meetings/briefs/chats — start clean for a demo):
```powershell
# Stop the backend first, then:
Remove-Item backend\salesintel.db -ErrorAction SilentlyContinue
# Restart the backend; tables are recreated empty.
```

**Regenerate a brief** without recreating the meeting — use the "regenerate"
control in the UI, or:
```powershell
Invoke-RestMethod -Method Post http://localhost:8000/meetings/<id>/brief/regenerate
```

**Add a new prospect company** — drop a folder of source docs (`.pdf`, `.md`,
`.txt`, `.html`) under `docs/<slug>/`. No code change needed; it appears in the
`/companies` dropdown automatically. To give it a nice display name, add a
`slug → "Name"` entry to `COMPANY_NAMES` in `backend/app/services/sources.py`.
The `docs/zoho/` folder is shared product knowledge and is never a prospect.

**Switch LLM provider** — edit `backend/.env` and restart the backend. No code
change. Offline example (Ollama):
```
LLM_BASE_URL=http://localhost:11434/v1
LLM_MODEL=llama3.1:8b
LLM_API_KEY=ollama
```

**Lint / build the frontend:**
```powershell
cd frontend
npm run lint
npm run build
```

---

## 7. API reference (quick)

| Method | Path | Purpose |
|---|---|---|
| GET | `/health` | Liveness + whether LLM key is set |
| GET | `/companies` | Prospect dropdown (scans `docs/`) |
| POST | `/meetings` | Create meeting → auto-schedules brief |
| GET | `/meetings` | List meetings |
| GET | `/meetings/{id}` | One meeting (includes `brief_status`) |
| DELETE | `/meetings/{id}` | Delete meeting + its brief + chat |
| POST | `/meetings/{id}/brief/regenerate` | Reset + regenerate brief |
| GET | `/meetings/{id}/brief` | Brief status / content / HTML / error |
| POST | `/meetings/{id}/chat` | Ask a grounded question (brief must be `ready`) |
| GET | `/meetings/{id}/chat` | Chat history |

---

## 8. Troubleshooting

| Symptom | Likely cause / fix |
|---|---|
| Brief stuck at `error` | Missing/invalid `LLM_API_KEY`, or provider unreachable. Check `/health` → `llm_configured`. Open `/meetings/{id}/brief` to read the `error` string. |
| Brief `error` mentions JSON/parse | LLM returned non-JSON. It retries once automatically; a persistent failure usually means a weak model — try a stronger `LLM_MODEL`. |
| `/companies` is empty | `DOCS_ROOT` wrong or `docs/` has no company folders. Default `DOCS_ROOT=../docs` is relative to `backend/`. |
| Frontend loads but all calls fail (CORS/network) | Backend not running on `:8000`, or origin not in `CORS_ORIGINS`. The client base URL is hardcoded to `http://localhost:8000` in `frontend/src/api/client.ts`. |
| `POST /chat` returns 409 | Brief isn't `ready` yet — wait for generation or regenerate. |
| Generation very slow (minutes) | A reasoning-heavy model without `reasoning_effort` support. `brief_engine` sets `reasoning_effort="low"` for Gemini; other providers ignore it. |
| `node`/`npm` not found | Refresh PATH (see Prerequisites) or reopen the terminal. |
| Port already in use | Change `--port` (backend) or run `npm run dev -- --port <n>` (frontend); keep `CORS_ORIGINS` / client base URL in sync. |

---

## 9. Configuration reference (`backend/.env`)

| Var | Default | Purpose |
|---|---|---|
| `LLM_BASE_URL` | Gemini OpenAI-compat endpoint | LLM provider endpoint |
| `LLM_MODEL` | `gemini-2.5-flash` | Model name |
| `LLM_API_KEY` | — | Provider key (**required** for briefs) |
| `DATABASE_URL` | `sqlite:///./salesintel.db` | SQLite file (relative to `backend/`) |
| `DOCS_ROOT` | `../docs` | Source-docs root (relative to `backend/`) |
| `CORS_ORIGINS` | `localhost:5173,127.0.0.1:5173` | Comma-separated allowed frontend origins |
