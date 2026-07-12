# SI-3.2 — Document ingestion (PyMuPDF extraction + cache)

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
As the brief engine, I want each source document turned into clean plain text quickly and only once, so that synthesis runs on readable evidence and repeat generations don't re-parse the same PDFs.

## Description
Source documents arrive as PDFs (and occasionally Markdown, text, or HTML), but the LLM needs plain text. This story is the extraction layer that converts each file to normalized text. PDFs go through PyMuPDF (fitz) page by page; Markdown and text files are read directly; HTML is crudely stripped of script/style blocks and tags with a handful of common entities decoded. Whatever the input, the output is run through a whitespace normalizer that collapses runs of blank lines and trims trailing spaces so the text fed to the model is compact and consistent.

Extraction is the slow part of a cold run, so it is cached on disk. The cache key is derived from the file's absolute path plus its modification time and size — meaning an unchanged file is read from cache on every subsequent brief, but editing or replacing a document automatically invalidates the old entry and forces a fresh extraction. This is what makes regeneration and multi-persona briefs feel instant after the first run, without ever serving stale text.

Robustness is a first-class requirement here because this code sits underneath the "background task must never crash" rule. A missing file returns empty text rather than raising; an unreadable or malformed document falls back to empty text; and the cache is strictly best-effort — if the cache directory can't be written, extraction still succeeds, it just isn't cached. Nothing in ingestion is allowed to take down a brief.

## Acceptance criteria
```gherkin
Scenario: A PDF is extracted to clean plain text
  Given a prospect PDF in the docs folder
  When the document is ingested
  Then its text is extracted page by page via PyMuPDF
  And blank-line runs and trailing whitespace are normalized
```

```gherkin
Scenario: Unchanged files are served from cache
  Given a document has already been extracted once
  When it is ingested again without being modified
  Then the cached text is returned without re-parsing
  And modifying the file (changing mtime or size) invalidates the cache and re-extracts
```

```gherkin
Scenario: A broken or missing document never crashes the engine
  Given a document that is missing or cannot be parsed
  When ingestion runs
  Then it returns empty text instead of raising
  And a failure to write the cache does not fail the extraction
```

## Technical notes (reference)
- Key files: `backend/app/services/ingestion.py`
- `extract_text` dispatches by suffix: `.pdf` → PyMuPDF, `.md`/`.txt` → direct read, `.html`/`.htm` → tag stripping; unknown types get a best-effort plain read.
- Cache lives under `backend/.cache/`, keyed by SHA-256 of `abs_path|mtime|size`; reads/writes wrapped so cache failures are swallowed.
- `_clean` normalizes CRLF, strips trailing spaces per line, and collapses 3+ newlines to 2.

## Definition of Done
- [x] PDF/Markdown/text/HTML extraction implemented with whitespace normalization
- [x] On-disk cache keyed on path + mtime + size, invalidating on file change
- [x] Missing/unparseable files return empty text without raising
- [x] Cache writes are best-effort and never fail extraction
