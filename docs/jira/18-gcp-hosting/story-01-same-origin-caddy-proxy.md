# SI-18.1 — Same-origin production build + Caddy reverse proxy

| Field | Value |
|---|---|
| Issue type | Story |
| Parent epic | SI-18 — Free Cloud Hosting on GCP |
| Status | Done |
| Priority | High |
| Story points | 5 |
| Component | Deployment |
| Labels | deployment, frontend, caddy, oauth |

## User story
As the operator hosting the demo, I want the React SPA and the FastAPI backend served from **one host on one URL**, so that there is no CORS to configure and exactly one clean OAuth redirect domain.

## Description
The frontend is built for production with `frontend/.env.production` set to **`VITE_API_URL=/api`**, so every API call the SPA makes is a **same-origin** relative request rather than a cross-origin call to `localhost:8000`. **Caddy** is the single public entrypoint: it terminates HTTPS on `:443`, serves the built React app statically from `/var/www/salesintel/`, and **reverse-proxies `/api/*`** to `uvicorn` on `127.0.0.1:8000` with the `/api` prefix stripped so FastAPI sees its normal routes. A SPA fallback serves `index.html` for client-side routes.

Because everything is same-origin, there is **no CORS** to configure and **one clean OAuth redirect domain** — the production redirect URI is simply `https://salesintel-ai.duckdns.org/api/auth/google/callback`. The `Caddyfile` carries a `__SITE_HOST__` placeholder that `deploy.sh` renders to the real host at deploy time.

## Acceptance criteria
```gherkin
Scenario: The SPA calls the API same-origin
  Given the frontend was built with VITE_API_URL=/api
  When the app issues an API request
  Then the request goes to /api/* on the same origin
  And no cross-origin request is made
```

```gherkin
Scenario: Caddy proxies /api to uvicorn with the prefix stripped
  Given a request arrives at https://<host>/api/health
  When Caddy handles it
  Then it is reverse-proxied to uvicorn on 127.0.0.1:8000 as /health
  And it returns {"status":"ok"}
```

```gherkin
Scenario: Client-side routes are served by the SPA
  Given a deep-link to a client-side route
  When the browser requests it
  Then Caddy serves the SPA index.html and React Router renders the route
```

```gherkin
Scenario: One clean OAuth redirect domain
  Given the app is same-origin behind Caddy
  When Google OAuth redirects back
  Then it uses the single domain https://salesintel-ai.duckdns.org/api/auth/google/callback
  And no CORS handling is required
```

## Technical notes (reference)
- Build config: `frontend/.env.production` → `VITE_API_URL=/api`; only the built `dist/` is published (see SI-18.4 for the local-build rationale).
- Proxy: `deploy/Caddyfile` — static file server for the SPA + `handle /api/*` reverse proxy to `127.0.0.1:8000` with the prefix stripped; `__SITE_HOST__` rendered by `deploy.sh`.
- Result: no CORS; a single OAuth redirect domain (`.../api/auth/google/callback`).

## Definition of Done
- [x] `frontend/.env.production` sets `VITE_API_URL=/api` so the SPA calls the API same-origin.
- [x] `Caddyfile` serves the static SPA and reverse-proxies `/api/*` to `uvicorn` on `127.0.0.1:8000` with the prefix stripped.
- [x] Client-side routes fall back to `index.html`.
- [x] No CORS configuration is needed; one clean OAuth redirect domain is used.
- [x] `__SITE_HOST__` in the `Caddyfile` is rendered by `deploy.sh` at deploy time.
