# SI-12.3 — Prep orchestrator, cached prepared docs + load seam + CLI

| Field | Value |
|---|---|
| Issue type | Story |
| Parent epic | SI-12 — Deterministic Web-to-Doc Prospect Prep (Plane A, NO LLM) |
| Status | Done |
| Priority | High |
| Story points | 8 |
| Component | Intelligence |
| Labels | backend, data, ai, retrieval |

## User story
As a sales rep, I want a prospect prepared once into small, clean, credible cached docs that the brief and Scout read from, and a CLI to pre-seed them, so that a demo runs instantly with zero LLM calls in the prep stage.

## Description
This story adds the orchestrator that ties the prep plane together, the load seam that feeds it into the rest of the app, and a CLI to pre-seed the cache.

`backend/app/services/prep.py` exposes `prepare_company(company, slug, force)`. It gathers pages via `retrieval` **plus the existing SI-11 feeds** as extra evidence, keeps only research-guide-matched passages (plus the descriptive lead of an authoritative source) tagged by category, scores credibility per source, and writes one clean `.md` per source plus a `manifest.json` to the git-ignored `backend/.cache/prepared/<slug>/`. The cache has a TTL (`PREP_TTL_HOURS`) and is idempotent — a fresh manifest short-circuits the run unless `force` is set.

The **integration seam** lives in `sources.py`. `load_prepared_docs()` maps the manifest to `SourceDoc[]` tagged `["web", "prospect", "prepared"]`. `load_company_intel()` now **prefers** prepared docs, then falls back to live SI-11 feeds, then to local `docs/<slug>/`; `docs/zoho/` is still always appended as shared knowledge.

`backend/app/tools/prepare.py` is the CLI: `python -m app.tools.prepare "<company>"` prepares one company, and `--all` prepares the five research-guide companies. It pre-seeds and caches so the demo is instant and makes zero LLM calls. New config keys `PREP_ENABLED`, `PREP_MAX_RESULTS`, and `PREP_TTL_HOURS` govern the stage. The whole plane is guaranteed LLM-free by construction.

## Acceptance criteria
```gherkin
Scenario: A company is prepared into cached docs
  Given a company name and slug
  When prepare_company runs
  Then guide-matched passages tagged by category are written as one .md per source
  And a manifest.json is written to backend/.cache/prepared/<slug>/
  And no LLM call is made
```

```gherkin
Scenario: The cache is idempotent within its TTL
  Given a fresh manifest exists for a slug
  When prepare_company runs again without force
  Then the run short-circuits and no new fetch is made
```

```gherkin
Scenario: The load seam prefers prepared docs
  Given a slug with prepared docs, live feeds, and a local docs folder
  When load_company_intel runs
  Then prepared docs are returned as SourceDoc tagged web/prospect/prepared first
  And live feeds and local docs are only fallbacks
  And docs/zoho/ is always appended
```

```gherkin
Scenario: The CLI pre-seeds the demo companies
  Given the prepare CLI is run with --all
  When it completes
  Then the five research-guide companies are prepared and cached
  And no LLM call is made
```

## Technical notes (reference)
- Key files: `backend/app/services/prep.py`, `backend/app/services/sources.py` (`load_prepared_docs`, `load_company_intel`), `backend/app/tools/prepare.py`.
- `prepare_company(company, slug, force)`: retrieval + SI-11 feeds as evidence → keep guide-matched passages (plus authoritative source's descriptive lead) tagged by category → credibility per source → write `.md` per source + `manifest.json` to git-ignored `backend/.cache/prepared/<slug>/`.
- TTL via `PREP_TTL_HOURS`; idempotent — a fresh manifest short-circuits.
- `load_prepared_docs()` maps manifest → `SourceDoc[]` tagged `["web","prospect","prepared"]`.
- `load_company_intel()` prefers prepared docs, then SI-11 feeds, then local `docs/<slug>/`; `docs/zoho/` always appended.
- CLI: `python -m app.tools.prepare "<company>"` and `--all` (5 research-guide companies).
- Config: `PREP_ENABLED`, `PREP_MAX_RESULTS`, `PREP_TTL_HOURS`.
- Live: `prepare "Freshworks"` produced 11 real docs (official/Wikipedia/SEC/press) tagged financial/leadership/pain.

## Definition of Done
- [x] `prepare_company` gathers retrieval + SI-11 pages, keeps guide-matched passages tagged by category, scores credibility, writes `.md` + `manifest.json` per source.
- [x] Cache is git-ignored, TTL'd, and idempotent (fresh manifest short-circuits; `force` overrides).
- [x] `load_prepared_docs()` maps the manifest to `SourceDoc` tagged web/prospect/prepared.
- [x] `load_company_intel()` prefers prepared → SI-11 feeds → local docs; `docs/zoho/` always appended.
- [x] CLI `python -m app.tools.prepare` supports a single company and `--all`.
- [x] Config keys `PREP_ENABLED`, `PREP_MAX_RESULTS`, `PREP_TTL_HOURS` added.
- [x] Prep plane makes zero LLM calls; all 6 target companies prepared.
