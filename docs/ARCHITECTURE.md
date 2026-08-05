# SalesIntel AI — Architecture

A single source of truth for how the system is put together. For the product framing
and roadmap see `BUILD_PLAN.md`; for a plain-English tour see `HOW_IT_WORKS.html`; for
running/deploying see `RUNBOOK.md` and `deploy/`.

## 1. What it is

SalesIntel AI auto-generates a grounded, **cited 9-section pre-sales briefing** about a
prospect for a sales rep, on a **calendar → dashboard → brief → chatbot** flow. The
demo scenario is **Zoho selling to The Sleep Company**. The thing being proven is the
*synthesis layer* — external prospect signal × internal Zoho product knowledge → an
actual pre-sales angle, not a summary.

Crucially, **the data feeding the synthesis is real**: a deterministic, keyless
web pipeline gathers live public signal about the prospect (see §4). The only LLM step
is the final synthesis.

## 2. System topology (as deployed)

Live, free, on a GCP Always-Free `e2-micro` VM behind Caddy (auto-HTTPS). One origin,
same-origin API, backend never exposed directly.

```
                       Internet
                          │  HTTPS (Let's Encrypt)
                ┌─────────▼──────────┐
                │  Caddy  :443        │  shared-password gate (basic-auth)
                │                     │  security headers (HSTS/CSP/XFO/…)
                │  ┌───────────────┐  │
   static SPA ◄─┤  │ file_server   │  │  /var/www/salesintel (built React app)
                │  └───────────────┘  │
                │  ┌───────────────┐  │
   /api/*  ────►│  │ reverse_proxy │──┼──► uvicorn 127.0.0.1:8000 (systemd: salesintel)
                │  └───────────────┘  │        │
                └─────────────────────┘        ├─ FastAPI (routers → services)
                                               ├─ SQLite (WAL) @ /var/lib/salesintel
                                               ├─ calendar-sync daemon (30s)
                                               └─ reminder-email daemon (~1h before)
```

CI/CD: every merge to `main` triggers a GitHub Actions deploy over an **IAP tunnel**
(SSH closed to the internet), authenticated **keyless** via Workload Identity
Federation. `deploy/deploy.sh` builds nothing on the box — the frontend is built on the
runner and rsynced. See `deploy/GITHUB_ACTIONS.md`.

## 3. Request → brief lifecycle (async state machine)

`POST /meetings` creates a Meeting + a `pending` Brief row, then schedules
`generate_brief_task` via FastAPI `BackgroundTasks`. Status flows are mirrored on
**both** `Meeting.brief_status` and `Brief.status`; the frontend polls the brief
endpoint (TanStack Query) to watch it flip.

```
POST /meetings ─► Meeting + Brief(pending) ─► BackgroundTask
                                                   │
   pending ─────────► generating ─────────► ready ─┴─► (auto-email if enabled)
      ▲                   │                   error
      └── regenerate ─────┘  (any failure is caught → status=error; never crashes)
```

The background task opens its **own** DB session and is exception-safe — a failure is
written as `status=error`, never raised. On startup, briefs left `generating` by a
killed process are requeued. A lock + rerun-flag serialize overlapping triggers.

A meeting's free-text `prospect_company` is mapped to a `docs/<slug>/` folder by
`sources.resolve_company_slug` (normalizes "The Sleep Company" → `sleep_company`). The
`zoho/` folder is never a prospect — it's always appended as shared product knowledge.

## 4. Data processing — the web-to-pitch pipeline

This is the heart of the system. From a company **name**, the pipeline produces a set
of citable `SourceDoc`s (`S1, S2, …`) that are fed to the LLM. **Every stage except the
final synthesis is deterministic — no LLM, no vector DB.**

```
 company name
     │
     ▼
 load_company_intel(name, slug)         ← the single entry point (services/sources.py)
     │   prefers the first non-empty of three tiers:
     │
     ├─(1) PREPARED web cache            backend/.cache/prepared/<slug>/  (built offline)
     │        clean Markdown + manifest.json, TTL 1 week
     │
     ├─(2) LIVE keyless feeds            services/web_sources.py  (if web_intel_enabled)
     │        • Google News RSS   news.google.com/rss/search?q="<company>"
     │        • SEC EDGAR         efts.sec.gov  (8-K / 10-Q / 10-K)
     │        • Reddit            reddit.com/search.json?q="<company>"
     │        • Zoho Angle        synthesized locally from company_hints (no network)
     │        keyword-prioritized, capped, cached 24h under .cache/webintel/
     │
     └─(3) LOCAL docs/<slug>/            services/ingestion.py   (FALLBACK only)
              PDFs → PyMuPDF text; .md/.txt/.html supported
     │
     └─ ALWAYS append docs/zoho/         shared Zoho product knowledge  (tag: zoho)
     │
     ▼
 SourceDoc[]  (each: marker S#, title, text, tags, credibility)
     │
     ▼
 generate_brief()  ─►  ONE LLM call (strict JSON, reasoning_effort=low)
     services/brief_engine.py            ← the ONLY LLM step for a brief
```

### The deterministic prep stage (offline, `services/prep.py`)

The richest tier is built ahead of time by a CLI (`python -m app.tools.prepare
"<company>"`), so briefs at request time serve instantly and quota-free. It is a pure,
**no-LLM** pipeline:

1. **Retrieve** candidate pages (`services/retrieval.py`) — a **keyless DuckDuckGo HTML
   search** driven by research-guide queries, **plus the company's Wikipedia article**
   (keyless REST API). Junk hosts (social/video/search engines) are skipped.
