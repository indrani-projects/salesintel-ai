# SI-6.3 — Email settings & DTOs

| Field | Value |
|---|---|
| Issue type | Story |
| Parent epic | SI-6 — Brief Delivery: Web View & Email |
| Status | Done |
| Priority | Medium |
| Story points | 2 |
| Component | Delivery |
| Labels | backend, infra |

## User story
As a developer running the demo, I want email delivery to be configuration-driven with clear DTOs, so that the "Send as email" feature works out of the box in demo mode and switches to real SMTP sending purely through environment variables.

## Description
This story establishes the configuration and data contracts that the rest of the email feature builds on. All SMTP settings live in the shared `Settings` object and are populated from `backend/.env`: `smtp_host`, `smtp_port` (default 587), `smtp_user`, `smtp_password`, `smtp_from` (falls back to `smtp_user` when blank), plus `default_recipient` (which prefills the dialog's To: field) and a `mock_email` flag. A derived `email_configured` property returns true only when host, user, and password are all present, and `email_from` resolves the effective sender address.

The behavior mirrors the existing LLM mock pattern so it feels consistent across the codebase: real delivery is attempted **only** when `email_configured` is true **and** `mock_email` is off. With no SMTP credentials (the default for the demo), the feature runs in "demo send" mode — composed, previewed, confirmed, but never actually delivered. `mock_email` additionally lets tests and E2E force demo-send even when credentials happen to be present, so verification never contacts a real mail server.

The story also defines the three API DTOs in the shared schema module: `EmailPreview` (subject, persona-tailored `body_html`, `attachment_filename`, `recipient_default`, and an `email_configured` flag telling the UI whether a real send will happen), `EmailSendRequest` (the target `recipient`), and `EmailSendResult` (`delivered`, `mode` of `sent`/`demo`/`error`, `recipient`, `subject`, and a human-readable `message`). These shapes are the seam consumed by the compose service (SI-6.4), the API (SI-6.5), and the hand-mirrored frontend types.

## Acceptance criteria
```gherkin
Scenario: Demo mode is the default with no SMTP configured
  Given backend/.env has no SMTP credentials
  When the app reads settings
  Then email_configured is false
  And the email feature will run in demo-send mode
```

```gherkin
Scenario: Real send is enabled by configuration
  Given smtp_host, smtp_user, and smtp_password are all set
  And mock_email is off
  When the app reads settings
  Then email_configured is true
  And email_from resolves to smtp_from, or smtp_user when smtp_from is blank
```

```gherkin
Scenario: Mock flag forces demo-send even when configured (edge case)
  Given SMTP credentials are present but mock_email is true
  When the app evaluates whether to send
  Then a real send is not attempted and demo-send is used
```

## Technical notes (reference)
- Key files: `backend/app/config.py`, `backend/app/schemas.py`, `backend/.env.example`.
- `config.py`: `smtp_host/port/user/password/from`, `default_recipient`, `mock_email`; `email_configured` = host+user+password all non-blank; `email_from` = `smtp_from or smtp_user`.
- `schemas.py`: `EmailPreview`, `EmailSendRequest`, `EmailSendResult`; keep field names in sync with `frontend/src/api/types.ts` (hand-mirrored).
- POC shortcut: demo-send is intentionally the default so the demo needs no SMTP; new-Outlook-only machine → plain SMTP transport only, no COM.

## Definition of Done
- [x] SMTP settings, `default_recipient`, and `mock_email` are read from `backend/.env`.
- [x] `email_configured` and `email_from` properties behave as specified.
- [x] `EmailPreview` / `EmailSendRequest` / `EmailSendResult` DTOs are defined in `schemas.py`.
- [x] Field names match the hand-mirrored frontend types.
