# EPIC SI-18 — Free Cloud Hosting on GCP

| Field | Value |
|---|---|
| Issue type | Epic |
| Suggested key | SI-18 |
| Status | Done |
| Priority | High |
| Component | Deployment |
| Labels | deployment, hosting, gcp, infra, security |
| Story points (rollup) | 29 |

## Summary
Host the SalesIntel AI POC **permanently and for free** on a **GCP Compute Engine `e2-micro` "Always Free" VM** (Ubuntu 24.04, `us-central1`) behind **Caddy**, so the demo lives at a stable public URL — **https://salesintel-ai.duckdns.org** — with automatic HTTPS, real persistence, and the background daemons always running. One host, one URL, same-origin: Caddy serves the built React SPA statically and reverse-proxies `/api/*` to `uvicorn` on `127.0.0.1:8000`, so there is **no CORS** and exactly **one clean OAuth redirect domain**. The app's architecture is kept intact on purpose — the calendar-sync and reminder daemons plus the SQLite file both need an always-on box with a real disk, which rules out serverless/spin-down free tiers.

## Description
Until now SalesIntel AI only ran on a developer's `localhost`. This epic gives it a permanent, free home without changing what the app *is*. A single **`e2-micro`** VM in the Always-Free tier runs the whole stack: the **FastAPI backend** under **systemd** (`salesintel.service`) as a non-root `salesintel` user bound to `127.0.0.1` only (never publicly exposed), hosting the two background daemons — the **30-second calendar sync** and the **1-hour-before reminder email**. In front of it, **Caddy** terminates HTTPS on `:443`, serves the built React app from disk, and reverse-proxies `/api/*` to `uvicorn` with the prefix stripped. Because the SPA is built with `frontend/.env.production` → `VITE_API_URL=/api`, the whole app is **same-origin**: no cross-origin requests, no CORS config, and a single redirect domain for Google OAuth.

Two properties make this stick on a 1 GB free-tier box. First, **SQLite runs in WAL mode**: `backend/app/db.py` sets `PRAGMA journal_mode=WAL` + `synchronous=NORMAL` on every sqlite connection (guarded to the sqlite dialect) so the daemons can **write** while the request path **reads** — eliminating "database is locked" with no schema change or migration. Second, the frontend is **built locally** and only the `dist/` bundle is uploaded, so the memory-hungry `npm build` never runs on the VM. The database lives at `/var/lib/salesintel/salesintel.db` (with its `-wal`/`-shm` sidecars) **outside** the deploy dir, so redeploys never clobber it.

A committed **`deploy/` toolkit** makes provisioning and redeploys repeatable: `bootstrap.sh` (system deps, Caddy, the non-root user, data dirs, `unattended-upgrades`), `deploy.sh` (venv + deps, publish frontend, install the systemd unit + rendered Caddyfile, restart), the `salesintel.service` unit, a `Caddyfile` (static SPA + `/api/*` proxy, with `__SITE_HOST__` rendered at deploy time), `env.production.example`, `backup.sh` (daily tarball of the DB + WAL sidecars + research cache), and a `README.md` runbook.

Security is deliberately hardened for a free box: only **80/443** are public; **SSH is closed to the internet** and reachable **only via a Google IAP tunnel** (`gcloud compute ssh --tunnel-through-iap`, firewall source `35.235.240.0/20`); the VM is a **Shielded VM** (secure boot + vTPM + integrity monitoring); secrets live in `/etc/salesintel/env` (chmod 600, owned by the non-root user) and are **never committed** — only `env.production.example` is in git — with a `.gitattributes` rule forcing **LF** on deploy files (a CRLF systemd `EnvironmentFile` would corrupt secret values). OS security updates apply automatically and a **budget alert** guards spend.

DNS and TLS are free too: a **DuckDNS** hostname points at a **reserved static IP**; because the IP is static there is no dynamic-update needed, and **Caddy** obtains and auto-renews the **Let's Encrypt** certificate over HTTP-01. Google OAuth stays in the **original Google Cloud project** (editing redirect URIs/test users is free and needs no billing): the production redirect URI `https://salesintel-ai.duckdns.org/api/auth/google/callback` plus `FRONTEND_URL` / `CORS_ORIGINS` / `GOOGLE_REDIRECT_URI` / `DATABASE_URL` are set as production env overrides, and the consent screen stays in **Testing** mode — hosting gives persistence, not public sign-up, so only whitelisted test users can log in.

The intelligence here is entirely in the *operations seam*: a same-origin production build behind a Caddy reverse proxy (SI-18.1), WAL-mode SQLite for concurrent daemon writes (SI-18.2), a hardened Always-Free VM (SI-18.3), a committed deploy toolkit + systemd service (SI-18.4), DNS + automatic HTTPS + OAuth redirect wiring (SI-18.5), and data durability with daily backups (SI-18.6). Every free-tier choice is intentional and carries a named scale path.

