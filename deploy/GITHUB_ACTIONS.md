# Continuous deploy — GitHub Actions → GCP VM

`.github/workflows/deploy.yml` redeploys the app to the Always-Free VM **on every push
to `main`** (i.e. whenever a PR merges). It builds the frontend on the runner and ships
to the VM over the **IAP tunnel**, so SSH stays closed to the internet — the same steps as
[`README.md`](./README.md), automated.

```
PR merged → push to main → GitHub Actions runner:
  npm ci && npm run build         (dist built on the runner, not the 1 GB VM)
  auth to GCP (keyless — Workload Identity Federation, no stored key)
  tar {backend,docs,deploy,dist} → scp ONE archive → VM  (IAP tunnel, NumPy-accelerated)
  gcloud ssh → unpack → rsync into /opt/salesintel → deploy/deploy.sh → restart
  curl https://<host>/api/health   (fails the job if unhealthy)
```

> **Auth = keyless (Workload Identity Federation).** GitHub mints a short-lived OIDC token
> each run; GCP federates it to the `github-deployer` service account. **No key material is
> stored in GitHub** — nothing to leak or rotate. The federation is locked to this one repo.

---

## What's already provisioned (done once, live now)

- **Service account** `github-deployer@your-gcp-project-id.iam.gserviceaccount.com`
  with roles `roles/compute.instanceAdmin.v1` + `roles/iap.tunnelResourceAccessor`.
- **Workload Identity Pool** `github-pool` + **OIDC provider** `github-provider`, issuer
  `https://token.actions.githubusercontent.com`, restricted by attribute condition to
  `assertion.repository == 'indrani-projects/salesintel-ai'`.
- The repo's WIF principal is granted `roles/iam.workloadIdentityUser` on the SA (so only
  this repo can impersonate it).
- **Repo variables** (Settings → Secrets and variables → Actions → *Variables*):

  | Name | Value |
  |---|---|
  | `GCP_PROJECT` | `your-gcp-project-id` |
  | `GCP_ZONE` | `us-central1-a` |
  | `VM_NAME` | `your-vm` |
  | `SITE_HOST` | `salesintel-ai.duckdns.org` |
  | `GCP_WIF_PROVIDER` | `projects/your-project-number/locations/global/workloadIdentityPools/github-pool/providers/github-provider` |
  | `GCP_SERVICE_ACCOUNT` | `github-deployer@your-gcp-project-id.iam.gserviceaccount.com` |

- **No secrets** are needed — keyless auth uses the variables above plus the workflow's
  `permissions: id-token: write`.

---

## Recreating the WIF setup from scratch (reference)

If the pool/provider ever need rebuilding, these are the exact commands (run as project
owner; `$GC` = full gcloud path on Windows):

```bash
PROJECT=your-gcp-project-id; PNUM=your-project-number; REPO=indrani-projects/salesintel-ai
SA_EMAIL="github-deployer@${PROJECT}.iam.gserviceaccount.com"

gcloud services enable iamcredentials.googleapis.com sts.googleapis.com iam.googleapis.com --project="$PROJECT"

# service account + deploy roles
gcloud iam service-accounts create github-deployer --project="$PROJECT" --display-name="GitHub Actions deployer"
gcloud projects add-iam-policy-binding "$PROJECT" --member="serviceAccount:${SA_EMAIL}" --role="roles/compute.instanceAdmin.v1"   --condition=None
gcloud projects add-iam-policy-binding "$PROJECT" --member="serviceAccount:${SA_EMAIL}" --role="roles/iap.tunnelResourceAccessor" --condition=None

# workload identity pool + GitHub OIDC provider (locked to the repo)
gcloud iam workload-identity-pools create github-pool --project="$PROJECT" --location=global --display-name="GitHub Actions"
gcloud iam workload-identity-pools providers create-oidc github-provider \
  --project="$PROJECT" --location=global --workload-identity-pool=github-pool \
  --issuer-uri="https://token.actions.githubusercontent.com" \
  --attribute-mapping="google.subject=assertion.sub,attribute.repository=assertion.repository" \
  --attribute-condition="assertion.repository=='${REPO}'"

# let ONLY this repo impersonate the SA
gcloud iam service-accounts add-iam-policy-binding "$SA_EMAIL" --project="$PROJECT" \
  --role="roles/iam.workloadIdentityUser" \
  --member="principalSet://iam.googleapis.com/projects/${PNUM}/locations/global/workloadIdentityPools/github-pool/attribute.repository/${REPO}"
```

Then set the `GCP_WIF_PROVIDER` and `GCP_SERVICE_ACCOUNT` repo variables to the provider
resource path and the SA email.

---

## Using it

- **Automatic:** merge any PR into `main` → the **Deploy to VM** workflow runs → the live
  site updates in ~3–4 min. Watch it under the repo's **Actions** tab.
- **Manual:** Actions → **Deploy to VM** → **Run workflow** (the `workflow_dispatch`
  trigger) to redeploy `main` without a new commit.
- **Safety:** a `concurrency` group serializes deploys, and the job **fails** if
  `https://<host>/api/health` doesn't return OK afterward.

The database (`/var/lib/salesintel/salesintel.db`), the on-VM Python venv, and the research
cache (`backend/.cache/`) are all preserved across deploys — the rsync excludes them and the
DB lives outside the deploy dir.

---

## Troubleshooting

- **`Permission denied` / token exchange fails at the auth step.** Confirm the workflow has
  `permissions: id-token: write`, the two `GCP_WIF_*`/`GCP_SERVICE_ACCOUNT` variables are set,
  and the provider's attribute condition matches the repo exactly.
- **`sudo: a password is required` on the VM.** Metadata-added SSH users get passwordless
  sudo on the standard GCP Ubuntu image, so this normally just works. If not, enable OS Login
  and grant the SA `roles/compute.osAdminLogin`.
- **Health check fails but deploy succeeded.** Give it a few seconds (Caddy/uvicorn restart),
  or check `journalctl -u salesintel -n 100 --no-pager` on the VM.

---

## Tearing it down

When the demo's done, remove the deployer identity entirely:

```bash
PROJECT=your-gcp-project-id
gcloud iam service-accounts delete "github-deployer@${PROJECT}.iam.gserviceaccount.com"
gcloud iam workload-identity-pools delete github-pool --location=global --project="$PROJECT"
```

(There is no long-lived key to revoke — keyless auth leaves nothing standing in GitHub.)
