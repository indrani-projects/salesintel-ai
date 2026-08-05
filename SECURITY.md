# Security Policy

## Reporting a vulnerability

Please report security issues **privately** — do **not** open a public issue.

Use GitHub's private vulnerability reporting: go to the repository's **Security** tab →
**Report a vulnerability**
([direct link](https://github.com/indrani-projects/salesintel-ai/security/advisories/new)).

This is a proof-of-concept project maintained on a best-effort basis — there is no formal
SLA, but reports are genuinely appreciated and will be looked at promptly.

## Scope

- **In scope:** this repository's own source code (`backend/`, `frontend/`, `deploy/`).
- **Out of scope:** the third-party material under `docs/` (news articles, vendor help
  content) included only for demonstration; and the live demo, which is access-gated.

## Good to know

- No secrets are committed to this repository; deployment credentials live outside git,
  and CI uses keyless auth locked to this repo.
- Secret scanning with push protection is enabled, so accidentally committed credentials
  are blocked at push time.
