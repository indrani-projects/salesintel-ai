# SI-8.2 — Backend unit & API test suite (pytest)

| Field | Value |
|---|---|
| Issue type | Story |
| Parent epic | SI-8 — Quality, Testing & Demo Readiness |
| Status | Done |
| Priority | High |
| Story points | 5 |
| Component | Quality |
| Labels | backend, testing, qa |

## User story
As a developer, I want a pytest suite that covers the backend units and the full API flow under mock modes, so that I can refactor the intelligence layer with confidence and prove the demo path is green before every commit.

## Description
The backend carries the product's intelligence — source discovery, PDF ingestion, LLM synthesis, HTML render, grounded chat, persona-scoped briefs, and send-as-email — and until now had no automated coverage (the original repo note read "no test suite"). This story adds ~30 passing pytest tests that lock in both the pure units and the end-to-end API behaviour, all running under `MOCK_LLM` / `MOCK_EMAIL` so they are fast, deterministic, quota-free, and hermetic.

The unit tests cover the building blocks in isolation: schema/DTO shapes and the persona section maps, company slug resolution (e.g. "The Sleep Company" → `sleep_company`), PDF text ingestion, the deterministic brief engine, and the JSON→HTML render. The email service has its own module (`test_email_service.py`) asserting that the AE digest highlights the recommended-angle and stakeholder sections, that persona-specific digests surface the right section titles and attachment filenames (`-ae-brief.html`, `-sdr-brief.html`, `-se-brief.html`), and that send is demo-mode when SMTP is not configured and errors cleanly on an empty recipient.

The API tests (`test_api.py`) drive the whole lifecycle through FastAPI's `TestClient`, which runs `BackgroundTasks` synchronously so a just-scheduled brief is ready by the next request. They verify health and the companies list (Sleep Company present), create a meeting and confirm the primary AE brief reaches `ready` with 9 sections and populated key facts, lazily generate the SDR (5-section) and SE (6-section) persona briefs via the toggle, exercise Scout for a grounded and an ungrounded question and confirm the persisted chat history, regenerate a brief, preview + demo-send the email (including the 409 when a persona brief is not yet ready), and finally delete a meeting and confirm its brief 404s.

A shared `conftest.py` sets `MOCK_LLM`, `MOCK_EMAIL`, and an isolated throwaway SQLite `DATABASE_URL` *before* the app is imported so pydantic-settings picks them up, exposes a session-scoped `TestClient` fixture (its context-manager entry triggers `init_db()`), and cleans up the test DB file afterward.

## Acceptance criteria
```gherkin
Scenario: The full meeting-to-brief-to-chat flow passes under mock modes
  Given the pytest suite runs with MOCK_LLM and MOCK_EMAIL enabled
  When it creates a Sleep Company meeting and polls the brief
  Then the AE brief reaches status ready with 9 sections and key facts
  And the SDR brief has 5 sections and the SE brief has 6 sections
  And Scout returns a grounded answer and an ungrounded answer with history persisted
```

```gherkin
Scenario: Email preview and demo-send are covered
  Given a Sleep Company meeting with a ready AE brief
  When the email preview and send endpoints are called
  Then the preview subject names the company and persona and email_configured is false
  And the send returns mode "demo" with delivered false
```

```gherkin
Scenario: Edge case — preview refuses a not-yet-generated persona brief
  Given a meeting created for the AE persona
  When the email preview is requested for the SE persona whose brief was never generated
  Then the endpoint responds 409 rather than composing a half-baked email
```

## Technical notes (reference)
- Key files: `backend/tests/conftest.py` (env + `client` fixture + DB cleanup), `backend/tests/test_api.py` (health, companies, create→brief→persona toggle→chat→regenerate→email→delete), `backend/tests/test_email_service.py` (compose/persona/demo-send/empty-recipient); plus unit tests for schemas, sources, ingestion, brief engine, and render.
- `TestClient` runs `BackgroundTasks` synchronously, so `_poll_brief` sees `ready` without real async waiting; `conftest` must set env vars before importing `app.main`.
- POC shortcut (intentional): tests run against an isolated file-based SQLite DB (`sqlite:///./test_salesintel.db`) that is deleted on teardown — no Postgres, no migrations.

## Definition of Done
- [x] `conftest.py` sets mock modes + isolated SQLite before app import and cleans up
- [x] Unit tests for schemas, sources, ingestion, brief engine, and render pass
- [x] API tests cover health, companies, create → brief → persona toggle → chat → regenerate → delete
- [x] Email service + email API tests cover compose, persona digests, demo-send, and the 409 not-ready case
- [x] ~30 tests pass deterministically with zero LLM quota consumed
