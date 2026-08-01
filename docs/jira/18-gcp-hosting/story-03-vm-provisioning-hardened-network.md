# SI-18.3 — Always-Free VM provisioning + hardened network

| Field | Value |
|---|---|
| Issue type | Story |
| Parent epic | SI-18 — Free Cloud Hosting on GCP |
| Status | Done |
| Priority | High |
| Story points | 5 |
| Component | Deployment |
| Labels | deployment, gcp, infra, security, network |

## User story
As the operator, I want the app to run on a **GCP Always-Free** VM with a **hardened network**, so that it stays free permanently and only the ports it needs are exposed to the internet.

## Description
The app runs on a **Compute Engine `e2-micro`** VM (Ubuntu 24.04) in **`us-central1`**, which sits inside GCP's **Always-Free** tier (an `e2-micro` in `us-central1` / `us-west1` / `us-east1` with a ≤30 GB standard disk). A reserved **static IP** is attached so the public address never changes (free while attached to a running VM), which also lets DuckDNS point at a fixed address with no dynamic updates (see SI-18.5).

The network is locked down:
- **Only ports 80 and 443** are open to the internet (HTTP for the ACME challenge + redirect, HTTPS for the app).
- **SSH is closed to the internet** — access is **only through the Google IAP tunnel** (`gcloud compute ssh --tunnel-through-iap`), with the firewall allowing SSH solely from IAP's source range **`35.235.240.0/20`**. No bastion host is needed.
- The instance is a **Shielded VM** (secure boot + vTPM + integrity monitoring).
- A **budget alert** guards against any accidental spend drift (e.g. leaving the Always-Free envelope).

## Acceptance criteria
```gherkin
Scenario: The VM stays in the Always-Free tier
  Given an e2-micro VM in us-central1 with a <=30 GB standard disk
  When it runs continuously
  Then it remains within GCP's Always-Free allowance
  And a budget alert warns on any spend drift
```

```gherkin
Scenario: Only 80 and 443 are public
  Given the firewall rules on the VM
  When the internet scans the host
  Then only ports 80 and 443 are reachable
```

```gherkin
Scenario: SSH is IAP-only
  Given SSH is closed to the internet and the firewall allows source 35.235.240.0/20
  When an operator runs gcloud compute ssh --tunnel-through-iap
  Then the connection succeeds through Google IAP
  And a direct public SSH attempt is refused
```

```gherkin
Scenario: The VM is a Shielded VM
  Given the instance was created with shielded-vm options
  When its config is inspected
  Then secure boot, vTPM, and integrity monitoring are enabled
```

```gherkin
Scenario: A static IP keeps the address stable
  Given a reserved static IP attached to the running VM
  When the VM restarts
  Then its public IP does not change
```

## Technical notes (reference)
- VM: Compute Engine `e2-micro`, Ubuntu 24.04, `us-central1`; ≤30 GB standard disk to stay Always-Free.
- IP: reserved **static IP** (free while attached to a running VM) — enables fixed DuckDNS host.
- Firewall: public **80/443** only; **SSH source restricted to `35.235.240.0/20`** (IAP), closed to the internet.
- Hardening: **Shielded VM** (secure boot + vTPM + integrity monitoring); **budget alert** on spend.
- Access: `gcloud compute ssh --tunnel-through-iap` — no bastion.

## Definition of Done
- [x] An `e2-micro` Ubuntu 24.04 VM runs in `us-central1` within the Always-Free tier.
- [x] A reserved static IP is attached so the address is stable.
- [x] Firewall exposes only 80/443 publicly; SSH is restricted to the IAP range `35.235.240.0/20`.
- [x] SSH access works only via `gcloud compute ssh --tunnel-through-iap`; direct public SSH is refused.
- [x] The instance is a Shielded VM (secure boot + vTPM + integrity monitoring).
- [x] A budget alert is configured to warn on spend drift.
