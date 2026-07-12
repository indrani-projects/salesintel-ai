# SI-8.1 — Deterministic MOCK_LLM / MOCK_EMAIL modes

| Field | Value |
|---|---|
| Issue type | Story |
| Parent epic | SI-8 — Quality, Testing & Demo Readiness |
| Status | Done |
| Priority | High |
| Story points | 3 |
| Component | Quality |
| Labels | backend, ai, testing |

## User story
As a presenter and CI pipeline, I want brief generation and Scout answers to be fully deterministic and email delivery to be safely faked, so that the demo is repeatable and CI is hermetic without burning LLM quota or sending real email.

## Description
Normally every brief and every Scout reply is produced by a live OpenAI-compatible LLM call (default: Gemini free tier), and "Send as email" can reach a real SMTP server. That makes the demo fragile — a slow network, an exhausted daily quota, or a mistyped recipient can all break the story — and it makes automated testing impossible to run cheaply or offline. This story introduces two switches that neutralise both risks.

`MOCK_LLM` is a boolean setting on `config.Settings` (env var `MOCK_LLM`). When on, `brief_engine` returns a deterministic, fully-shaped brief — all nine sections present, key facts populated, sources cited — instead of calling the LLM, and `chat_service` returns canned grounded/ungrounded answers keyed off the question. Output is byte-identical run to run, so tests can assert on exact content and a presenter sees the same brief every rehearsal, at zero quota cost.

`MOCK_EMAIL` is the email counterpart (env var `MOCK_EMAIL`). The email service already only sends for real when SMTP is configured; `MOCK_EMAIL` forces demo-send even when SMTP creds exist, guaranteeing that a test or rehearsal never contacts a mail server. The compose + preview + confirm flow still runs end to end — only the final network hop is skipped — so the UI and the tests exercise the whole feature.

Both switches default to off (production behaviour) and are flipped on by the test fixtures and the Playwright web-server config, so real runs are unaffected while every automated run is hermetic.

## Acceptance criteria
```gherkin
Scenario: MOCK_LLM produces a deterministic, fully-shaped brief
  Given MOCK_LLM is enabled
  When a brief is generated for The Sleep Company
  Then all nine sections and the key facts are populated without any LLM call
  And the output is identical on every subsequent run
```

```gherkin
Scenario: MOCK_LLM keeps Scout deterministic for grounded and ungrounded questions
  Given MOCK_LLM is enabled
  When Scout is asked a grounded question and then an out-of-scope question
  Then the first answer is marked grounded and the second is marked not grounded
  And neither answer consumes Gemini quota
```

```gherkin
Scenario: MOCK_EMAIL forces demo-send even with SMTP configured
  Given SMTP credentials are present but MOCK_EMAIL is enabled
  When the composed brief email is sent
  Then the result reports mode "demo" and delivered false
  And no connection is made to the mail server
```

## Technical notes (reference)
- Key files: `backend/app/config.py` (the `mock_llm` / `mock_email` settings + `email_configured`), `backend/app/services/brief_engine.py` (`if settings.mock_llm:` branch + `_mock_brief`), `backend/app/services/chat_service.py` (`if settings.mock_llm:` branch), `backend/app/services/email_service.py` (`should_send = settings.email_configured and not settings.mock_email`)
- Enabled in tests via `backend/tests/conftest.py` (`os.environ["MOCK_LLM"]="1"`, `MOCK_EMAIL="1"`) and in E2E via `frontend/playwright.config.ts` web-server `env` block.
- POC shortcut (intentional): the mock brief is a canned fixture, not a recorded golden capture of a real LLM response — good enough to prove the flow and keep the demo stable.

## Definition of Done
- [x] `mock_llm` and `mock_email` settings added to `config.Settings`, defaulting off
- [x] `brief_engine` short-circuits to a deterministic 9-section brief under `MOCK_LLM`
- [x] `chat_service` returns deterministic grounded/ungrounded answers under `MOCK_LLM`
- [x] `email_service` forces demo-send under `MOCK_EMAIL` regardless of SMTP config
- [x] Both modes exercised by the pytest and Playwright suites with zero quota use
