# SI-12.1 — Research-guide keyword taxonomy + rule-based credibility scoring

| Field | Value |
|---|---|
| Issue type | Story |
| Parent epic | SI-12 — Deterministic Web-to-Doc Prospect Prep (Plane A, NO LLM) |
| Status | Done |
| Priority | High |
| Story points | 5 |
| Component | Intelligence |
| Labels | backend, ai, data |

## User story
As a sales rep, I want the app to know exactly what to look for on a web page and how trustworthy each source is, so that my prospect docs contain sales-relevant material from credible sources rather than raw, unranked scrapings.

## Description
This story encodes the deterministic "judgement" of the prep plane in two rule-based modules — no LLM in either.

`backend/app/services/research_keywords.py` turns **Section 3** of the research guide into six keyword **categories**: `financial_intel`, `product_strategy`, `leadership_changes`, `pain_points`, `social_signals`, and `job_intent`. `match_categories(text, company, competitors)` returns which categories a passage hits, case-insensitively. Short acronyms such as `arr`, `nrr`, `eps`, and `cfo` are **word-bounded**, so they match "ARR grew" but never fire inside a word like "warranty". `search_queries(company, competitors)` builds focused, keyless search queries from the same taxonomy so retrieval looks for exactly the categories the guide cares about.

`backend/app/services/credibility.py` is a pure, rule-based scorer: `score(url, company) -> (0-100, source_type)`. Tiers are fixed: gov / SEC = 95 (regulatory), Wikipedia = 85 (encyclopedia), the official company domain = 90, tier-1 press = 80, reddit / forums / blogs = 35 (social), everything else = 55 (web). The official-domain match is deliberately strict — the domain's primary label must equal the WHOLE compacted company name — so `thesleepcompany.in` is "official" for The Sleep Company while the unrelated `sleepnumber.com` is not.

Together these modules give the orchestrator everything it needs to decide *what to keep* and *how much to trust it*, all without a model call.

## Acceptance criteria
```gherkin
Scenario: A passage is tagged by research-guide category
  Given a passage mentioning "ARR grew 40% and the new CFO joined"
  When match_categories runs
  Then it returns financial_intel and leadership_changes
```

```gherkin
Scenario: Short acronyms are word-bounded
  Given a passage containing the word "warranty"
  When match_categories runs
  Then the "arr" acronym does not match inside "warranty"
```

```gherkin
Scenario: Search queries are built from the taxonomy
  Given a company and its competitors
  When search_queries runs
  Then it returns focused keyless queries covering the guide's categories
```

```gherkin
Scenario: Credibility tiers are assigned by rule
  Given a SEC URL, a Wikipedia URL, and a reddit URL
  When score runs on each
  Then they return 95 regulatory, 85 encyclopedia, and 35 social respectively
```

## Technical notes (reference)
- Key files: `backend/app/services/research_keywords.py`, `backend/app/services/credibility.py`.
- `research_keywords.py` categories: financial_intel, product_strategy, leadership_changes, pain_points, social_signals, job_intent — derived from research guide Section 3.
- `match_categories(text, company, competitors)` is case-insensitive; short acronyms (arr/nrr/eps/cfo) are word-bounded to avoid substring false positives.
- `search_queries(company, competitors)` expands the taxonomy into focused keyless queries.
- `credibility.score(url, company) -> (0-100, source_type)`; tiers: gov/SEC 95, Wikipedia 85, official domain 90, tier-1 press 80, social 35, else 55.
- Official-domain check requires the domain's primary label to equal the whole compacted company name.

## Definition of Done
- [x] `research_keywords.py` encodes the six Section 3 categories.
- [x] `match_categories` returns hit categories case-insensitively, with word-bounded short acronyms.
- [x] `search_queries` builds focused keyless queries from the taxonomy.
- [x] `credibility.score` assigns the fixed tiers with source_type labels.
- [x] Official-domain match is strict (whole compacted company name), so look-alike domains are not "official".
- [x] Neither module imports the LLM client.
