# SI-13.1 — Zoho catalog seed + deterministic extractive condenser

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
As a sales rep, I want a curated, deterministic list of what each Zoho product does, so that a brief can match a prospect's pain points against real Zoho product descriptions instead of the model's recollection — with no LLM in the loop.

## Description
This story introduces two deterministic building blocks: `zoho_catalog.py` and `condense.py`.

`zoho_catalog.py` holds an editable seed `ZOHO_SOURCES` of 15 sources: product overviews (Zoho Payroll, Expense, Bigin, Bookings, Forms, SalesIQ, Thrive, RouteIQ) plus 7 Zoho Assist integrations (Desk, SalesIQ, CRM, Meeting, Bookings, Flow, Mail). Each entry is `{product, url, kind}` where `kind` is `"overview"` or `"integration"`. Only **static `www.zoho.com` pages** are usable: the `help.zoho.com/portal` knowledge base is a JavaScript app that yields nothing to a keyless fetch, so product/marketing pages are used for those integration topics instead. A test enforces that no `help.zoho.com` URL is ever seeded. Curating the catalog is a matter of editing this list and re-running the builder.

`condense.py` is the deterministic, **extractive (never abstractive)** condenser — no LLM. `lead_paragraph(md)` returns the first substantive prose sentence, trimmed; `key_points(md, cap)` returns up to N bullet points cleaned of markdown, heading, and STEP-prefix noise. Because the logic is purely extractive, the same page always yields the same summary — a property the offline tests pin down (heading/STEP stripping + dedupe).

## Acceptance criteria
```gherkin
Scenario: Seed lists 15 static Zoho sources
  Given the ZOHO_SOURCES seed
  When it is loaded
  Then it contains 15 entries of product overviews and Zoho Assist integrations
  And each entry has a product, a url, and a kind of "overview" or "integration"
```

```gherkin
Scenario: No JavaScript-only knowledge-base URLs are seeded
  Given the seed enforces keyless-readable pages
  When the seed is validated
  Then no help.zoho.com URL is present
  And every source resolves to a static www.zoho.com page
```

```gherkin
Scenario: Condensing is deterministic and extractive
  Given the same product page markdown
  When lead_paragraph and key_points run twice
  Then both runs return identical output
  And no LLM call is made
```

```gherkin
Scenario: Key points are cleaned of noise
  Given page markdown with headings, STEP prefixes, and duplicate lines
  When key_points runs with a cap
  Then heading and STEP-prefix noise is stripped
  And duplicate points are de-duplicated
  And at most cap points are returned
```

## Technical notes (reference)
- Key files: `backend/app/services/zoho_catalog.py`, `backend/app/services/condense.py`.
- `ZOHO_SOURCES`: 15 curated entries — 8 product overviews + 7 Zoho Assist integrations — each `{product, url, kind: "overview"|"integration"}`.
- Only static `www.zoho.com` pages are usable; `help.zoho.com/portal` is a JavaScript app that returns nothing to a keyless fetch, so marketing/product pages stand in — a test enforces no `help.zoho.com` URLs.
- `condense.py` is extractive, never abstractive, no LLM: `lead_paragraph(md)` (first substantive prose sentence, trimmed) + `key_points(md, cap)` (up to N cleaned bullets, heading/STEP-prefix noise stripped, de-duplicated).
- Determinism is a hard requirement: the same page always yields the same summary.

## Definition of Done
- [x] `zoho_catalog.py` seeds 15 static Zoho sources (8 overviews + 7 Assist integrations), each `{product, url, kind}`.
- [x] A test enforces no `help.zoho.com` (JavaScript-only) URL is seeded.
- [x] `condense.py` provides extractive `lead_paragraph` and `key_points`, with NO LLM.
- [x] `key_points` strips heading/STEP-prefix noise and de-duplicates, capped at N.
- [x] Condensing is deterministic — the same page always yields the same summary.
