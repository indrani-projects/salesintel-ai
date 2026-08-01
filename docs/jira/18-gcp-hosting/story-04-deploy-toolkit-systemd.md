# SI-18.4 — Deploy toolkit + hardened systemd service

| Field | Value |
|---|---|
| Issue type | Story |
| Parent epic | SI-18 — Free Cloud Hosting on GCP |
| Status | Done |
| Priority | High |
| Story points | 8 |
| Component | Deployment |
| Labels | deployment, systemd, caddy, security, tooling |

## User story
As the operator, I want a **committed, repeatable deploy toolkit** and a **hardened systemd service**, so that provisioning and redeploys are one scripted run and the backend runs as an unprivileged, localhost-only process.

## Description
The `deploy/` folder is a committed toolkit that provisions the VM and ships the app repeatably:

- **`bootstrap.sh`** — one-time VM setup: system deps, **Caddy**, the non-root **`salesintel`** user, the data directories (`/var/lib/salesintel`, `/var/www/salesintel`, `/etc/salesintel`), and **`unattended-upgrades`** for automatic OS security updates.
- **`deploy.sh`** — repeatable deploy: builds the Python **venv + deps**, publishes the frontend (`dist/` → `/var/www/salesintel`), installs the **systemd unit** and the **rendered Caddyfile** (`__SITE_HOST__` → real host), and restarts the services.
- **`salesintel.service`** — the systemd unit that runs **uvicorn as the non-root `salesintel` user, bound to `127.0.0.1` only** (never publicly exposed), with restart-on-failure. The two background daemons live inside this one process.
- **`Caddyfile`**, **`env.production.example`**, **`backup.sh`** (see SI-18.1, SI-18.5, SI-18.6), and a **`README.md`** runbook.

Because the box has only 1 GB RAM, the frontend is **built locally** and only the `dist/` bundle is uploaded — the VM never runs a memory-hungry `npm build`. Secrets live in **`/etc/salesintel/env`** (chmod **600**, owned by the non-root user) and are **never committed** (only `env.production.example` is in git); a **`.gitattributes`** rule forces **LF** on the deploy files because a **CRLF** systemd `EnvironmentFile` would corrupt secret values. The database sits at `/var/lib/salesintel/` **outside** the deploy dir so redeploys never touch it.

## Acceptance criteria
```gherkin
Scenario: bootstrap prepares the VM once
  Given a fresh e2-micro VM
  When bootstrap.sh runs
  Then it installs system deps, Caddy, the non-root salesintel user, the data dirs, and unattended-upgrades
```

```gherkin
Scenario: deploy publishes the app repeatably
  Given the payload is on the VM
  When deploy.sh runs
  Then it builds the venv + deps, publishes the frontend dist, installs the systemd unit and rendered Caddyfile, and restarts the services
```

```gherkin
Scenario: The backend runs unprivileged and localhost-only
  Given salesintel.service is installed
  When the service starts
  Then uvicorn runs as the non-root salesintel user bound to 127.0.0.1
  And it restarts on failure
  And the calendar-sync and reminder daemons run inside that process
```

```gherkin
Scenario: The VM never runs a memory-hungry build
  Given the frontend is built locally
  When the payload is uploaded
  Then only the dist/ bundle is shipped and the VM never runs npm build
```

```gherkin
Scenario: Secrets are protected and LF-normalized
  Given secrets live in /etc/salesintel/env
  When the file is inspected
  Then it is chmod 600, owned by the non-root user, and uncommitted (only env.production.example is in git)
  And .gitattributes forces LF so the EnvironmentFile is not corrupted by CRLF
```

## Technical notes (reference)
- Toolkit: `deploy/bootstrap.sh`, `deploy/deploy.sh`, `deploy/salesintel.service`, `deploy/Caddyfile`, `deploy/env.production.example`, `deploy/backup.sh`, `deploy/README.md`.
- Service: uvicorn as non-root `salesintel`, bound to `127.0.0.1`, restart-on-failure; hosts the 30s calendar-sync + 1-hour-before reminder daemons.
- Layout on VM: code `/opt/salesintel/`, static `/var/www/salesintel/`, DB `/var/lib/salesintel/` (outside deploy dir), secrets `/etc/salesintel/env`.
- 1 GB box: frontend built locally; only `dist/` uploaded.
- `.gitattributes` forces LF on deploy files (CRLF `EnvironmentFile` corrupts secrets).

## Definition of Done
- [x] `bootstrap.sh` installs system deps, Caddy, the non-root user, data dirs, and `unattended-upgrades`.
- [x] `deploy.sh` builds the venv, publishes the frontend, installs the systemd unit + rendered Caddyfile, and restarts services.
- [x] `salesintel.service` runs uvicorn as non-root, bound to `127.0.0.1`, with restart-on-failure.
- [x] The frontend is built locally; only `dist/` is uploaded (the VM never runs `npm build`).
- [x] Secrets live in `/etc/salesintel/env` (600, non-root owner) and are uncommitted; only `env.production.example` is in git.
- [x] `.gitattributes` forces LF on deploy files so a CRLF `EnvironmentFile` cannot corrupt secrets.