## Stories in this epic
| Key | Story | Points | Priority |
|---|---|---|---|
| SI-18.1 | Same-origin production build + Caddy reverse proxy | 5 | High |
| SI-18.2 | SQLite WAL mode for concurrent daemon writes | 3 | High |
| SI-18.3 | Always-Free VM provisioning + hardened network | 5 | High |
| SI-18.4 | Deploy toolkit + hardened systemd service | 8 | High |
| SI-18.5 | DNS + automatic HTTPS + OAuth redirect wiring | 5 | High |
| SI-18.6 | Data durability & daily backups | 3 | Medium |

## Epic acceptance criteria
```gherkin
Scenario: The app is reachable at a permanent free HTTPS URL
  Given the e2-micro VM is running Caddy and the salesintel service
  When a visitor opens https://salesintel-ai.duckdns.org
  Then the built React SPA loads over HTTPS with a valid Let's Encrypt cert
  And GET /api/health returns {"status":"ok"}
```

```gherkin
Scenario: The app is served same-origin with no CORS
  Given the frontend was built with VITE_API_URL=/api
  When the SPA calls /api/*
  Then Caddy reverse-proxies the request to uvicorn on 127.0.0.1:8000 with the prefix stripped
  And no cross-origin request is made and no CORS handling is needed
```

```gherkin
Scenario: Background daemons write while requests read
  Given SQLite runs with journal_mode=WAL and synchronous=NORMAL
  When the calendar-sync and reminder daemons write while the request path reads
  Then no "database is locked" error occurs
  And no schema change or migration was required
```

```gherkin
Scenario: The backend is never publicly exposed
  Given uvicorn is bound to 127.0.0.1 under systemd as a non-root user
  When the internet tries to reach the backend directly
  Then only ports 80 and 443 are reachable and the backend is not
  And all traffic reaches FastAPI only through Caddy
```

```gherkin
Scenario: SSH is reachable only through the IAP tunnel
  Given SSH is closed to the internet and the firewall allows source 35.235.240.0/20
  When an operator runs gcloud compute ssh --tunnel-through-iap
  Then the connection succeeds through Google IAP
  And a direct SSH attempt from the public internet is refused
```

```gherkin
Scenario: Redeploys never clobber the database
  Given the DB lives at /var/lib/salesintel/salesintel.db outside the deploy dir
  When deploy.sh republishes code and restarts services
  Then the existing database and its -wal/-shm sidecars are untouched
```

```gherkin
Scenario: Secrets stay out of git and uncorrupted
  Given secrets live in /etc/salesintel/env (chmod 600, non-root owner)
  When the repo is inspected
  Then only env.production.example is committed, never the real env
  And .gitattributes forces LF so the systemd EnvironmentFile is not corrupted by CRLF
```

## Out of scope
- **Public sign-up.** The OAuth consent screen stays in **Testing** mode — only whitelisted Google test users can log in. Hosting delivers a permanent URL and persistence, not open registration.
- Migrating off SQLite to Postgres, off DuckDNS to a paid domain, or off the IAP tunnel to a bastion host — all deliberate free-tier choices with named scale paths.
- Horizontal scaling, load balancing, container orchestration, or a CI/CD pipeline (deploys are a scripted `deploy.sh` run).
- Any change to application features — this epic hosts the app as-is; the only code change is the SQLite WAL pragmas in `db.py`.

## Dependencies
- Google Workspace integration (SI-10) — supplies the OAuth client whose production redirect URI and test users are wired here.
- Calendar auto-sync (SI-15) and the 1-hour-before email (SI-16) — the always-on daemons that make an always-on VM (not serverless) the right host.
- The frontend build (`frontend/.env.production`) and `backend/app/db.py`.
- The committed `deploy/` toolkit (`bootstrap.sh`, `deploy.sh`, `salesintel.service`, `Caddyfile`, `env.production.example`, `backup.sh`, `README.md`).

## Deliberate free-tier choices (intentional — each with a scale path)
- **SQLite on a persistent disk** (not Postgres) — WAL mode makes concurrent daemon writes safe; the scale path is Cloud SQL / Postgres if concurrency grows.
- **A single `e2-micro` (1 GB RAM)** — the frontend is built locally and only `dist/` is uploaded, so the box never runs a memory-hungry `npm build`; if load grows, the `$300` free trial can bump the VM to `e2-small` temporarily.
- **DuckDNS** (not a paid domain) — a free hostname on a reserved static IP; the scale path is a purchased domain.
- **Google IAP tunnel** (no bastion) — SSH stays closed to the internet with no extra host to run or pay for.

## Verification
- **Live URL** — `https://salesintel-ai.duckdns.org` loads the SPA over HTTPS; `GET /api/health` returns `{"status":"ok"}`; `systemctl status salesintel caddy` are both active.
- **WAL confirmed** — `sqlite3 /var/lib/salesintel/salesintel.db 'PRAGMA journal_mode;'` returns `wal`; no "database is locked" under concurrent daemon writes.
- **Same-origin** — the SPA calls `/api/*` and Caddy proxies to `127.0.0.1:8000`; no CORS involved; one OAuth redirect domain.
- **Security posture** — only 80/443 public; direct SSH refused, IAP SSH succeeds; Shielded VM enabled; `/etc/salesintel/env` is `600` and uncommitted; budget alert active.
- Shipped as **PR #21** (branch `feat/gcp-deploy`).
