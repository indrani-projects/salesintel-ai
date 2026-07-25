# SI-11.3 — Web-first source seam

| Field | Value |
|---|---|
| Issue type | Story |
| Parent epic | SI-11 — Web-First Prospect Intel (generic, on-demand) + filtered cache |
| Status | Done |
| Priority | High |
| Story points | 5 |
| Component | Intelligence |
| Labels | backend, ai, api |

## User story
As a developer, I want a single source-loading seam that prefers web intel and falls back to local docs, so that both the brief engine and Scout consume live intel unchanged — including for companies that have no docs folder at all.

## Description
This story adds `sources.load_company_intel(company_name, slug=None)` as the one place that assembles a prospect's source set. Its order is **web-first**: it calls the keyless fetcher (SI-11.1, served through the SI-11.2 cache) and uses those documents when present. Only when the web returns nothing does it fall back to `_load_folder_docs(docs/<slug>/)`. In both cases `docs/zoho/` is always appended as shared Zoho product knowledge, and the combined set is stamped with shared **sequential `S#` markers** so citations remain stable across the whole source set.

Web documents are tagged `["web", …]` so provenance flows through into `SourceDoc.url` and, downstream, into the brief's `[S#]` citations — a reader can tell a claim came from a live source rather than a local PDF.

Crucially, the company **name** is threaded through the pipeline so unknown companies work end to end: `brief_engine.generate_brief` gains a `company_name` parameter, and `chat_service.answer_question` derives the company name from the brief. Because both surfaces now resolve their sources through this one seam, a company with no `docs/<slug>/` folder still produces a fully grounded brief and answerable Scout session. A `web_intel_enabled` config gates the behavior.

## Acceptance criteria
```gherkin
Scenario: Web intel is preferred when available
  Given web intel is enabled and returns documents for a company
  When load_company_intel runs
  Then the web documents are used as the prospect source set
  And each is tagged "web" so its provenance flows into SourceDoc.url and [S#] citations
```

```gherkin
Scenario: Fallback to local docs when the web is empty
  Given the web returns no documents for a company with a docs/<slug>/ folder
  When load_company_intel runs
  Then it falls back to _load_folder_docs(docs/<slug>/)
```

```gherkin
Scenario: Zoho knowledge and sequential markers are always applied
  Given any prospect source set (web or local)
  When the source set is assembled
  Then docs/zoho/ is appended as shared knowledge
  And every document carries a shared sequential S# marker
```

```gherkin
Scenario: Unknown company flows through both surfaces
  Given a company with no docs/<slug>/ folder
  When a brief is generated and Scout answers a question
  Then the company_name is threaded into generate_brief and derived in answer_question
  And both consume the same web-first seam unchanged
```

## Technical notes (reference)
- Key file: `backend/app/services/sources.py` — new `load_company_intel(company_name, slug=None)`.
- Web-first order: web fetch (cached) → `_load_folder_docs(docs/<slug>/)` fallback → always append `docs/zoho/`.
- Web docs tagged `["web", …]`; provenance carried on `SourceDoc.url` into `[S#]` citations; shared sequential `S#` numbering across the whole set.
- Name threading: `brief_engine.generate_brief` gains `company_name`; `chat_service.answer_question` derives it from the brief.
- Gated by `web_intel_enabled`; brief and Scout consume the seam with no other changes.

## Definition of Done
- [x] `sources.load_company_intel(company_name, slug=None)` implemented, web-first with local fallback.
- [x] Web docs tagged `["web", …]`; provenance flows into `SourceDoc.url` and brief `[S#]` citations.
- [x] `docs/zoho/` always appended; shared sequential `S#` markers across the source set.
- [x] `company_name` threaded into `generate_brief`; derived from the brief in `answer_question`.
- [x] Both brief and Scout consume the one seam unchanged; gated by `web_intel_enabled`.
