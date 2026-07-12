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
- **LLM** — OpenAI-compatible client → Google Gemini (`gemini-flash-lite-latest`), swappable via `.env`
- **Ingestion** — PyMuPDF over the local `docs/<company>/` folder (stands in for live scraping)

See [docs/BUILD_PLAN.md](docs/BUILD_PLAN.md) for the full plan and
[docs/PROJECT_TRACKER.html](docs/PROJECT_TRACKER.html) for build status.

## Get it running on your machine (first-time setup)

**New to this / not very technical? Follow every step in order and copy each
command exactly.** Everything here is free. These instructions are for **Windows**
(PowerShell). For an even more hand-held version — with per-step checks, an offline
option, and the real-email setup — see **[docs/RUNBOOK.md](docs/RUNBOOK.md)**.

> **How to open a terminal:** press the **Windows key**, type **PowerShell**, press
> **Enter**. A blue window opens — that's where you paste the commands below (right-click
> pastes). Run one command at a time and wait for it to finish.

### Step 0 — Install the three free tools (one time only)

In PowerShell, run these three commands one by one. Click **Yes** if Windows asks
for permission.

```powershell
winget install Git.Git
winget install Python.Python.3.12
winget install OpenJS.NodeJS.LTS
```

**Then close PowerShell and open a NEW PowerShell window** (so it picks up the newly
installed tools). Verify all three work — each should print a version number:

```powershell
git --version
python --version
node --version
```

> If `python` or `node` says *"not recognized"* even in a new window, run this line
> once to refresh the terminal, then try again:
> ```powershell
> $env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")
> ```

### Step 1 — Download the code

Pick a folder to keep the project in (this example uses your Documents folder),
then clone the repo:

```powershell
cd $HOME\Documents
git clone https://github.com/indrani-projects/salesintel-ai.git
cd salesintel-ai
```

You're now inside the project folder. All remaining commands are run from here.

### Step 2 — Set up the backend (Python)

The project does **not** include the Python environment or the secret `.env` file —
you create both now.

```powershell
cd backend
python -m venv .venv                                     # create the virtualenv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt   # install dependencies (takes a minute)
Copy-Item .env.example .env                              # create your own .env from the template
```

> `Copy-Item` is PowerShell's copy command (the Mac/Linux `cp` also works here:
> `cp .env.example .env`). This makes a real `.env` file that is **yours** and is
> never uploaded to GitHub (it's git-ignored on purpose, because it holds secrets).

### Step 3 — Get a free Gemini API key and put it in `.env`

The app needs an AI key to write the briefs. It's free.

1. Open **https://aistudio.google.com/apikey** in your browser.
2. **Sign in** with any Google account.
3. Click **Create API key** → **Create API key in new project**.
4. A long key appears (it starts with letters/numbers). Click **Copy**.
5. Open the file `backend\.env` in Notepad:
   ```powershell
   notepad .env
   ```
6. Find the line `LLM_API_KEY=PASTE_YOUR_GEMINI_KEY_HERE` and replace the
   placeholder with your key, so it reads e.g. `LLM_API_KEY=AIza...your-key...`.
   **Save** (Ctrl+S) and close Notepad.

That's the only key required. (Real email sending is optional — see
[docs/RUNBOOK.md](docs/RUNBOOK.md) §2b.)

### Step 4 — Set up the frontend (the web app)

Open a **second** PowerShell window, go to the project's `frontend` folder, and
install its packages:

```powershell
cd $HOME\Documents\salesintel-ai\frontend
npm install
```

### Step 5 — Start both servers (one command)

From the **repo root**, run:
```powershell
.\stack.ps1            # starts backend + frontend, waits until healthy, prints the URLs
```
(macOS/Linux: `./stack.sh`.) That's it — leave that window open. To stop everything:
`.\stack.ps1 stop`. Other actions: `.\stack.ps1 status` / `.\stack.ps1 restart`.

<details><summary>Prefer two manual terminals (live console output)?</summary>

**Window 1 — backend** (from `backend`): `.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --port 8000`
**Window 2 — frontend** (from `frontend`): `npm run dev`
</details>

### Step 6 — Open the app

Open **http://localhost:5173** in your browser. To confirm the AI key is wired up,
open **http://localhost:8000/health** — it should show `"llm_configured": true`. If
it says `false`, your key in `backend\.env` is missing or still the placeholder —
fix it and re-run `.\stack.ps1 restart`.

Next time, you only repeat **Step 5** (`.\stack.ps1`) — the setup steps are one-time.

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

## Accessing the app (shared link)

No install needed. When the app owner shares a link (an `https://…` URL), just
open it in any browser — the full app runs there: add a meeting, watch the brief
generate, read the 9 sections, and chat with Scout, exactly as in the demo flow
above. The link works only while the owner has the app running.

> Running it yourself and want to share it with others? See **[docs/SHARING.md](docs/SHARING.md)**.

## Sending briefs as email (optional)

Every brief has a **Send as email** button (one per persona). Out of the box it
runs in **demo-send**: it composes and previews the email but doesn't actually
deliver — so it works with zero setup and is safe for a live demo. To send a **real**
email, add SMTP credentials (a Gmail App Password) to `backend/.env` — full
step-by-step in **[docs/RUNBOOK.md](docs/RUNBOOK.md) §2b (Optional: real email)**.

## Configuration (`backend/.env`)

Created in Step 2 above by copying `backend/.env.example`. Key settings:

| Var | Purpose |
|---|---|
| `LLM_API_KEY` | **Required.** Your Gemini key (Step 3). Without it, briefs error. |
| `LLM_MODEL` | Model name (default `gemini-flash-lite-latest`) |
| `LLM_BASE_URL` | OpenAI-compatible endpoint (default: Gemini) |
| `DOCS_ROOT` | source docs root (default `../docs`) |
| `CORS_ORIGINS` | allowed frontend origins |
| `SMTP_*`, `DEFAULT_RECIPIENT` | Optional — real email sending (see RUNBOOK §2) |

To run fully offline, point `LLM_BASE_URL` at a local Ollama
(`http://localhost:11434/v1`) — no other code changes.
