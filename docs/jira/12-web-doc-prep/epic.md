# EPIC SI-12 — Deterministic Web-to-Doc Prospect Prep (Plane A, NO LLM)

| Field | Value |
|---|---|
| Issue type | Epic |
| Suggested key | SI-12 |
| Status | Done |
| Priority | High |
| Component | Intelligence |
| Labels | backend, ai, data, retrieval |
| Story points (rollup) | 21 |

## Summary
Phase 1 of a web-to-pitch analysis engine re-architecture: read full web pages for a prospect, turn them into clean, keyword-filtered, credibility-scored CACHED docs — with NO LLM. Goes beyond SI-11 (which only keyword-sorted RSS/JSON feed snippets) by actually extracting page main-text, tagging passages by research-guide category, scoring each source's credibility, and writing small grounded `.md` docs the later LLM stages read. Keeps everything inside the Gemini free tier.

## Description
SI-11 proved that a brief could be grounded in live web signal instead of a hand-curated `docs/<slug>/` folder, but it stopped at feed snippets: Google News RSS, SEC EDGAR, and Reddit headlines, keyword-sorted and capped. That is thin evidence — a headline is not a page. This epic introduces **Plane A**, a deterministic preparation stage that fetches full web pages, extracts their main content, filters that content down to sales-relevant passages, scores the source's credibility, and persists the result as clean cached Markdown docs. The LLM never runs in this plane. It only runs in later stages, reading these small grounded docs — which is exactly what keeps the whole pipeline inside the Gemini free tier.

Every decision in this epic is **rule-based and reproducible**. The taxonomy of "what to look for on a page" comes straight from `docs/shared/SalesIntel_Research_Guide.doc.pdf` **Section 3**, encoded as keyword categories (financial_intel, product_strategy, leadership_changes, pain_points, social_signals, job_intent). Those categories drive two things at once: they expand the keyless search queries, and they filter extracted passages so only guide-matched material is kept. Credibility scoring is a pure lookup over the URL and company — regulatory/SEC and encyclopedia sources rank highest, official company domains next, tier-1 press below that, and social/forum chatter lowest — with an official-domain check strict enough that an unrelated look-alike domain is never mistaken for the company's own.

The orchestrator, `prep.py`, ties it together: it gathers pages via a keyless retrieval layer (DuckDuckGo HTML + Wikipedia) plus the existing SI-11 feeds as extra evidence, keeps only guide-matched passages tagged by category, scores credibility per source, and writes one clean `.md` per source plus a `manifest.json` to a git-ignored, TTL'd cache under `backend/.cache/prepared/<slug>/`. A CLI (`app/tools/prepare.py`) pre-seeds and caches for an instant, zero-call demo. The load seam in `sources.py` prefers prepared docs, then live SI-11 feeds, then local `docs/<slug>/`, with `docs/zoho/` always appended. The prep modules are guaranteed LLM-free by construction, asserted in tests.

## Stories in this epic
| Key | Story | Points | Priority |
|---|---|---|---|
| SI-12.1 | Research-guide keyword taxonomy + rule-based credibility scoring | 5 | High |
| SI-12.2 | Keyless retrieval + trafilatura main-content extraction | 5 | High |
| SI-12.3 | Prep orchestrator, cached prepared docs + load seam + CLI | 8 | High |
| SI-12.4 | Correctness hardening: official-domain precision, word-bounded acronyms, cache test isolation | 3 | Medium |

## Epic acceptance criteria
```gherkin
Scenario: A prospect is prepared into clean cached docs with no LLM call
  Given a company name and slug
  When prepare_company runs
  Then full web pages are fetched, extracted to Markdown, and filtered to guide-matched passages
  And each source is credibility-scored and written as one .md plus a manifest.json to backend/.cache/prepared/<slug>/
  And no LLM client is imported or called anywhere in the prep plane
```

```gherkin
Scenario: Passages are kept only when they hit a research-guide category
  Given extracted page text for a company and its competitors
  When the prep stage filters passages
  Then only passages matching a Section 3 category are kept, tagged by category
  And the descriptive lead of an authoritative source is retained as context
```

```gherkin
Scenario: Prepared docs are preferred by the load seam
  Given a slug with a fresh prepared manifest
  When company intel is loaded
  Then prepared docs are returned as SourceDoc tagged web/prospect/prepared
  And live SI-11 feeds and local docs/<slug>/ are used only as fallbacks
  And docs/zoho/ is always appended as shared knowledge
```

```gherkin
Scenario: The cache is idempotent within its TTL
  Given a company was prepared within PREP_TTL_HOURS
  When prepare_company runs again without force
  Then a fresh manifest short-circuits the run
  And no new network fetch is made
```

## Out of scope
- Any LLM call in the preparation plane (synthesis, ranking, or summarizing) — that lives in later stages.
- Keyed / paid data sources or scrapers that need credentials or an API token.
- A vector DB or RAG retrieval layer (prepared docs are still stuffed into one downstream call).
- UI changes — prep is a backend/CLI stage and adds no frontend surface.

## Dependencies
- SI-11 — Web-First Prospect Intel; its keyless feeds are reused as extra evidence and as a fallback.
- Research guide `docs/shared/SalesIntel_Research_Guide.doc.pdf` **Section 3** (keyword categories).
- New dependency `trafilatura==2.1.0` for network-free main-content extraction.
- Config keys `PREP_ENABLED`, `PREP_MAX_RESULTS`, `PREP_TTL_HOURS`; existing `settings.mock_web`.

## Verification
- **pytest all green** including new `tests/test_prep.py` (offline, no network, no LLM, ~10 tests); **npm build** clean; **Playwright 6/6** (unchanged — prep adds no UI).
- Live confirmed: `prepare "Freshworks"` produced 11 real docs (official / Wikipedia / SEC / press) correctly tagged financial / leadership / pain.
- All 6 target companies prepared: Freshworks, Braze, Sprout Social, Amplitude, Zuora, The Sleep Company.
