# Continuous deploy — GitHub Actions → GCP VM

`.github/workflows/deploy.yml` redeploys the app to the Always-Free VM **on every push
to `main`** (i.e. whenever a PR merges). It builds the frontend on the runner and ships
to the VM over the **IAP tunnel**, so SSH stays closed to the internet — the same steps as
[`README.md`](./README.md), automated.

```
PR merged → push to main → GitHub Actions runner:
  npm ci && npm run build         (dist built on the runner, not the 1 GB VM)
  auth to GCP (service-account key)
  gcloud scp  backend docs deploy dist  → VM  (IAP tunnel)
  gcloud ssh  → rsync into /opt/salesintel → deploy/deploy.sh → restart
  curl https://<host>/api/health   (fails the job if unhealthy)
```

> **Auth method:** this uses a **service-account JSON key** stored as a GitHub secret —
> the simplest setup. It's a long-lived credential; for anything beyond a short-lived POC,
> switch to keyless Workload Identity Federation and **delete this key** (see the last
> section). Rotate or delete the key when you're done with the demo.

---

## One-time setup (🔴 you — run once)

You need the `gcloud` CLI authenticated as the project owner
(`indrani.patra.projects@gmail.com`). Paste these as-is; values are pre-filled for the live
project. On Windows, run them from Git Bash using the full gcloud path if it's not on PATH
(`"/c/Users/indra/AppData/Local/Google/Cloud SDK/google-cloud-sdk/bin/gcloud"`).

### 1. Create the deployer service account + grant it deploy permissions

```bash
PROJECT=salesintel-vm-08011625
gcloud config set project "$PROJECT"

gcloud iam service-accounts create github-deployer \
  --display-name="GitHub Actions deployer"

SA_EMAIL="github-deployer@${PROJECT}.iam.gserviceaccount.com"

# Manage the instance (push the runner's ephemeral SSH key to instance metadata)…
gcloud projects add-iam-policy-binding "$PROJECT" \
  --member="serviceAccount:${SA_EMAIL}" \
  --role="roles/compute.instanceAdmin.v1"

# …and reach it through the IAP tunnel (no public SSH).
gcloud projects add-iam-policy-binding "$PROJECT" \
  --member="serviceAccount:${SA_EMAIL}" \
  --role="roles/iap.tunnelResourceAccessor"
```

### 2. Create a JSON key (this is the GitHub secret)

```bash
gcloud iam service-accounts keys create gha-deployer-key.json \
  --iam-account="$SA_EMAIL"
```

This writes `gha-deployer-key.json` to the current folder. You'll paste its **entire
contents** into GitHub in the next step, then **delete the local file**.

### 3. Add the secret + variables in GitHub

Repo → **Settings → Secrets and variables → Actions**:

**Secrets** (tab "Secrets") → *New repository secret*:

| Name | Value |
|---|---|
| `GCP_SA_KEY` | the full contents of `gha-deployer-key.json` |

**Variables** (tab "Variables") → *New repository variable* (these aren't secret):

| Name | Value |
|---|---|
| `GCP_PROJECT` | `salesintel-vm-08011625` |
| `GCP_ZONE` | `us-central1-a` |
| `VM_NAME` | `salesintel-vm` |
| `SITE_HOST` | `salesintel-ai.duckdns.org` |

### 4. Delete the local key file

```bash
rm gha-deployer-key.json
```

The only copy now lives in the GitHub secret. **Never commit the key** — `.gitignore`
already blocks `*-key.json` / `gha-*.json` (added with this workflow).

---

## Using it

- **Automatic:** merge any PR into `main` → the **Deploy to VM** workflow runs → the live
  site updates in ~2–3 min. Watch it under the repo's **Actions** tab.
- **Manual:** Actions → **Deploy to VM** → **Run workflow** (the `workflow_dispatch`
  trigger) to redeploy `main` without a new commit.
- **Safety:** a `concurrency` group serializes deploys (no two at once), and the job
  **fails** if `https://<host>/api/health` doesn't return OK afterward.

The database (`/var/lib/salesintel/salesintel.db`), the on-VM Python venv, and the research
cache (`backend/.cache/`) are all preserved across deploys — the rsync excludes them and the
DB lives outside the deploy dir.

---

## Troubleshooting the first run

- **`sudo: a password is required` / permission denied on the VM.** The runner connects as
  an SSH user derived from the service account; on the standard GCP Ubuntu image, keys added
  via instance metadata get passwordless sudo automatically, so this usually just works. If
  it doesn't, enable OS Login and grant the SA the admin-login role (which carries sudo):
  ```bash
  gcloud compute instances add-metadata salesintel-vm --zone us-central1-a \
    --metadata enable-oslogin=TRUE
  gcloud projects add-iam-policy-binding "$PROJECT" \
    --member="serviceAccount:${SA_EMAIL}" --role="roles/compute.osAdminLogin"
  ```
  (Note: enabling OS Login switches the VM off metadata SSH keys — your own
  `gcloud compute ssh` keeps working as long as your account has the `osAdminLogin` role.)
- **`Permission denied` reaching the tunnel.** Confirm the IAP firewall rule allows
  `35.235.240.0/20` on TCP 22 (it already exists — that's how your own SSH works) and that
  the SA has `roles/iap.tunnelResourceAccessor`.
- **Health check fails but deploy succeeded.** Give it a few seconds (Caddy/uvicorn restart),
  or check `journalctl -u salesintel -n 100 --no-pager` on the VM.

---

## Tearing it down / upgrading later

When the demo's done (or to remove the standing credential):

```bash
# delete the key(s) so the credential can't be used
gcloud iam service-accounts keys list --iam-account="$SA_EMAIL"
gcloud iam service-accounts delete "$SA_EMAIL"   # removes the SA and its keys
```

Then remove the `GCP_SA_KEY` secret in GitHub. To keep auto-deploy without a stored key,
re-do auth with **Workload Identity Federation** (`google-github-actions/auth` with
`workload_identity_provider` instead of `credentials_json`) — no key material in GitHub.
