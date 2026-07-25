# EPIC SI-13 — Zoho Product Catalog (Plane B, deterministic, NO LLM)

| Field | Value |
|---|---|
| Issue type | Epic |
| Suggested key | SI-13 |
| Status | Done |
| Priority | High |
| Component | Intelligence |
| Labels | backend, ai, data |
| Story points (rollup) | 13 |

## Summary
Build the INTERNAL "Plane B" of the pain→product match: structured, deterministic knowledge of what each Zoho product actually does, cached from `zoho.com` with NO LLM, so a brief can weigh a prospect's pain points against real Zoho product descriptions. Complements SI-12 (Plane A, external prospect signal). Shipped as PR #12, branch `feat/zoho-catalog`.

## Description
A grounded pre-sales angle needs two planes. Plane A is the external prospect signal — the pain, the buying triggers, the competitor tooling — delivered by SI-12. Plane B is the internal counterpart: an accurate, up-to-date picture of *what Zoho sells and what each product is for*. Without it, the synthesis layer can only guess at which Zoho product answers a given pain. This epic builds Plane B as a compact, deterministic product catalog cached straight from Zoho's own pages, so a brief can match a prospect's pain points against real product descriptions rather than the model's recollection.

The catalog is assembled with **no LLM calls at any stage**. An editable seed (`zoho_catalog.py`) lists 15 curated Zoho sources — product overviews plus Zoho Assist integrations. A CLI builder (`app/tools/build_zoho_catalog.py`) fetches each source (reusing SI-12's keyless retrieval / trafilatura), writes the full clean content to `docs/zoho/products/<slug>.md`, and assembles a compact `docs/zoho/zoho_products_summary.md`. The condensing is purely **extractive, never abstractive** (`condense.py`): a lead paragraph plus up to N cleaned key points per product, so the same page always yields the same summary. Curating the catalog is a matter of editing the seed list and re-running the builder.

Only **static `www.zoho.com` pages are usable** by a keyless fetch. The `help.zoho.com/portal` knowledge base is a JavaScript application that renders nothing to a keyless retrieval, so product and marketing pages under `www.zoho.com` stand in for those integration topics — and a test enforces that no `help.zoho.com` URL is ever seeded. The context-length design is deliberate: the compact summary (~9 KB for 15 products) sits at the top level of `docs/zoho/` so it auto-loads into every brief, while the full per-product docs live in the `docs/zoho/products/` subfolder, which `sources._doc_files` (non-recursive) does NOT auto-inject. Briefs therefore get one short deterministic catalog instead of many long documents.

## Stories in this epic
| Key | Story | Points | Priority |
|---|---|---|---|
| SI-13.1 | Zoho catalog seed + deterministic extractive condenser | 5 | High |
| SI-13.2 | Catalog builder CLI + generated per-product docs & compact summary | 5 | High |
| SI-13.3 | Context-length design (auto-load summary, subfolder excluded) + verification | 3 | Medium |

## Epic acceptance criteria
```gherkin
Scenario: The catalog is built with no LLM calls
  Given the seed list of 15 Zoho sources
  When the builder runs
  Then each source is fetched with the keyless retrieval and condensed extractively
  And no LLM call is made at any stage
  And the same page always yields the same summary
```

```gherkin
Scenario: Only static pages are seeded
  Given the seed enforces static www.zoho.com pages
  When the seed is validated
  Then no help.zoho.com/portal (JavaScript-only) URL is present
  And every product overview and Assist integration resolves to a keyless-readable page
```

```gherkin
Scenario: One short catalog feeds every brief
  Given the compact summary lives at the top level of docs/zoho/
  When a brief is generated
  Then the ~9 KB summary auto-loads as shared Zoho knowledge
  And the full per-product docs in docs/zoho/products/ are NOT auto-injected
```

## Out of scope
- Any LLM/abstractive summarization of Zoho pages (condensing is deterministic and extractive only).
- Scraping the `help.zoho.com/portal` knowledge base — it is a JavaScript app that yields nothing to a keyless fetch.
- A vector DB or RAG layer over the product docs (the compact summary is stuffed into the existing call).
- Live/scheduled re-crawling — the catalog is rebuilt on demand by re-running the CLI.

## Dependencies
- SI-12 (Plane A) — provides the `retrieval.fetch_and_extract` / trafilatura keyless retrieval this epic reuses.
- The existing `sources` doc-loading seam (`_doc_files`, non-recursive) that auto-injects top-level `docs/zoho/` content.
- `docs/shared/SalesIntel_Research_Guide.doc.pdf` — Section 1 maps the 5 target companies to their "lead-with" Zoho products.
- The user-supplied Zoho help / marketing URLs that seed the catalog.

## Verification
- **Backend pytest all green**, incl. new `tests/test_zoho_catalog.py` (4 offline tests: deterministic condensers with heading/STEP stripping + dedupe, seed integrity, unique slugs, no JS-only URLs).
- **npm build** clean; **Playwright 6/6** — no regressions (the new summary auto-loads under `MOCK_LLM` without changing canned output).
- Live: `python -m app.tools.build_zoho_catalog` produced 15/15 product docs + the summary, 0 misses.
