# EPIC SI-10 — Google Workspace Integration (Gmail send + Calendar, one OAuth)

| Field | Value |
|---|---|
| Issue type | Epic |
| Suggested key | SI-10 |
| Status | Done |
| Priority | High |
| Component | Integrations |
| Labels | frontend, backend, api, integrations, oauth, google |
| Story points (rollup) | 21 |

## Summary
Connect one Google account with a single OAuth consent and use it for two capabilities — sending brief emails from the rep's own Gmail, and two-way Google Calendar sync — all gated by a `mock_google` flag for deterministic tests.

## Description
SalesIntel AI already delivers a finished brief on screen and by email, and it already lets a rep add meetings on a calendar. This epic closes the loop with the rep's real Google Workspace: **one consent, two capabilities.** A single Google OAuth connection grants the scopes needed to (1) send the persona-tailored brief email from the rep's **own Gmail** — so it lands in the recipient's inbox as a genuine message from the rep, threaded and in "Sent" — and (2) keep the app's calendar and the rep's **Google Calendar** in sync both ways.

The connection is deliberately **single-user** for the POC: exactly one Google account is connected at a time, stored as a single-row `GoogleToken` table (access token, refresh token, expiry, granted scopes, and the connected email). This keeps the auth surface tiny and demoable without a full multi-tenant identity system, while still exercising the real OAuth authorization-code exchange, token refresh, and scope handling.

Every Google API call in the codebase is routed behind a `mock_google` flag, mirroring the `mock_llm` / `mock_email` pattern used elsewhere. With `MOCK_GOOGLE` on, the status endpoint, Gmail send, and calendar sync return deterministic canned results so pytest, `npm build`, and Playwright can run hermetically with no credentials and no network. With it off and real client credentials configured, the identical code paths hit live Google.

On the send side, `email_service.send_brief_email` gains a new preferred transport: when Google is connected it sends via the **Gmail API** (`users.messages.send`) and returns `mode = "gmail"`; otherwise it falls back to SMTP, and finally to demo-send — the existing precedence is preserved, Gmail simply sits at the top. On the calendar side, a sync endpoint pulls upcoming primary-calendar events, turns the ones that match a known prospect into meetings + briefs (deduped by `google_event_id` so re-sync is idempotent), and pushes app-created meetings back **out** to Google Calendar on a best-effort basis that never breaks meeting creation.

A new **Settings** page surfaces the whole thing: Connect Google, live connection status (connected email + scopes), Sync calendar now, and Disconnect — plus a Sync Google button on the Calendar page.

### Notable gotcha (documented)
The OAuth login and callback are **separate stateless requests**, so the Google client library's auto-generated PKCE `code_verifier` created during login could not survive to the token exchange in the callback, producing `invalid_grant: Missing code verifier`. The fix was to **disable PKCE** (`flow.autogenerate_code_verifier = False`) for this server-side authorization-code flow. Setup is documented in `docs/RUNBOOK.md` §2c.

## Stories in this epic
| Key | Story | Points | Priority |
|---|---|---|---|
| SI-10.1 | Google OAuth foundation (one consent, token store, auth router) | 8 | Highest |
| SI-10.2 | Send brief email from the rep's Gmail | 3 | High |
| SI-10.3 | Two-way Google Calendar sync | 8 | High |
| SI-10.4 | Settings page & Calendar sync UI | 2 | Medium |

## Epic acceptance criteria
```gherkin
Scenario: One consent grants both capabilities
  Given Google client credentials are configured
  When the rep completes the Google consent screen once
  Then the app stores a single token with the gmail.send and calendar.events scopes
  And both Gmail send and Calendar sync become available without a second consent
```

```gherkin
Scenario: Brief email is sent from the rep's own Gmail
  Given a Google account is connected
  When the rep confirms "Send as email" for a ready brief
  Then the message is delivered via the Gmail API from the connected account
  And the send result reports mode "gmail"
```

```gherkin
Scenario: Calendar sync imports a prospect meeting both idempotently
  Given a Google account is connected
  And the primary calendar has an event "Discovery call with Sleep Company"
  When the rep runs Sync calendar now
  Then a meeting + brief is created for "The Sleep Company"
  And running the sync again creates no duplicate, matched by google_event_id
```

```gherkin
Scenario: Deterministic behaviour under MOCK_GOOGLE
  Given MOCK_GOOGLE is enabled
  When status, Gmail send, and calendar sync run
  Then each returns a deterministic canned result with no network call
```

## Verification
- pytest, `npm run build`, and Playwright E2E all green under `MOCK_GOOGLE`.
- Live OAuth verified end-to-end for a connected account: a real Gmail send delivered from the rep's inbox, and a real Google Calendar event imported into the app.

## Out of scope
- Multi-user / multi-tenant Google identity (single connected account by design).
- Google Contacts, Drive, Meet, or any scope beyond `gmail.send` + `calendar.events` + `openid` + `userinfo.email`.
- Full RFC-5545 recurring-event expansion or attendee/RSVP round-tripping.
- Server-side background polling of the calendar (sync is user-triggered).

## Dependencies
- Brief Delivery epic (SI-6) — provides `email_service.send_brief_email` and the EmailDialog this epic extends.
- Calendar & Meeting Management epic (SI-2) — provides `build_meeting_with_briefs` and the Calendar page reused here.
- Shared contract files `schemas.py` / `frontend/src/api/types.ts` (DTO shapes for `GoogleStatus` and `CalendarSyncResult`).
