# SI-18.5 — DNS + automatic HTTPS + OAuth redirect wiring

| Field | Value |
|---|---|
| Issue type | Story |
| Parent epic | SI-18 — Free Cloud Hosting on GCP |
| Status | Done |
| Priority | High |
| Story points | 5 |
| Component | Deployment |
| Labels | deployment, dns, https, oauth, caddy |

## User story
As the operator, I want a **free hostname with automatic HTTPS** and the **production OAuth redirect wired up**, so that the demo has a stable secure URL and whitelisted users can sign in with Google.

## Description
DNS is free: a **DuckDNS** hostname (`salesintel-ai.duckdns.org`) points at the VM's **reserved static IP**. Because the IP is static there is **no dynamic-update client** to run. **Caddy** obtains and **auto-renews** the **Let's Encrypt** certificate over the **HTTP-01** challenge (which is why port 80 stays open), so HTTPS is fully automatic with no manual cert handling.

Google OAuth is wired for production **without incurring billing**: the OAuth client stays in the **original Google Cloud project** (editing its redirect URIs and test users is free). The production **redirect URI** `https://salesintel-ai.duckdns.org/api/auth/google/callback` is registered, and the production env sets `FRONTEND_URL`, `CORS_ORIGINS`, `GOOGLE_REDIRECT_URI`, and `DATABASE_URL` as overrides. The consent screen stays in **Testing** mode, so **only whitelisted test users** can log in — hosting gives persistence and a permanent URL, **not public sign-up**.

## Acceptance criteria
```gherkin
Scenario: A free hostname resolves to the static IP
  Given a DuckDNS host pointed at the reserved static IP
  When the hostname is resolved
  Then it returns the VM's static IP
  And no dynamic-update client is needed because the IP is static
```

```gherkin
Scenario: HTTPS is obtained and renewed automatically
  Given Caddy is fronting the app on ports 80 and 443
  When the app is first served
  Then Caddy obtains a Let's Encrypt cert over HTTP-01
  And it auto-renews the cert without manual intervention
```

```gherkin
Scenario: The production OAuth redirect is wired
  Given the OAuth client stays in the original Google Cloud project
  When production env is set
  Then the redirect URI https://salesintel-ai.duckdns.org/api/auth/google/callback is registered
  And FRONTEND_URL, CORS_ORIGINS, GOOGLE_REDIRECT_URI, and DATABASE_URL are set as production overrides
```

```gherkin
Scenario: Only whitelisted test users can log in
  Given the OAuth consent screen stays in Testing mode
  When a non-whitelisted Google account tries to sign in
  Then it is rejected
  And a whitelisted test user can sign in successfully
```

## Technical notes (reference)
- DNS: **DuckDNS** host `salesintel-ai.duckdns.org` → reserved static IP; no dynamic-update client (IP is static).
- TLS: **Caddy** auto-obtains + auto-renews a **Let's Encrypt** cert via **HTTP-01** (port 80 kept open for the challenge).
- OAuth: client stays in the original GCP project (free to edit redirect URIs/test users); prod redirect `.../api/auth/google/callback`; prod overrides for `FRONTEND_URL` / `CORS_ORIGINS` / `GOOGLE_REDIRECT_URI` / `DATABASE_URL`.
- Consent screen stays **Testing** — persistence, not public sign-up.

## Definition of Done
- [x] A free DuckDNS host points at the reserved static IP with no dynamic-update client.
- [x] Caddy obtains and auto-renews the Let's Encrypt cert over HTTP-01.
- [x] The production redirect URI `https://salesintel-ai.duckdns.org/api/auth/google/callback` is registered.
- [x] `FRONTEND_URL`, `CORS_ORIGINS`, `GOOGLE_REDIRECT_URI`, and `DATABASE_URL` are set as production overrides.
- [x] The OAuth consent screen stays in Testing mode; only whitelisted test users can log in.
