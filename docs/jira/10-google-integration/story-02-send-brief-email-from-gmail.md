# SI-10.2 — Send brief email from the rep's Gmail

| Field | Value |
|---|---|
| Issue type | Story |
| Parent epic | SI-10 — Google Workspace Integration |
| Status | Done |
| Priority | High |
| Story points | 3 |
| Component | Integrations |
| Labels | backend, frontend, api, google, email |

## User story
As a sales rep, I want the brief email to be sent from my own Gmail when I've connected Google, so that it reaches the recipient as a real message from me and shows up in my Sent folder.

## Description
This story adds Gmail as the **preferred transport** for the existing "Send as email" flow (SI-6). `email_service.send_brief_email` now checks whether Google is connected first: if it is, the persona-tailored digest and full-brief attachment are sent through the **Gmail API** (`users.messages.send`) from the connected account, returning a new send mode `EmailSendResult.mode = "gmail"`. If Google is not connected, the existing precedence is unchanged — real SMTP when configured, otherwise demo-send. Gmail simply sits at the top of that ladder, so nothing about the SMTP or demo paths regresses.

The actual Gmail call lives in `google_service.send_message`, which builds an RFC-822 MIME message (subject, HTML body, attachment), base64url-encodes it, and calls `users.messages.send`. Under `mock_google` it returns a deterministic success without touching the network, so the send path is fully testable.

On the frontend, `EmailDialog.tsx` learns about the new `gmail` mode. A bug is fixed here: the dialog previously branched only on `sent` / `demo` / `error`, so a **successful Gmail send fell through to the error branch and was mislabeled "Could not send."** The result mapping now treats `gmail` as a success state ("Email sent" from Gmail), matching the actual outcome.

## Acceptance criteria
```gherkin
Scenario: Gmail is preferred when Google is connected
  Given a Google account is connected
  When the rep confirms "Send as email" for a ready brief
  Then the message is sent via the Gmail API users.messages.send from the connected account
  And the send result mode is "gmail"
```

```gherkin
Scenario: Falls back to SMTP or demo when Google is not connected
  Given no Google account is connected
  When the rep confirms send
  Then the app uses SMTP if configured, otherwise a demo send
  And the existing send precedence is unchanged
```

```gherkin
Scenario: Gmail success is labeled correctly in the UI (bug fix)
  Given a Google account is connected and the send succeeds with mode "gmail"
  When the result state renders in EmailDialog
  Then it shows a success message
  And it does not mislabel the send as "Could not send"
```

```gherkin
Scenario: Deterministic Gmail send under MOCK_GOOGLE
  Given MOCK_GOOGLE is enabled
  When the send path runs with Google "connected"
  Then google_service.send_message returns a deterministic success with no network call
```

## Technical notes (reference)
- Key files: `backend/app/services/email_service.py`, `backend/app/services/google_service.py`, `frontend/src/components/EmailDialog.tsx`.
- `email_service.send_brief_email`: prefers Gmail when Google is connected, else SMTP, else demo; adds `EmailSendResult.mode = "gmail"`.
- `google_service.send_message`: builds a base64url MIME message and calls Gmail API `users.messages.send`; deterministic under `mock_google`.
- `EmailDialog.tsx`: result mapping treats `gmail` as success (fixes the mislabel-as-error bug).

## Definition of Done
- [x] `send_brief_email` sends via Gmail API when Google is connected, returning `mode = "gmail"`.
- [x] SMTP-then-demo fallback preserved when Google is not connected.
- [x] `google_service.send_message` implemented, with deterministic behaviour under `MOCK_GOOGLE`.
- [x] `EmailDialog` labels a `gmail`-mode send as success (mislabel-as-error bug fixed).
