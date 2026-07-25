# SI-11.1 — Keyless web sources fetcher

| Field | Value |
|---|---|
| Issue type | Story |
| Parent epic | SI-11 — Web-First Prospect Intel (generic, on-demand) + filtered cache |
| Status | Done |
| Priority | High |
| Story points | 5 |
| Component | Intelligence |
| Labels | backend, data, ai |

## User story
As a sales rep, I want the app to pull live public intel about a prospect by name whenever I add a meeting, so that I get a grounded brief even for a company the app has never been told about — without anyone configuring API keys.

## Description
This story introduces `backend/app/services/web_sources.py`, a keyless fetcher that queries public sources by company name using the `httpx` client already present in the codebase. Three sources are wired in:

- **Google News RSS** — `news.google.com/rss/search?q=<company>` for recent headlines and article snippets.
- **SEC EDGAR full-text search** — `efts.sec.gov/LATEST/search-index?q=<company>` for filings that name the company (10-K/10-Q/8-K signal).
- **Reddit** — `reddit.com/search.json?q=<company>` for practitioner chatter. Reddit currently blocks unauthenticated `.json` access, so this source is skipped gracefully rather than failing the fetch.

Every source is **fail-soft**: each is wrapped so any one can error or time out and the remaining sources still return their results. A source that returns nothing simply contributes nothing.

The collected snippets pass through a keyword-priority filter, `_prioritize`, which floats the most sales-relevant material to the top *before* the combined text is capped to the character budget. Priority keywords cover buying signals and pain — earnings, layoffs, CFO/CTO moves, pricing complaints — and competitor tooling such as Salesforce, HubSpot, and QuickBooks. This ensures the highest-value signal survives the cap instead of being truncated away.

A `mock_web` path returns deterministic canned documents so tests and E2E runs are hermetic and quota-free. The live path was verified against real endpoints: real Google News headlines and real SEC filings were returned for the query "Freshworks".

## Acceptance criteria
```gherkin
Scenario: Live intel is fetched by company name
  Given web intel is enabled and a company name "Freshworks"
  When the fetcher runs
  Then Google News RSS and SEC EDGAR return snippets tagged to their source
  And the results are combined into web intel documents
```

```gherkin
Scenario: A failing source does not break the fetch
  Given one source times out or returns an error
  When the fetcher runs
  Then that source contributes nothing
  And the remaining sources still return their results
```

```gherkin
Scenario: Sales-relevant signal is prioritized before capping
  Given more snippets than fit in the character budget
  When the fetcher prioritizes results
  Then snippets mentioning earnings, layoffs, CFO/CTO, pricing, or competitor tools float to the top
  And the combined text is capped after prioritization
```

```gherkin
Scenario: Deterministic mock mode
  Given MOCK_WEB is enabled
  When the fetcher runs
  Then it returns fixed canned documents with no network calls
```

## Technical notes (reference)
- Key file: `backend/app/services/web_sources.py`.
- Sources: Google News RSS (`news.google.com/rss/search`), SEC EDGAR full-text (`efts.sec.gov/LATEST/search-index`), Reddit (`reddit.com/search.json`, skipped when unauthenticated access is blocked).
- Transport: reuses the existing `httpx` dependency; per-source try/except makes each source fail-soft.
- `_prioritize` reorders snippets by a keyword weight (earnings / layoffs / CFO / CTO / pricing / Salesforce / HubSpot / QuickBooks …) before applying the char cap.
- `mock_web` returns canned docs for hermetic tests/E2E; live path confirmed with real news + SEC results for "Freshworks".

## Definition of Done
- [x] `web_sources.py` fetches by company name from Google News RSS + SEC EDGAR (+ Reddit, gracefully skipped).
- [x] All sources are fail-soft — any can error/timeout without breaking the fetch.
- [x] `_prioritize` floats sales-relevant snippets to the top before the character cap.
- [x] `mock_web` returns deterministic canned documents for tests.
- [x] Live fetch verified: real Google News headlines and real SEC filings returned for "Freshworks".
