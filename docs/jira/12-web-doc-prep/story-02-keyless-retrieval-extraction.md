# SI-12.2 — Keyless retrieval + trafilatura main-content extraction

| Field | Value |
|---|---|
| Issue type | Story |
| Parent epic | SI-12 — Deterministic Web-to-Doc Prospect Prep (Plane A, NO LLM) |
| Status | Done |
| Priority | High |
| Story points | 5 |
| Component | Intelligence |
| Labels | backend, data, retrieval |

## User story
As a sales rep, I want the app to actually read full web pages about a prospect — not just headlines — so that my prospect docs contain real page content, cleaned of navigation and ads, without anyone configuring API keys.

## Description
This story introduces `backend/app/services/retrieval.py`, a keyless layer that finds and reads full web pages. `search()` returns results from the **DuckDuckGo HTML endpoint** plus the company's **Wikipedia** page, using queries built by `research_keywords.search_queries` — so retrieval looks for exactly the categories the guide cares about, with no API key required.

Extraction is handled by `extract_page(html, url)`, a **pure, network-free** wrapper over `trafilatura` that pulls a page's main text and renders it to Markdown, stripping navigation, ads, and boilerplate. Because it takes HTML in and returns Markdown out, it is fully unit-testable offline with no network. `fetch_and_extract(url)` is the thin network wrapper that fetches a URL and then calls `extract_page`.

The whole layer is **fail-soft**: any single fetch or extraction can error without breaking the run, and `settings.mock_web` disables all network so tests and E2E runs are hermetic and quota-free. `trafilatura==2.1.0` is added as a new dependency to power the extraction.

## Acceptance criteria
```gherkin
Scenario: Keyless search returns DuckDuckGo and Wikipedia results
  Given a company name and guide-built queries
  When search runs
  Then it returns DuckDuckGo HTML endpoint results plus the company's Wikipedia page
  And no API key is required
```

```gherkin
Scenario: Main content is extracted to clean Markdown
  Given raw page HTML with navigation, ads, and boilerplate
  When extract_page runs
  Then it returns the page's main text as Markdown
  And navigation, ads, and boilerplate are stripped
```

```gherkin
Scenario: Extraction is pure and network-free
  Given HTML passed directly to extract_page
  When it runs
  Then it produces Markdown without making any network call
```

```gherkin
Scenario: Mock mode disables the network
  Given settings.mock_web is enabled
  When search or fetch_and_extract runs
  Then no network request is made
```

## Technical notes (reference)
- Key file: `backend/app/services/retrieval.py`.
- `search()` = DuckDuckGo HTML endpoint results + the Wikipedia page; queries from `research_keywords.search_queries`.
- `extract_page(html, url)` = pure/network-free `trafilatura` main-text extraction to Markdown (strips nav/ads/boilerplate) — unit-testable offline.
- `fetch_and_extract(url)` = network wrapper around fetch + `extract_page`.
- Fail-soft throughout; `settings.mock_web` disables network for hermetic tests/E2E.
- New dependency: `trafilatura==2.1.0`.

## Definition of Done
- [x] `retrieval.search()` returns DuckDuckGo HTML + Wikipedia results from guide-built queries, keyless.
- [x] `extract_page(html, url)` extracts main text to Markdown, network-free, stripping nav/ads/boilerplate.
- [x] `fetch_and_extract(url)` wraps fetch + extraction.
- [x] Layer is fail-soft; `settings.mock_web` disables network.
- [x] `trafilatura==2.1.0` added as a dependency.
- [x] No LLM client imported.
