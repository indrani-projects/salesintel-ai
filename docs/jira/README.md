# SalesIntel AI — MVP 1 Jira Backlog (demo pack)

This folder is a **paste-ready Jira backlog** for the SalesIntel AI POC. It re-frames
everything that was actually built into **17 product epics and 75 stories**, so a PM can
copy each file straight into Jira (Epic → Stories) with no translation.

> **What this is:** a back-fill of already-delivered work into a clean, capability-shaped
> board for the demo. Every item is **Status = Done**. The original build was organized by
> which agent owned which files; this backlog re-groups it by *product capability* instead.

## How to use

- Each **epic** lives in its own folder: `NN-<slug>/epic.md` plus one `story-NN-*.md` per story.
- Every file is self-contained Markdown with a metadata table (issue type, key, status,
  priority, story points, component, labels), a description, **Gherkin acceptance criteria**
  (`Given / When / Then`), technical notes, and a Definition of Done.
- In Jira: create the Epic from `epic.md`, then create each Story from its file and link it
  to the epic via the **Suggested key** (e.g. `SI-3.4` → epic `SI-3`).
- Story points use Fibonacci; priorities are Highest/High/Medium/Low.

## Epic index

| Key | Epic | Folder | Stories | Priority |
|---|---|---|---|---|
| **SI-1** | Platform Foundation & Data Contract | `01-platform-foundation/` | 5 | Highest |
| **SI-2** | Calendar & Meeting Management | `02-calendar-meetings/` | 5 | High |
| **SI-3** | AI Brief Generation Engine | `03-brief-engine/` | 6 | Highest |
| **SI-4** | Multi-Persona Briefs (AE / SDR / SE) — *superseded by SI-14* | `04-multi-persona-briefs/` | 4 | High |
| **SI-5** | Scout Chatbot (Grounded Q&A) | `05-scout-chatbot/` | 3 | Medium |
| **SI-6** | Brief Delivery: Web View & Email (PDF attachment) | `06-brief-delivery-email/` | 5 | High |
| **SI-7** | Application Experience & Visual Design | `07-app-experience-design/` | 5 | Medium |
| **SI-8** | Quality, Testing & Demo Readiness | `08-quality-testing-demo/` | 5 | High |
| **SI-9** | Engineering Workflow & Tooling | `09-engineering-workflow-tooling/` | 5 | High |
| **SI-10** | Google Workspace Integration (Gmail + Calendar) | `10-google-integration/` | 4 | High |
| **SI-11** | Web-First Prospect Intel (generic, on-demand) | `11-web-prospect-intel/` | 4 | High |
| **SI-12** | Web-to-Doc Prospect Prep (Plane A · no LLM) | `12-web-doc-prep/` | 4 | High |
| **SI-13** | Zoho Product Catalog (Plane B · no LLM) | `13-zoho-catalog/` | 3 | High |
| **SI-14** | Persona Refresh — 6 personas from the persona doc (supersedes SI-4) | `14-persona-refresh/` | 4 | High |
| **SI-15** | Recurring Google Calendar Auto-Sync (+ token expiry, deletion, live UI) | `15-calendar-autosync/` | 4 | High |
| **SI-16** | Scheduled 1-Hour-Before Persona Email (+ per-persona routing) | `16-hour-before-email/` | 3 | High |
| **SI-17** | Demo Login & Persona Selection (single active persona) | `17-demo-login/` | 6 | Medium |

## The product in one paragraph

SalesIntel AI auto-generates a grounded, cited **pre-sales brief** about a prospect for a
sales rep, driven by a **Calendar → Dashboard → Brief → Scout chatbot** flow. The demo
scenario is **Zoho selling to The Sleep Company**. The value is the *synthesis layer*: external
prospect signal × internal Zoho product knowledge → an actual pre-sales angle, now reframed
for **six personas** (Sales Representative, Sales Manager, Sales Enablement, Revenue Operations
Manager, VP of Sales, SalesIntel AI Admin — SI-14), delivered on screen and by email. Under it,
a **two-plane, no-LLM data foundation** reads the open web about a prospect into
keyword-filtered, credibility-scored cached docs (**Plane A**, SI-12) and joins it against a
deterministic **Zoho product catalog** (**Plane B**, SI-13).

## Deliberate POC shortcuts (intentional — noted in the relevant stories)

These are documented design choices for a fast, cheap hypothesis test, each with a named scale path:

- **No vector DB** — all source text is stuffed into one LLM call (RAG is the scale path).
- **Web-first prospect intel** (Google News RSS / SEC EDGAR / Reddit — keyword-filtered + cached, **no extra LLM call**) with a **local `docs/` fallback**. SI-11 reversed the original "local docs only" shortcut; live LinkedIn/Crunchbase scraping stays out of scope.
- **No-LLM data foundation** (SI-12/SI-13): the deterministic web-to-doc prep (`trafilatura` extraction + research-guide keyword filtering + rule-based credibility, cached under `backend/.cache/prepared/`) and the Zoho product catalog (`docs/zoho/products/` + a compact `zoho_products_summary.md`) both run with **zero LLM calls** — retrieval/filtering only. Keyed / paid search APIs, JS-rendered KB portals, and RAG/vector retrieval stay out of scope; the free-tier Gemini call runs only in synthesis.
- **SQLite** (SQLModel) instead of Postgres.
- **FastAPI BackgroundTasks** instead of a job queue.
- **MOCK_LLM / MOCK_EMAIL / MOCK_GOOGLE / MOCK_WEB** modes for repeatable, quota-free, network-free demos and hermetic CI.
- **Demo-send email** by default (real send is opt-in — SMTP `.env`, or the rep's Gmail via Google OAuth in SI-10).