2. **Extract** each page's clean main text with **`trafilatura`** (Markdown output).
3. **Filter** to only the passages that match a research-guide **keyword taxonomy**
   (`services/research_keywords.py`): financial intel, product/strategy, leadership
   changes, pain points, social signals, and competitor-tool "job intent" — a
   deterministic case-insensitive match, no model.
4. **Score credibility** by domain rules (`services/credibility.py`): `.gov`/SEC → 95
   (regulatory), Wikipedia → 85, official company domain → 90, tier-1 press → 80,
   social/forum/blog → 35, else 55. Authoritative sources keep their descriptive lead
   even without a keyword hit.
5. **Cache**: one clean Markdown doc per source + a `manifest.json` under
   `backend/.cache/prepared/<slug>/`, TTL 1 week, built in memory first so a failed
   fetch never corrupts a good cache.

Every fetch layer is **fail-soft**: a dead search, a 404, or an empty feed yields
nothing and the pipeline degrades to the next tier.

### Synthesis + grounded Q&A (the LLM stages)

`brief_engine.generate_brief` concatenates **all** the loaded source text into a single
prompt (`===== SOURCE S# | tag=… =====` blocks) — **no RAG / no vector retrieval** — and
makes **one** OpenAI-compatible call requesting strict JSON, with a param-stripping
fallback if the endpoint rejects `response_format`/`reasoning_effort`. Output is parsed
defensively: fences stripped, confidence/flags coerced, and **all nine sections
guaranteed** (missing ones become low-confidence placeholders). Every factual claim must
carry an inline `[S#]` marker, mapped back to the source inventory. The rep's
`why`/`agenda` are injected so emphasis shifts (agenda = "scaling support" → Zoho Desk
gets weight) — the demo's proof that synthesis is real.

`chat_service.answer_question` (Scout) **reuses the same intel set** the brief used and
answers strictly from it, citing the same `[S#]` markers, declining when unsupported.

### Caching summary (all git-ignored, all regenerable)

| Cache | Location | TTL | Built by |
|---|---|---|---|
| Prepared web docs | `backend/.cache/prepared/<slug>/` | 1 week | CLI `app.tools.prepare` |
| Live feed intel | `backend/.cache/webintel/…json` | 24h | auto, on request |
| Extracted local-doc text | `backend/.cache/…txt` | by file signature | auto, on request |

## 5. Backend layering (`backend/app/`)

- **`api/{meetings,briefs,chat,google}.py`** — thin routers. `meetings.py` also holds
  the `generate_brief_task` background job; `google.py` holds calendar sync + OAuth.
- **`services/`** — the intelligence: `sources` (discovery/loading) → `retrieval` /
  `web_sources` / `prep` / `research_keywords` / `credibility` (the web pipeline) →
  `ingestion` (local PDF text) → `brief_engine` (LLM synthesis) → `brief_render`
  (JSON→HTML). `chat_service` handles grounded Q&A. `llm_client` is the single
  OpenAI-compatible client (swappable via `.env`; default Gemini free tier).
- **Two shared contract files** are the backbone and are treated as append-only:
  `schemas.py` (all API DTOs + the 9-section order) and `contracts.py` (service
  signatures + the internal `SourceDoc`). `schemas.py` is hand-mirrored to
  `frontend/src/api/types.ts`.
- **`models.py` (SQLModel tables) vs `schemas.py` (API DTOs)** are deliberately separate.
  Brief content is stored as a JSON string in `Brief.content_json`, re-validated on read.
- **`db.py`** — SQLite in **WAL mode** (concurrent daemon writes) + idempotent additive
  migrations. DB lives at `/var/lib/salesintel/salesintel.db`, outside the deploy dir.

## 6. Frontend (`frontend/src/`)

React 19 + Vite + TS + Tailwind, React Router, TanStack Query, FullCalendar. `api/client.ts`
is the axios client (base URL from `VITE_API_URL`; production = `/api`, same-origin behind
Caddy). Pages: **Calendar** (add meetings), **Dashboard** (brief status + polling),
**BriefView** (9-section render + `ChatPanel`/Scout), **Settings** (Google connect,
automation, Developer Library). PDF export is client-side (`lib/pdf.ts`, html2pdf) over the
brief HTML; the "Send as email" attachment is a server-side PDF (xhtml2pdf).

Six **personas** (`Persona` in `schemas.py`) each reframe the brief; the signed-in user
sees only their own persona's tab.

## 7. Security & access

- **Access gate:** Caddy shared-password (basic-auth) over the whole origin;
  `/api/health` and `/api/auth/google/*` exempt. Backend binds `127.0.0.1` only.
- **Headers:** HSTS, CSP, X-Frame-Options, X-Content-Type-Options, Referrer-Policy.
- **API errors** are generic to clients (full detail in server logs); Swagger is off in
  production; the OAuth connect flow uses a signed, time-bounded `state` nonce (CSRF).
- **Secrets** live in `/etc/salesintel/env` (chmod 600), never committed. SSH is
  IAP-only; CI auth is keyless (WIF). See `docs/SECURITY_AND_QUALITY_PLAN.md`.

## 8. Deliberate POC shortcuts (still true — don't "fix" without reason)

- **No vector DB / no RAG** — the entire filtered source set is stuffed into one LLM call
  (per-source capped at 8000 chars). RAG is the scale path.
- **Local `docs/` folder as a fallback** to the live web pipeline; the heavy prep runs
  **offline via a CLI**, then briefs serve from that cache (instant + quota-free).
- **SQLite** (WAL) instead of Postgres; **FastAPI `BackgroundTasks`** instead of a job
  queue; substring keyword matching instead of semantic filtering.
