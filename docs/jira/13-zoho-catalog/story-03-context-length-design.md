# SI-13.3 — Context-length design (auto-load summary, subfolder excluded) + verification

| Field | Value |
|---|---|
| Issue type | Story |
| Parent epic | SI-13 — Zoho Product Catalog (Plane B, deterministic, NO LLM) |
| Status | Done |
| Priority | Medium |
| Story points | 3 |
| Component | Intelligence |
| Labels | backend, data, ai |

## User story
As a sales rep, I want every brief to draw on the Zoho catalog without blowing the context budget, so that the model gets one short deterministic product catalog rather than many long documents — and I want proof the change ships no regressions.

## Description
This story is the deliberate context-length design that makes the catalog usable inside a single brief call. The compact `docs/zoho/zoho_products_summary.md` (~9 KB for 15 products) sits at the **top level** of `docs/zoho/`, so `sources._doc_files` auto-loads it as shared Zoho knowledge into every brief. The full per-product docs live in the `docs/zoho/products/` **subfolder**, which `sources._doc_files` (non-recursive) does NOT auto-inject. The net effect: briefs get one short deterministic catalog instead of 15 long product documents, keeping the single-call POC design within budget while still grounding the pain→product match in real Zoho descriptions.

Verification is the other half of the story. Backend pytest is all green including the new `tests/test_zoho_catalog.py` — 4 offline tests covering the deterministic condensers (heading/STEP stripping + dedupe), seed integrity, unique slugs, and no JS-only URLs. `npm build` is clean and Playwright is 6/6 with no regressions: the new summary auto-loads under `MOCK_LLM` without changing the canned output, so the visual E2E is unaffected.

## Acceptance criteria
```gherkin
Scenario: The compact summary auto-loads into every brief
  Given zoho_products_summary.md at the top level of docs/zoho/
  When a brief is generated
  Then sources._doc_files auto-loads the ~9 KB summary as shared Zoho knowledge
```

```gherkin
Scenario: Full per-product docs are excluded from auto-injection
  Given the full docs live in the docs/zoho/products/ subfolder
  When sources._doc_files loads docs/zoho/
  Then the non-recursive loader does NOT inject the subfolder docs
  And the brief receives one short catalog, not 15 long documents
```

```gherkin
Scenario: No regressions under mock mode
  Given MOCK_LLM is enabled
  When the Playwright E2E runs
  Then the new summary auto-loads without changing the canned output
  And Playwright is 6/6
```

```gherkin
Scenario: Offline catalog tests pass
  Given tests/test_zoho_catalog.py
  When backend pytest runs
  Then the deterministic condensers, seed integrity, unique slugs, and no-JS-URL checks all pass
```

## Technical notes (reference)
- Placement is the design: `docs/zoho/zoho_products_summary.md` (~9 KB, 15 products) at the top level → auto-loaded by `sources._doc_files`; `docs/zoho/products/*.md` in the subfolder → NOT auto-injected (loader is non-recursive).
- Result: briefs get one short deterministic catalog instead of many long docs, keeping the single-call design in budget.
- New tests: `backend/tests/test_zoho_catalog.py` — 4 offline tests (deterministic condensers with heading/STEP stripping + dedupe, seed integrity, unique slugs, no JS-only `help.zoho.com` URLs).
- Regression proof: `MOCK_LLM` E2E — the summary auto-loads without changing canned output, so Playwright stays 6/6.

## Definition of Done
- [x] Compact summary placed at top level of `docs/zoho/` so `sources._doc_files` auto-loads it into every brief.
- [x] Full per-product docs kept in the `docs/zoho/products/` subfolder, excluded from the non-recursive auto-injection.
- [x] `tests/test_zoho_catalog.py` (4 offline tests) green: condensers, seed integrity, unique slugs, no JS-only URLs.
- [x] Backend pytest all green; `npm build` clean; Playwright 6/6 with no regressions.
- [x] Verified the summary auto-loads under `MOCK_LLM` without changing canned output.
