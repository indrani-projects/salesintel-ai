# EPIC SI-8 — Quality, Testing & Demo Readiness

| Field | Value |
|---|---|
| Issue type | Epic |
| Suggested key | SI-8 |
| Status | Done |
| Priority | High |
| Component | Quality |
| Labels | qa, testing, backend, frontend, infra |
| Story points (rollup) | 20 |

## Summary
Everything that makes the SalesIntel AI build reliable and the live demo repeatable — deterministic mock modes, a backend test suite, a frontend E2E suite, a pre-commit gate, and a full integration dry-run.

## Description
SalesIntel AI auto-generates a grounded, cited 9-section pre-sales briefing about a prospect through a Calendar → Dashboard → Brief → Scout-chatbot flow, with AE/SDR/SE personas and a "Send as email" feature. The headline demo is Zoho selling to "The Sleep Company". Because every brief and every Scout answer is normally produced by a live LLM (Gemini free tier), an un-guarded demo is both fragile and quota-hungry: a flaky network call or an exhausted daily quota can break the story on stage, and no two runs look the same. This epic exists to remove that fragility.

The cornerstone is a pair of deterministic **mock modes**. `MOCK_LLM` swaps the real LLM call in `brief_engine` and `chat_service` for canned, fully-shaped output, so briefs and Scout answers are identical on every run and cost zero quota. `MOCK_EMAIL` forces the "Send as email" feature into demo-send, so nothing ever leaves the machine during a test or a rehearsal. Together they make the entire product hermetic: CI can run it, Playwright can drive it, and a presenter can rehearse it a hundred times without touching a real API.

On top of that foundation sit the test suites. The backend has ~30 pytest tests spanning the pure units (schemas, source resolution, ingestion, brief engine, HTML render) and the full API flow (health, companies list, meeting → brief → persona toggle → Scout chat → regenerate → delete, plus email preview and demo-send). The frontend has four Playwright specs that boot fresh mock servers and click through the real UI — app shell, create-meeting dialog + dashboard, brief render + persona toggle + Scout, and email compose + demo-send — capturing screenshots at every step.

Finally, a **pre-commit quality gate** runs pytest + `npm run build` + Playwright before every commit so nothing regresses, and an **integration dry-run** story ties the whole thing together: FE↔BE wiring with status polling and CORS, empty/loading/error states, the seeded Sleep Company dropdown, README run steps, and a rehearsed end-to-end demo narrative.

## Stories in this epic
| Key | Story | Points | Priority |
|---|---|---|---|
| SI-8.1 | Deterministic MOCK_LLM / MOCK_EMAIL modes | 3 | High |
| SI-8.2 | Backend unit & API test suite (pytest) | 5 | High |
| SI-8.3 | Frontend E2E suite (Playwright + screenshots) | 5 | High |
| SI-8.4 | Pre-commit quality gate | 2 | Medium |
| SI-8.5 | End-to-end integration & demo dry-run | 5 | High |

## Epic acceptance criteria
```gherkin
Scenario: The full product runs without an LLM key or a mail server
  Given MOCK_LLM and MOCK_EMAIL are enabled
  When a rep adds a Sleep Company meeting and opens the brief, toggles personas, chats with Scout, and sends the brief by email
  Then every step succeeds with deterministic output
  And no Gemini quota is consumed and no email leaves the machine
```

```gherkin
Scenario: The test suites prove the demo path
  Given the backend pytest suite and the frontend Playwright suite
  When both run against fresh mock servers
  Then ~30 backend tests and 4 E2E specs pass
  And screenshots of every demo screen are captured
```

```gherkin
Scenario: Regressions are caught before they land
  Given the pre-commit quality gate is installed
  When a developer attempts a commit
  Then pytest, npm build, and Playwright must all pass first
  And a failure blocks the commit
```

## Out of scope
- Production observability, load testing, and performance benchmarking
- A real SMTP / transactional-email integration (deferred; demo-send stands in)
- Contract-testing or codegen to auto-sync `schemas.py` ↔ `types.ts` (kept hand-mirrored for the POC)
- Live web scraping of prospect signal (the local `docs/` folder stands in)

## Dependencies
- SI-1..SI-7 (the built product: calendar, brief engine, Scout chat, persona toggle, send-as-email) — this epic hardens and verifies them
