# SI-13.2 — Catalog builder CLI + generated per-product docs & compact summary

| Field | Value |
|---|---|
| Issue type | Story |
| Parent epic | SI-13 — Zoho Product Catalog (Plane B, deterministic, NO LLM) |
| Status | Done |
| Priority | High |
| Story points | 5 |
| Component | Intelligence |
| Labels | backend, data, ai |

## User story
As a sales rep, I want the Zoho catalog generated from Zoho's own pages into ready-to-use docs, so that every brief draws on an accurate, current picture of what each Zoho product does — without anyone hand-writing the descriptions.

## Description
This story adds the CLI builder `backend/app/tools/build_zoho_catalog.py`, run as `python -m app.tools.build_zoho_catalog`. It walks the `ZOHO_SOURCES` seed and, for each source, fetches the page by **reusing SI-12's keyless retrieval** (`retrieval.fetch_and_extract` / trafilatura) — no new fetcher, no LLM.

For each source it writes the full clean content to `docs/zoho/products/<slug>.md`, then assembles a compact `docs/zoho/zoho_products_summary.md` — one short entry per product giving what it does (the extractive lead paragraph), its key points, and the source URL. The condensing goes through `condense.py`, so the generated summary is deterministic and extractive.

Because only static `www.zoho.com` pages are keyless-readable, the builder operates entirely over the curated static seed; the JavaScript-rendered `help.zoho.com/portal` knowledge base is deliberately out of scope for retrieval. The live run was confirmed: `python -m app.tools.build_zoho_catalog` produced 15/15 product docs plus the summary, with 0 misses.

## Acceptance criteria
```gherkin
Scenario: Builder fetches and writes per-product docs
  Given the ZOHO_SOURCES seed of 15 sources
  When python -m app.tools.build_zoho_catalog runs
  Then each source is fetched with SI-12's keyless retrieval
  And the full clean content is written to docs/zoho/products/<slug>.md
```

```gherkin
Scenario: A compact summary is assembled
  Given the per-product docs are written
  When the builder assembles the summary
  Then docs/zoho/zoho_products_summary.md has one short entry per product
  And each entry gives what it does, key points, and the source URL
```

```gherkin
Scenario: Live build produces the full catalog
  Given a live run over the 15-source seed
  When the builder completes
  Then 15/15 product docs and the summary are produced
  And there are 0 misses
```

```gherkin
Scenario: Slugs are unique
  Given the products are slugified for filenames
  When the docs are written
  Then every product resolves to a unique slug
  And no per-product doc overwrites another
```

## Technical notes (reference)
- Key file: `backend/app/tools/build_zoho_catalog.py`, invoked as `python -m app.tools.build_zoho_catalog`.
- Retrieval reuses SI-12: `retrieval.fetch_and_extract` / trafilatura — keyless, no LLM.
- Outputs: full clean content per source → `docs/zoho/products/<slug>.md`; compact one-entry-per-product → `docs/zoho/zoho_products_summary.md` (what it does + key points + source URL).
- Condensing is delegated to `condense.py`, keeping the generated summary deterministic and extractive.
- `help.zoho.com/portal` is excluded from retrieval (JavaScript app, unreadable keyless); the builder runs over the static `www.zoho.com` seed only.
- Live run: 15/15 product docs + summary, 0 misses.

## Definition of Done
- [x] `build_zoho_catalog.py` runs as `python -m app.tools.build_zoho_catalog` over the 15-source seed.
- [x] Each source is fetched with SI-12's keyless `retrieval.fetch_and_extract` / trafilatura — no LLM.
- [x] Full clean content is written to `docs/zoho/products/<slug>.md`, one file per source.
- [x] A compact `docs/zoho/zoho_products_summary.md` is assembled (what it does + key points + source URL per product).
- [x] Every product resolves to a unique slug (test-enforced).
- [x] Live build verified: 15/15 product docs + summary, 0 misses.
