# SI-8.4 — Pre-commit quality gate

| Field | Value |
|---|---|
| Issue type | Story |
| Parent epic | SI-8 — Quality, Testing & Demo Readiness |
| Status | Done |
| Priority | Medium |
| Story points | 2 |
| Component | Quality |
| Labels | infra, qa, testing |

## User story
As a developer on a demo-critical POC, I want a pre-commit gate that runs the backend tests, the frontend build, and the E2E suite, so that no commit can regress the demo path.

## Description
The demo's reliability depends on the suites from SI-8.2 and SI-8.3 staying green. A test suite that nobody runs is worthless, so this story wires the checks into a pre-commit quality gate that fires automatically before every commit and blocks the commit if anything fails.

The gate runs three things in sequence: the backend pytest suite (under `MOCK_LLM`/`MOCK_EMAIL`, so it is fast and quota-free), `npm run build` on the frontend (`tsc -b && vite build`, which catches TypeScript and type-mirror drift between `schemas.py` and `types.ts`), and the Playwright E2E suite against fresh mock servers. Because all of it runs under mock modes, the gate needs no LLM key and no mail server and produces identical results on any machine.

All three must pass for the commit to proceed; a failure prints the failing step and aborts, so a broken demo path can never be committed. This keeps the ~30 backend tests and 4 E2E specs honest as the codebase evolves.

## Acceptance criteria
```gherkin
Scenario: A clean tree passes the gate and the commit proceeds
  Given the pre-commit gate is installed
  When a developer commits with all suites green
  Then pytest, npm build, and Playwright all pass
  And the commit is created
```

```gherkin
Scenario: Edge case — a failing check blocks the commit
  Given a change that breaks a backend test or the frontend build
  When the developer attempts to commit
  Then the gate reports the failing step and aborts
  And no commit is created until it is fixed
```

## Technical notes (reference)
- Runs: `pytest` (from `backend/`, mock modes via the test env) + `npm run build` (from `frontend/`) + `npx playwright test` (fresh mock servers per `playwright.config.ts`).
- All checks are hermetic under `MOCK_LLM`/`MOCK_EMAIL` — no LLM key or SMTP needed, so the gate is reproducible across machines and CI.
- POC shortcut (intentional): a lightweight local gate for a single-machine demo build rather than a full multi-stage CI pipeline.

## Definition of Done
- [x] Pre-commit gate runs pytest, npm build, and Playwright before each commit
- [x] Any failing check aborts the commit with a clear message
- [x] Gate runs entirely under mock modes — no quota, no real email
- [x] Documented as the required check before committing
