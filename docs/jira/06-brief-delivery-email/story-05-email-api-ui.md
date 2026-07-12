# SI-6.5 — Email API & EmailDialog UI (preview + send/demo-send)

| Field | Value |
|---|---|
| Issue type | Story |
| Parent epic | SI-6 — Brief Delivery: Web View & Email |
| Status | Done |
| Priority | High |
| Story points | 5 |
| Component | Delivery |
| Labels | backend, frontend, api, ux |

## User story
As a sales rep, I want to review the composed email and confirm sending from a dialog in the brief view, so that I can send the right persona's brief to the right person without leaving the app or guessing what will be delivered.

## Description
This story wires the compose service (SI-6.4) to the UI through two endpoints and a review dialog. The backend adds `GET /meetings/{id}/brief/email/preview`, which composes the persona-tailored email and returns an `EmailPreview` (subject, `body_html` digest, `attachment_filename`, `recipient_default`, and an `email_configured` flag telling the UI whether a real send will occur), and `POST /meetings/{id}/brief/email/send`, which composes and delivers (real or demo) and returns an `EmailSendResult`. Both endpoints resolve the brief for the requested persona and return **409** until that brief is `ready`, so the UI can never email an unfinished brief. Both accept an optional `persona` query param so the email always matches the persona the rep is viewing.

On the frontend, the brief toolbar carries a **per-persona "Send as email" button** that opens the `EmailDialog`. The dialog fetches the preview on open (via TanStack Query), prefills the **To** field from `recipient_default`, shows the composed **subject**, renders the digest **body_html inside an iframe preview**, and shows an **attachment chip** with the full-brief filename. When the backend is not configured for real sending, the dialog shows a clear "demo mode" notice and the primary button reads "Confirm send" instead of "Send email."

Confirming triggers the send mutation and swaps the dialog into a result state that reflects the returned `mode`: "Email sent" (`sent`), "Demo send complete" (`demo`), or "Could not send" (`error`), each with the backend's human-readable message. A backend/network failure of the request itself is surfaced separately as a friendly inline error, so the rep always gets actionable feedback rather than a dead dialog.

## Acceptance criteria
```gherkin
Scenario: Preview loads and prefills the dialog
  Given the rep opens "Send as email" for a ready brief
  When the dialog opens
  Then it fetches the email preview for the viewed persona
  And prefills the To field from recipient_default
  And shows the subject, an iframe preview of the digest, and the attachment chip
```

```gherkin
Scenario: Confirm send in demo mode
  Given the backend reports email is not configured for real sending
  When the rep confirms send
  Then the primary button reads "Confirm send"
  And the result state shows "Demo send complete" with the backend message
```

```gherkin
Scenario: Send is blocked until the brief is ready
  Given the persona's brief is not yet ready
  When the preview or send endpoint is called
  Then the API responds with HTTP 409
```

```gherkin
Scenario: Backend unreachable on send (edge case)
  Given the rep confirms send
  When the request to the backend fails
  Then the dialog shows a friendly "Could not reach the backend" error
  And the dialog remains usable
```

## Technical notes (reference)
- Key files: `backend/app/api/briefs.py`, `frontend/src/components/EmailDialog.tsx`, `frontend/src/api/client.ts`, `frontend/src/api/types.ts`, `frontend/src/pages/BriefView.tsx`.
- API: `_ready_brief_content` raises 409 unless the persona's brief `status == "ready"`; `preview` sets `email_configured = settings.email_configured and not settings.mock_email`; `send` delegates to `email_service.send_brief_email`.
- Client methods `getBriefEmailPreview(id, persona)` / `sendBriefEmail(id, recipient, persona)` append `?persona=`; `EmailDialog` uses TanStack Query for preview and a mutation for send, renders `body_html` via iframe `srcDoc`, and branches result UI on `result.mode` (`sent`/`demo`/`error`).

## Definition of Done
- [x] `GET .../brief/email/preview` and `POST .../brief/email/send` implemented, persona-aware, returning the correct DTOs.
- [x] Both endpoints return 409 until the persona's brief is ready.
- [x] Per-persona "Send as email" button opens the `EmailDialog` from the brief toolbar.
- [x] Dialog previews subject + digest (iframe) + attachment chip, prefills recipient, and shows a demo-mode notice when applicable.
- [x] Result state distinguishes sent / demo / error and surfaces request failures gracefully.
