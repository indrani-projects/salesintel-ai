# SI-3.1 — Source discovery (LocalFolderProvider + Zoho shared knowledge)

| Field | Value |
|---|---|
| Issue type | Story |
| Parent epic | SI-3 — AI Brief Generation Engine |
| Status | Done |
| Priority | High |
| Story points | 3 |
| Component | Brief Engine |
| Labels | backend, ai, data |

## User story
As a sales rep, I want the system to find the right prospect's documents from a free-text company name and always pair them with Zoho's own product knowledge, so that every brief is grounded in both sides of the deal without me pointing at any files.

## Description
Before the engine can synthesize anything, it has to answer one question: given a meeting that just says "The Sleep Company", which documents are the evidence for this brief? This story is that discovery layer. It scans a local documents root, treats each sub-folder as a prospect company, and resolves the rep's free-text company name to the correct folder — normalizing casing, dropping a leading "The", and collapsing punctuation so "The Sleep Company", "sleep company", and the raw slug `sleep_company` all land on the same folder.

The critical product rule is that Zoho is never a prospect. The `zoho/` folder holds shared internal product knowledge (what Zoho CRM, Desk, and the rest actually do) and is appended as evidence to every single brief, while being excluded from the list of companies a rep can pick. This is what makes cross-source synthesis possible: the pain-hypothesis and recommended-angle sections can only map prospect signal to Zoho products because both sets of documents arrive together in one source list, each tagged with its origin ("prospect" vs "zoho") so downstream code and citations know which side a fact came from.

Each discovered document becomes a `SourceDoc` record with a stable citation marker (`S1`, `S2`, …) assigned in a single sequence across prospect docs first then Zoho docs, a readable title derived from the filename, and its extracted text (capped per document to control token usage and latency). The prospect signal is a local folder rather than live scraping — a deliberate POC shortcut — but discovery is written as a swappable provider so a live-fetch implementation can replace the local folder later without changing how briefs are synthesized.

## Acceptance criteria
```gherkin
Scenario: Free-text company name resolves to its docs folder
  Given a docs folder named "sleep_company" exists
  When a meeting names the prospect "The Sleep Company"
  Then the name resolves to the "sleep_company" slug
  And the same slug resolves from "sleep company" and from the raw slug
```

```gherkin
Scenario: Zoho knowledge is appended to every brief's sources
  Given any prospect company is resolved
  When its sources are loaded
  Then the prospect's documents are included and tagged "prospect"
  And the shared Zoho documents are appended and tagged "zoho"
  And each document has a unique sequential [S#] marker
```

```gherkin
Scenario: Zoho is never offered as a prospect
  Given the docs root contains a "zoho" folder alongside company folders
  When the list of prospect companies is built
  Then the "zoho" folder is excluded from the company list
  And hidden folders (starting with "." or "_") are excluded too
```

## Technical notes (reference)
- Key files: `backend/app/services/sources.py`, `backend/app/contracts.py` (`SourceDoc`), `backend/app/schemas.py` (`CompanyRead`)
- `resolve_company_slug` tries an exact slug match first, then a normalized match against both the folder name and its display name; `COMPANY_NAMES` holds slug→display-name overrides (e.g. `sleep_company` → "The Sleep Company").
- `load_company_sources` loads `docs/<slug>/` as tag "prospect" then `docs/zoho/` as tag "zoho", assigning `S#` markers in one continuous sequence; per-doc text is truncated to `_MAX_DOC_CHARS` (8000).
- POC shortcut: local folder provider instead of live scraping; the seam is intentional so a live fetcher can be swapped in without touching `brief_engine.py`.

## Definition of Done
- [x] Company folders discovered under the docs root, excluding `zoho`/hidden
- [x] Free-text names resolve to slugs with normalization (leading "The", casing, punctuation)
- [x] Prospect + Zoho docs loaded into `SourceDoc` records with sequential `S#` markers and origin tags
- [x] Zoho appended to every brief and excluded from the prospect list
- [x] Per-document text capped for token/latency control
