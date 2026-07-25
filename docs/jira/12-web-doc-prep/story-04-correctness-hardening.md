# SI-12.4 — Correctness hardening: official-domain precision, word-bounded acronyms, cache test isolation

| Field | Value |
|---|---|
| Issue type | Story |
| Parent epic | SI-12 — Deterministic Web-to-Doc Prospect Prep (Plane A, NO LLM) |
| Status | Done |
| Priority | Medium |
| Component | Intelligence |
| Labels | backend, ai, data, testing |

## User story
As a sales rep, I want the prep stage to score sources and match keywords accurately, and I want a live prep run to never leak into the test suite, so that my prospect docs are trustworthy and the build stays deterministic.

## Description
While preparing the six target companies, three correctness issues surfaced in the deterministic plane and were fixed in this story.

**Official-domain precision.** The credibility scorer originally matched an official company domain too loosely, so `sleepnumber.com` was falsely scored as "official" for The Sleep Company. The check now requires the domain's primary label to equal the WHOLE compacted company name, so `thesleepcompany.in` is official while the unrelated `sleepnumber.com` is not.

**Word-bounded short acronyms.** Short acronyms in the keyword taxonomy (`arr`, `nrr`, `eps`, `cfo`) matched as substrings, so a passage containing "warranty" falsely hit the `arr` financial keyword. Short acronyms are now word-bounded, so they match only whole tokens and no longer fire inside unrelated words.

**Prepared-cache test isolation.** A live `prepare` run wrote into `backend/.cache/prepared/` and could leak into the test suite. The prepared cache is now isolated per test in `conftest`, so a real prepare run no longer affects test outcomes and the suite stays hermetic.

## Acceptance criteria
```gherkin
Scenario: A look-alike domain is not "official"
  Given the company "The Sleep Company"
  When credibility scores sleepnumber.com and thesleepcompany.in
  Then thesleepcompany.in is official (90) and sleepnumber.com is not
```

```gherkin
Scenario: A short acronym does not match inside a word
  Given a passage containing "warranty"
  When match_categories runs
  Then the "arr" acronym does not match and financial_intel is not falsely triggered
```

```gherkin
Scenario: A live prepare run does not leak into tests
  Given a live prepare run wrote to backend/.cache/prepared/
  When the test suite runs
  Then conftest isolates the prepared cache per test
  And test outcomes are unaffected by the live run
```

## Technical notes (reference)
- Official-domain fix in `credibility.py`: domain primary label must equal the whole compacted company name.
- Word-bounded short acronyms in `research_keywords.py`: arr/nrr/eps/cfo match whole tokens only (no substring hits inside e.g. "warranty").
- Prepared-cache isolation in `tests/conftest.py`: a live prepare run no longer leaks into tests.
- Verified by `tests/test_prep.py` (offline, no network, no LLM, ~10 tests).

## Definition of Done
- [x] Official-domain match is strict; `sleepnumber.com` is no longer "official" for The Sleep Company.
- [x] Short acronyms (arr/nrr/eps/cfo) are word-bounded and do not match inside words like "warranty".
- [x] `conftest` isolates the prepared cache per test; a live prepare run cannot leak in.
- [x] `tests/test_prep.py` passes offline with no network and no LLM (~10 tests).
- [x] Backend pytest all green; npm build clean; Playwright 6/6 unchanged.
