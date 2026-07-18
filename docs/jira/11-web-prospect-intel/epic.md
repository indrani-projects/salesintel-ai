# EPIC SI-11 — Web-First Prospect Intel (generic, on-demand) + filtered cache

| Field | Value |
|---|---|
| Issue type | Epic |
| Suggested key | SI-11 |
| Status | Done |
| Priority | High |
| Component | Intelligence |
| Labels | backend, frontend, ai, api, data |
| Story points (rollup) | 18 |

## Summary
Reverse the "local docs only" POC shortcut: when a meeting is created, pull LIVE web intel for the prospect by name (any company, known or unknown), keyword-filter it, cache the filtered text, and feed it to both the brief engine and Scout — with the local `docs/<company>/` folder as the fallback. Zero extra LLM calls.

## Description
The original SalesIntel AI POC took a deliberate shortcut: prospect signal came only from a hand-curated `docs/<slug>/` folder of PDFs. That works for the scripted demo (Zoho → The Sleep Company) but breaks the moment a rep types a company the app has never heard of. This epic removes that ceiling. A meeting's free-text company name now drives an **on-demand web fetch** so a grounded, cited brief can be produced for *any* company, with no folder to prepare in advance.

The design constraint that shapes every story is **zero extra LLM calls**. The web text is treated exactly like the local PDF text already was: it is collected, filtered, concatenated with shared `S#` source markers, and handed to the *existing* brief-synthesis and Scout-Q&A calls. No new model round-trips are introduced, so the whole feature stays inside the Gemini free tier. The intelligence in this epic is entirely in the *retrieval and filtering* — a keyless fetcher (SI-11.1), a temporary filtered cache (SI-11.2), a web-first source seam (SI-11.3), and a generic any-company pipeline with a free-text UI (SI-11.4).

Retrieval uses only **keyless public sources** — Google News RSS, SEC EDGAR full-text search, and Reddit — queried by company name over the `httpx` client already in the codebase. Every source is fail-soft: any one can time out or error and the rest still return. A keyword-priority filter floats sales-relevant snippets (earnings, layoffs, CFO/CTO moves, pricing complaints, competitor tools like Salesforce / HubSpot / QuickBooks) to the top before the text is capped, so the most useful signal survives the character budget. The filtered result is written to a 24h on-disk cache keyed by the company name, so repeated briefs, Scout turns, and persona toggles for the same prospect reuse it with no re-fetch and no extra API calls — the "temporary memory" the chatbot reads from.

The work is derived from the user's research guide (`docs/shared/SalesIntel_Research_Guide.doc.pdf`): 5 target companies, 10 shared keyless data-source APIs, and category keyword templates. An optional company-hints table enriches those 5 targets (Freshworks, Braze, Sprout Social, Amplitude, Zuora) with ticker + Zoho pitch angle, but the generic path works without any hint. Local `docs/<slug>/` remains the fallback whenever the web returns nothing.

## Stories in this epic
| Key | Story | Points | Priority |
|---|---|---|---|
| SI-11.1 | Keyless web sources fetcher | 5 | High |
| SI-11.2 | Filtered-intel cache (temporary, no LLM) | 3 | Medium |
| SI-11.3 | Web-first source seam | 5 | High |
| SI-11.4 | Generic any-company pipeline + free-text UI + hints | 5 | High |

## Epic acceptance criteria
```gherkin
Scenario: Brief is generated for a company with no docs folder
  Given a meeting is created for a prospect with no docs/<slug>/ folder
  When the brief is generated
  Then live web intel for that company name is fetched, filtered, and cached
  And the brief renders with citations traced to the web sources
  And no additional LLM call is made beyond the existing synthesis call
```

```gherkin
Scenario: Repeated work reuses the cache
  Given a company's web intel was fetched within the TTL window
  When another brief, Scout turn, or persona toggle runs for the same company
  Then the filtered text is served from the on-disk cache
  And no new web request or API call is made
```

```gherkin
Scenario: Web-first with local fallback
  Given a company that returns no usable web intel
  When the brief is generated
  Then the pipeline falls back to the local docs/<slug>/ folder
  And docs/zoho/ is always appended as shared knowledge
```

## Out of scope
- Any keyed / paid data source or scraper that needs credentials or an API token.
- A vector DB or RAG retrieval layer (the text is still stuffed into one call).
- Additional LLM calls for summarizing or ranking web results (filtering is keyword-based).
- Persisting web intel beyond the temporary TTL cache.

## Dependencies
- Brief generation epic (SI-3) — the existing synthesis call this epic feeds unchanged.
- Scout Chatbot epic (SI-5) — consumes the same source seam for grounded Q&A.
- Shared contract files `schemas.py` / `contracts.py` / `frontend/src/api/types.ts`.
- Research guide `docs/shared/SalesIntel_Research_Guide.doc.pdf` (targets, sources, keyword templates).

## Verification
- **pytest 40/40**, **npm build** clean, **Playwright 5/5** — all under `MOCK_WEB` (the dialog E2E now creates a "Freshworks" web-only meeting).
- Live fetch confirmed: real Google News headlines and real SEC filings returned for "Freshworks".
