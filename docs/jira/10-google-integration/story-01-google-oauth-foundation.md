# SI-10.1 — Google OAuth foundation (one consent, token store, auth router)

| Field | Value |
|---|---|
| Issue type | Story |
| Parent epic | SI-10 — Google Workspace Integration |
| Status | Done |
| Priority | Highest |
| Story points | 8 |
| Component | Integrations |
| Labels | backend, api, oauth, google, security |

## User story
As a sales rep, I want to connect my Google account once with a single consent, so that the app can send email from my Gmail and sync my calendar without me authorizing each capability separately.

## Description
This story is the authentication backbone for the whole epic. It implements a single Google OAuth authorization-code flow whose one consent screen covers every scope the epic needs: `gmail.send`, `calendar.events`, `openid`, and `userinfo.email`. The result is stored so both Gmail send (SI-10.2) and Calendar sync (SI-10.3) work off the same token with no further prompts.

New settings are added in `config.py`: `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`, `GOOGLE_REDIRECT_URI`, `FRONTEND_URL` (where the callback redirects back to), and `mock_google`. A derived `google_configured` property reports whether real client credentials are present, so the rest of the app (and the UI) can branch cleanly between real and mock behaviour.

Token persistence is a single-row `GoogleToken` SQLModel table holding the access token, refresh token, expiry, the granted scopes, and the connected account's email — deliberately one row because the POC connects exactly one account.

A new router `backend/app/api/google.py` (mounted in `main.py`) exposes:
- `GET /auth/google/login` — builds the consent URL and returns a **302 redirect** to Google.
- `GET /auth/google/callback` — exchanges the authorization `code` for tokens, stores the `GoogleToken`, and redirects the browser back to `${FRONTEND_URL}/settings?google=connected` (or `?google=error` on failure).
- `GET /integrations/google/status` — reports whether an account is connected, with the connected email and scopes.
- `DELETE /integrations/google/disconnect` — clears the stored token.

The Google-specific work (building the flow, exchanging the code, refreshing tokens, reading userinfo) lives in `backend/app/services/google_service.py`, built on the `google-auth` libraries. Under `mock_google` the service short-circuits to deterministic values so nothing hits the network.

### Gotcha fixed — PKCE disabled
Because `login` and `callback` are **separate stateless HTTP requests**, the PKCE `code_verifier` that the client library auto-generates during `login` did not survive to the token exchange in `callback`, so Google rejected the exchange with `invalid_grant: Missing code verifier`. The fix is to **disable PKCE for this server-side flow** by setting `flow.autogenerate_code_verifier = False`. Setup steps (creating the OAuth client, redirect URI, test-user allow-list) are documented in `docs/RUNBOOK.md` §2c.

## Acceptance criteria
```gherkin
Scenario: One consent covers all required scopes
  Given Google client credentials are configured
  When the rep hits GET /auth/google/login
  Then they are 302-redirected to the Google consent screen
  And the requested scopes include gmail.send, calendar.events, openid, and userinfo.email
```

```gherkin
Scenario: Callback exchanges the code and stores one token
  Given the rep approves the consent screen
  When Google redirects to GET /auth/google/callback with a code
  Then the code is exchanged for access and refresh tokens
  And a single GoogleToken row is stored with the scopes and connected email
  And the browser is redirected to /settings?google=connected
```

```gherkin
Scenario: Callback failure redirects with an error flag
  Given the token exchange fails
  When the callback runs
  Then the browser is redirected to /settings?google=error
  And no crash is surfaced to the user
```

```gherkin
Scenario: Status and disconnect reflect the connection
  Given an account is connected
  When GET /integrations/google/status is called
  Then it reports connected true with the email and scopes
  And DELETE /integrations/google/disconnect clears the token so status reports connected false
```

```gherkin
Scenario: PKCE is disabled so the exchange succeeds
  Given login and callback are separate stateless requests
  When the authorization-code exchange runs
  Then the flow does not require an auto-generated code_verifier
  And the exchange does not fail with "Missing code verifier"
```

## Technical notes (reference)
- Key files: `backend/app/services/google_service.py`, `backend/app/api/google.py`, `backend/app/config.py`, `backend/app/models.py`, `backend/app/main.py`, `backend/.env.example`.
- `config.py`: adds `GOOGLE_CLIENT_ID` / `GOOGLE_CLIENT_SECRET` / `GOOGLE_REDIRECT_URI` / `FRONTEND_URL` / `mock_google`, plus a `google_configured` property.
- `models.py`: `GoogleToken` single-row SQLModel table — access token, refresh token, expiry, scopes, email.
- `google_service.py`: builds the OAuth flow with `flow.autogenerate_code_verifier = False` (PKCE disabled), exchanges the code, refreshes tokens, and reads userinfo; short-circuits under `mock_google`.
- `api/google.py`: `GET /auth/google/login` (302), `GET /auth/google/callback` (exchange → store → redirect to `${FRONTEND_URL}/settings?google=connected|error`), `GET /integrations/google/status`, `DELETE /integrations/google/disconnect`; router mounted in `main.py`.
- Setup documented in `docs/RUNBOOK.md` §2c.

## Definition of Done
- [x] Single consent requests `gmail.send`, `calendar.events`, `openid`, `userinfo.email`.
- [x] `GoogleToken` single-row table persists access/refresh token, expiry, scopes, and email.
- [x] `login` 302-redirects to Google; `callback` exchanges the code, stores the token, and redirects to `/settings?google=connected|error`.
- [x] `status` and `disconnect` endpoints implemented and consistent with stored state.
- [x] PKCE disabled (`autogenerate_code_verifier = False`); exchange no longer fails with "Missing code verifier".
- [x] `google_configured` property and `mock_google` flag added; service is deterministic under `MOCK_GOOGLE`.
- [x] Setup documented in `docs/RUNBOOK.md` §2c and `backend/.env.example` updated.
