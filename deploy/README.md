# Deploying SalesIntel AI to a free GCP Always-Free VM

This folder hosts the app on a **GCP Compute Engine `e2-micro` (Always Free)** VM behind
**Caddy** (automatic HTTPS). One host, one URL, same-origin: Caddy serves the built React
app and reverse-proxies `/api/*` to `uvicorn` on `127.0.0.1:8000`.

```
Internet ──HTTPS──> Caddy :443 ──> static SPA (/var/www/salesintel)
                              └──> /api/* ──> uvicorn 127.0.0.1:8000  (systemd: salesintel.service)
                                              └── FastAPI + SQLite (WAL) + calendar-sync & reminder daemons
```

Everything here is **free-tier** and keeps the app's architecture intact (the background
daemons and the SQLite file both need an always-on box with a real disk — which rules out
serverless/spin-down free tiers).

## Files
| File | Purpose |
|---|---|
| `bootstrap.sh` | One-time VM setup: system deps, `salesintel` user, data dirs, Caddy, auto-updates. |
| `deploy.sh` | Repeatable deploy: venv + deps, publish frontend, install unit + Caddyfile, restart. |
| `salesintel.service` | systemd unit — uvicorn as non-root, localhost-only, restart-on-failure. |
| `Caddyfile` | Static SPA + `/api/*` reverse proxy; `__SITE_HOST__` is rendered by `deploy.sh`. |
| `env.production.example` | Template for `/etc/salesintel/env` (real secrets; never committed). |
| `backup.sh` | Daily tarball of the DB (+ WAL sidecars) and prepared research cache. |
| `GITHUB_ACTIONS.md` | Continuous deploy: auto-redeploy on merge to `main` via GitHub Actions + IAP. |

## What lives where on the VM
- Code payload: `/opt/salesintel/` (`backend/`, `docs/`, `frontend/dist/`, `backend/.cache/`)
- Database: `/var/lib/salesintel/salesintel.db` (+ `-wal` / `-shm`) — persistent, outside the deploy dir
- Static site: `/var/www/salesintel/`
- Secrets: `/etc/salesintel/env` (chmod 600, owned by `salesintel`)

---

## First-time deploy

Prereqs done by the operator ahead of these steps: a GCP project with billing, the VM
created (`e2-micro`, Ubuntu, region `us-central1`), a DuckDNS host pointed at the static
IP, and the OAuth redirect URI `https://<host>/api/auth/google/callback` registered.

```bash
# 0. Set your host once (used below)
HOST=salesintel-you.duckdns.org

# 1. Build the frontend LOCALLY (keeps the 1 GB VM out of a memory-hungry npm build)
#    (from repo root on your machine)
cd frontend && npm ci && npm run build   # emits frontend/dist/ with VITE_API_URL=/api
cd ..

# 2. Upload the payload to the VM (via gcloud IAP; run from your machine).
#    Excludes venv/node_modules/.git; INCLUDES backend/.cache (git-ignored research data).
gcloud compute scp --recurse --tunnel-through-iap \
  backend docs deploy frontend/dist salesintel-vm:/tmp/payload/ --zone us-central1-a
# then on the VM, place it:
gcloud compute ssh salesintel-vm --tunnel-through-iap --zone us-central1-a --command '
  sudo mkdir -p /opt/salesintel/frontend &&
  sudo cp -r /tmp/payload/backend /tmp/payload/docs /tmp/payload/deploy /opt/salesintel/ &&
  sudo cp -r /tmp/payload/dist /opt/salesintel/frontend/dist &&
  rm -rf /tmp/payload'

# 3. One-time bootstrap (installs Caddy, user, dirs, auto-updates)
gcloud compute ssh salesintel-vm --tunnel-through-iap --zone us-central1-a \
  --command 'sudo bash /opt/salesintel/deploy/bootstrap.sh'

# 4. Create the env file from the template, fill secrets from local backend/.env,
#    replace __SITE_HOST__ with $HOST, then lock it down:
gcloud compute ssh salesintel-vm --tunnel-through-iap --zone us-central1-a --command "
  sudo cp /opt/salesintel/deploy/env.production.example /etc/salesintel/env &&
  sudo chown salesintel:salesintel /etc/salesintel/env && sudo chmod 600 /etc/salesintel/env &&
  sudo sed -i 's/__SITE_HOST__/$HOST/g' /etc/salesintel/env"
#    ...then edit /etc/salesintel/env to paste the real LLM/Google secrets.

# 5. Deploy (venv, publish, services, HTTPS cert issues automatically)
gcloud compute ssh salesintel-vm --tunnel-through-iap --zone us-central1-a \
  --command "SITE_HOST=$HOST sudo -E bash /opt/salesintel/deploy/deploy.sh"

# 6. Daily backup cron
gcloud compute ssh salesintel-vm --tunnel-through-iap --zone us-central1-a --command '
  ( sudo crontab -l 2>/dev/null; echo "0 3 * * * /opt/salesintel/deploy/backup.sh" ) | sudo crontab -'
```

Verify: `https://<host>/api/health` returns `{"status":"ok"}`, the homepage loads over
HTTPS, and `systemctl status salesintel caddy` are both active. Then connect Google from
the live Settings page (only whitelisted OAuth test users can log in).

## Redeploying after a code change

**Automatic (preferred):** merging a PR into `main` triggers the **Deploy to VM** GitHub
Actions workflow, which runs exactly these steps for you over the IAP tunnel. See
[`GITHUB_ACTIONS.md`](./GITHUB_ACTIONS.md) for the one-time setup and how to trigger a
manual run.

**Manual (fallback):**
```bash
cd frontend && npm run build && cd ..
# re-run step 2 (upload) then:
gcloud compute ssh salesintel-vm --tunnel-through-iap --zone us-central1-a \
  --command "SITE_HOST=$HOST sudo -E bash /opt/salesintel/deploy/deploy.sh"
```
The database is untouched (it lives in `/var/lib/salesintel`, outside the deploy dir).

## Handy checks
```bash
systemctl status salesintel caddy         # services up?
journalctl -u salesintel -n 100 --no-pager   # backend logs
sqlite3 /var/lib/salesintel/salesintel.db 'PRAGMA journal_mode;'   # -> wal
```

## Cost & safety notes
- Stay on `e2-micro` in `us-central1` / `us-west1` / `us-east1` with a ≤30 GB standard
  disk to remain in the Always-Free tier. A `$1` budget alert warns on any drift.
- The reserved static IP is free **while attached to a running VM**. If you ever stop the
  VM for a long time, release the IP or it accrues a few cents.
- OAuth stays in **Testing** mode: only whitelisted Google accounts can log in. Hosting
  gives a permanent URL, not public sign-up.
