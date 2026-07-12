# SalesIntel AI — Operations Runbook

Practical guide to set up, run, verify, and troubleshoot the app. For architecture
see [`../CLAUDE.md`](../CLAUDE.md); for product framing see [`BUILD_PLAN.md`](BUILD_PLAN.md).
To share a running instance with non-technical peers via a public link, see
[`SHARING.md`](SHARING.md).

The stack is two processes: a **FastAPI backend** (`:8000`) and a **Vite frontend**
(`:5173`). SQLite is the only datastore (a file, `backend/salesintel.db`). All
commands below are PowerShell on Windows.

---

## 1. Prerequisites (install once)

You need three free tools. Open **PowerShell** (Windows key → type "PowerShell" →
Enter) and install each; approve any Windows permission prompt:

```powershell
winget install Git.Git
winget install Python.Python.3.12
winget install OpenJS.NodeJS.LTS
```

**Close PowerShell and open a new window**, then confirm each prints a version:

| Need | Check command | Expected |
|---|---|---|
| Git | `git --version` | `git version 2.x` |
| Python 3.12+ | `python --version` | `Python 3.12.x` |
| Node.js LTS | `node --version` | `v20.x` or newer |
| npm | `npm --version` | `10.x` or newer |

> If `python`/`node`/`npm` are "not recognized" even in a fresh terminal, refresh
> PATH once, then retry:
> ```powershell
> $env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")
> ```

You also need a **free Gemini API key** (obtained in §2, step 4). No credit card.

---

## 2. First-time setup (from a fresh clone)

A clone from GitHub contains **only source code** — it deliberately does **not**
include the Python virtualenv (`backend/.venv`) or the secret `backend/.env`. You
create both here. This is a one-time process; day-to-day you only do §3.

### Step 1 — Get the code

```powershell
cd $HOME\Documents
git clone https://github.com/indrani-projects/salesintel-ai.git
cd salesintel-ai
```
(Least-technical alternative: on the GitHub page click **Code → Download ZIP**,
extract it, then `cd` into the extracted folder. Git clone is preferred.)

### Step 2 — Create the Python environment and install backend dependencies

```powershell
cd backend
python -m venv .venv                                             # creates backend\.venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt    # installs FastAPI, PyMuPDF, etc. (~1 min)
```
The rest of this guide always calls Python as `.\.venv\Scripts\python.exe` so you
never have to "activate" the environment.

### Step 3 — Create your `.env` from the template

```powershell
Copy-Item .env.example .env      # PowerShell copy; the Unix `cp .env.example .env` also works
```
This creates `backend\.env` (git-ignored — it holds secrets and is never uploaded).
`.env.example` stays as the committed template.

### Step 4 — Get a free Gemini API key and paste it in

1. Open **https://aistudio.google.com/apikey** and **sign in** with any Google account.
2. Click **Create API key → Create API key in new project**.
3. **Copy** the generated key.
4. Open the env file: `notepad .env`
5. Replace the placeholder on the `LLM_API_KEY=` line:
   ```
   LLM_API_KEY=AIza...paste-your-actual-key...
   ```
6. **Save** (Ctrl+S) and close Notepad.

Without a real key the server still starts, but every brief lands in `status=error`.
The default `LLM_MODEL=gemini-flash-lite-latest` works with a fresh free key; if you
ever see a 404 "model not found", pick a current model from AI Studio and update
that line.

### Step 5 — Install the frontend packages

```powershell
cd ..\frontend
npm install
```

Setup is done. Continue to §3 to start the app.

### Step 6 — Enable the git workflow (only if you'll commit changes)

Not needed just to *run* the app. If you'll make code/doc changes, enable the
repo's shared git hooks + commit identity **once per clone**, from the repo root:

```powershell
.\bootstrap.ps1        # macOS/Linux: ./bootstrap.sh
```

This sets `core.hooksPath=.githooks` (blocks direct pushes to `main`, auto-adds the
Claude co-author trailer) and the `indrani-projects` commit identity. The full
workflow — feature branch → commit → push → PR, never touching `main` directly — is
defined in **`.claude/skills/git-workflow/SKILL.md`** (the `git-workflow` skill) and
summarized in §10 below.

---

## 2b. Optional — real email sending (Gmail App Password)

The brief's **Send as email** button works with **no setup** (demo-send: it composes
and previews the email but doesn't deliver). To send a **real** email, give the
backend an SMTP account. Easiest is Gmail:

1. Turn on **2-Step Verification**: https://myaccount.google.com/security (required
   before app passwords exist).
2. Create an **App Password**: https://myaccount.google.com/apppasswords → name it
   "SalesIntel" → **Create** → copy the **16-character** code (a normal Gmail
   password will NOT work over SMTP).
3. Edit `backend\.env` and fill in:
   ```
   SMTP_HOST=smtp.gmail.com
   SMTP_PORT=587
   SMTP_USER=your.address@gmail.com
   SMTP_PASSWORD=your16charapppassword     # the App Password, no spaces
   SMTP_FROM=your.address@gmail.com
   DEFAULT_RECIPIENT=who.should.get.it@example.com   # prefills the "To" box
   ```
4. Restart the backend. Now clicking **Send as email → Confirm** delivers a real
   message. Leave `SMTP_*` blank to stay in safe demo-send mode.

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
| GET | `/meetings/{id}/brief/email/preview` | Compose the persona email (preview only, no send) |
| POST | `/meetings/{id}/brief/email/send` | Send (real if SMTP set, else demo-send) |
| POST | `/meetings/{id}/chat` | Ask a grounded question (brief must be `ready`) |
| GET | `/meetings/{id}/chat` | Chat history |

> Brief endpoints take an optional `?persona=ae|sdr|se` (defaults to the meeting's
> primary persona).

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
| `.\.venv\Scripts\python.exe` not found (fresh clone) | You skipped the venv step — a clone has no `.venv`. Run §2 Step 2: `python -m venv .venv` then `pip install -r requirements.txt`. |
| Brief errors with 404 "model not found" | `LLM_MODEL` was retired. Set a current model in `backend/.env` (default `gemini-flash-lite-latest`) and restart. |
| "Send as email" says *demo send, not delivered* | Expected with no SMTP configured. To send for real, fill `SMTP_*` in `.env` (see §2b) and restart. |
| Real email fails to send | Wrong/again-needed Gmail **App Password** (not your normal password), or 2-Step Verification off. Re-check §2b; the error text is shown in the dialog. |

---

## 9. Configuration reference (`backend/.env`)

| Var | Default | Purpose |
|---|---|---|
| `LLM_BASE_URL` | Gemini OpenAI-compat endpoint | LLM provider endpoint |
| `LLM_MODEL` | `gemini-flash-lite-latest` | Model name |
| `LLM_API_KEY` | — | Provider key (**required** for briefs) |
| `DATABASE_URL` | `sqlite:///./salesintel.db` | SQLite file (relative to `backend/`) |
| `DOCS_ROOT` | `../docs` | Source-docs root (relative to `backend/`) |
| `CORS_ORIGINS` | `localhost:5173,127.0.0.1:5173` | Comma-separated allowed frontend origins |
| `SMTP_HOST` / `SMTP_PORT` | — / `587` | Mail server for real email (blank → demo-send). See §2b |
| `SMTP_USER` / `SMTP_PASSWORD` | — | Login for real send (Gmail: an **App Password**) |
| `SMTP_FROM` | = `SMTP_USER` | "From" address on sent mail |
| `DEFAULT_RECIPIENT` | — | Prefills the "To" box in the Send-as-email dialog |
| `MOCK_LLM` | `false` | `true` → canned briefs/chat (tests/E2E; no key, no quota) |
| `MOCK_EMAIL` | `false` | `true` → never contacts a real mail server (tests/E2E) |

---

## 10. Git workflow (contributing)

**`main` is protected — never commit or push to it directly.** Every change goes:
branch off the latest `main` → commit → **rebase onto latest `main`** → push → PR → merge.

**One-time per clone:** `.\bootstrap.ps1` (or `./bootstrap.sh`) — enables the shared
hooks and the `indrani-projects` commit identity. See §2 Step 6.

**Per change:**
```powershell
# 1. Always branch off an up-to-date main
git fetch origin; git checkout main; git pull --ff-only
git checkout -b feat/<slug>              # types: feat | fix | chore | docs | refactor
# 2. ...work..., then commit (author + Claude co-author applied automatically):
git add -A
git commit -m "feat: short summary"
# 3. Rebase onto latest main BEFORE the PR (never stale), then re-run the gate:
git fetch origin; git rebase origin/main
# 4. Push (force-with-lease after a rebase) and open the PR:
git push --force-with-lease -u origin feat/<slug>
gh pr create --base main --head feat/<slug> --title "..." --body "..."
```

**Enforcement in the repo:**
| Mechanism | Effect |
|---|---|
| `.githooks/pre-push` | Rejects direct pushes to `main`/`master` (override: `SALESINTEL_ALLOW_MAIN=1`). |
| `.githooks/commit-msg` | Auto-adds `Co-Authored-By: Claude`. |
| git `user.*` | Author is always `indrani-projects <indrani.patra.projects@gmail.com>`. |

> These git hooks are **client-side** — they protect anyone working in a local clone
> that ran `bootstrap`. They do **not** stop edits made through the GitHub website or
> API; blocking those requires server-side branch protection / rulesets (a paid or
> public-repo feature). Full spec: `.claude/skills/git-workflow/SKILL.md`.
