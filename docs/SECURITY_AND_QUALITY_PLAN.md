# Security & Quality Hardening Plan

Derived from a three-part audit (backend security, frontend/deploy security, code
quality) of the **live public** deployment at `https://salesintel-ai.duckdns.org`.
This plan closes the real security gaps and pays down hygiene debt **without changing
what the application does**.

## Decisions locked

- **Access model: whole-site shared password** (Caddy basic-auth). One password gates the
  entire app + API + `/library` docs; `/api/health` (CI probe) and `/api/auth/google/*`
  (OAuth login+callback) stay exempt so CI and "Connect Google" keep working.
- **A4 (restrict email recipient) is intentionally dropped** — it would change app
  behaviour (today you can email any address, by design). With the access gate (A1) in
  place, only trusted users can reach the send endpoint, so the email-abuse risk is closed
  **without** a behaviour change.
- **A7 (generic client errors) is kept.**
- The only intentional user-visible change in the whole plan is the **password prompt at the
  door (A1)** and **friendlier error text (A7)**. Nothing changes what the app *does*.

## Guardrails — acceptance criteria that apply to EVERY task

1. One task = one branch = one PR; no task bundles unrelated changes.
2. Green gate before merge: `pytest` all pass · `npm run build` clean · Playwright E2E no
   regressions vs. the current baseline (9/9).
3. Auto-deploy verified: within ~5 min of merge, `/api/health` returns `{"status":"ok"}`
   and the homepage loads over HTTPS.
4. Each PR states the exact existing behaviour it must preserve, and a one-line rollback
   (revert the PR → next deploy restores prior state).
5. Caddy/deploy-only changes can't be exercised by the local gate (it bypasses Caddy) → they
   carry an explicit **live smoke test** in their acceptance criteria.

---

## Epic A — Public-access hardening (security) · P0/P1

### A1 — Whole-site password gate (Caddy basic-auth) · P0 — do first
Closes in one move: unauthenticated API, Gmail-send abuse, quota/cost DoS, exposed Swagger,
publicly served ops docs.

**Change:** add a `basic_auth` gate to `deploy/Caddyfile` covering everything **except**
`/api/health` and `/api/auth/google/*`. The bcrypt hash is injected at deploy time from
`DEMO_AUTH_HASH` in `/etc/salesintel/env` (rendered like the existing `__SITE_HOST__`), and
is **never committed**. Requires a matching one-line addition to `env.production.example`
and the `deploy.sh` render step.

**Acceptance criteria:**
- Anonymous request to `/`, `/api/meetings`, `/api/docs` → **401**.
- Request with the shared credential → app loads and behaves exactly as today.
- **Connect Google completes end-to-end on the live site** (callback exempt; browser carries
  creds to `/settings`).
- CI post-deploy `/api/health` check still passes (path exempt).
- `grep -ri` over the repo shows **no password and no hash** committed; the hash exists only
  in `/etc/salesintel/env`.
- Local Playwright gate unaffected (bypasses Caddy) — still 9/9.

**No-break / rollback:** zero app-code change; revert the Caddyfile commit → redeploy removes
the gate.

### A2 — Fix the PDF-export XSS · P0
The only true XSS: `frontend/src/lib/briefHtml.ts` interpolates `company`, `headline`,
`s.title`, `src.title`, `src.filename` into `innerHTML` **unescaped** (sink at
`BriefCard.tsx:52`). The on-screen UI is already safe (react-markdown, no raw HTML).

**Change:** HTML-escape every interpolated field in `renderBriefToHtml` (or escape the
assembled string before `innerHTML`).

**Acceptance criteria:**
- A brief whose company/headline contains `<img src=x onerror=alert(1)>` exports to PDF with
  the payload rendered as **inert text** — no script execution.
- Normal briefs export visually identical to today.
- Backed by a unit test (see D1); `npm run build` clean; E2E unchanged.

**No-break:** pure escaping of already-displayed fields.

### A3 — Security headers in Caddy · P1
**Change:** add a `header {}` block to `deploy/Caddyfile`: `Strict-Transport-Security`,
`X-Frame-Options: DENY`, `X-Content-Type-Options: nosniff`, `Referrer-Policy`, and a
conservative `Content-Security-Policy` tuned to the SPA's actual inline needs.

**Acceptance criteria:**
- Live `curl -I` shows all five headers.
- App, brief render, chat, Connect Google, and PDF export all still work (CSP verified not to
  block anything the app needs).
- Rollback = revert Caddyfile commit.

### A5 — Disable Swagger/OpenAPI in production · P2 (A1 already gates it)
**Change:** set `docs_url/redoc_url/openapi_url=None` in `main.py` unless a debug flag is set.

**Acceptance criteria:** local dev still serves `/docs`; production `/api/docs` → 404; every
endpoint still functions; gate green.

### A6 — OAuth `state` nonce (CSRF on connect) · P2
**Change:** generate + persist a `state` in `authorization_url`, validate it in the callback
(`google_service.py` + `api/google.py`).

**Acceptance criteria:** Connect Google still works live; a callback with missing/mismatched
`state` is rejected; `test_google.py` extended; gate green.

### A7 — Generic client-facing errors · P2 (kept)
Stop returning raw `str(e)` to clients: brief error surfaced via `briefs.py` (source
`meetings.py:75`), `google.py:331`, `email_service.py:260/312`.

**Change:** log full detail server-side; return generic messages to clients.

**Acceptance criteria:**
- Error responses contain no LLM/model/Google internals.
- `status=error` briefs still display a friendly message; "send email" failure still surfaces
  a friendly message.
- Existing tests adjusted; gate green.

**Visible change (accepted):** error text becomes friendlier/less technical; server logs keep
full detail.

> **Dropped: A4 (restrict/validate email recipient).** Would change app behaviour; covered by
> A1 instead.

---

## Epic B — Deploy/ops hardening · P2

### B1 — Enforce env-file `chmod 600` in `deploy.sh`
**Acceptance:** after deploy, `/etc/salesintel/env` is `600`, owned by `salesintel` (verify
live); deploy still succeeds; app healthy.

### B2 — Broaden `.gitignore` for `.env.local` / `.env.*.local`
**Acceptance:** patterns added; `git check-ignore` confirms; committed
`frontend/.env.production` remains tracked (unchanged).

### B3 — (Optional) extra systemd hardening
`ProtectSystem=strict`, `RestrictAddressFamilies=AF_INET AF_INET6 AF_UNIX`,
`ProtectKernelTunables`, `PrivateDevices`, etc. in `deploy/salesintel.service`.

**Acceptance:** `systemctl status salesintel` active after deploy; app + both daemons +
outbound Gemini/Google calls all still work (validate live — this is the risk area).

---

## Epic C — Code quality & hygiene · P2 (all invisible to users)

### C1 — Promote cross-module private symbols
Make `sources._normalize`/`_display_name` and `retrieval._domain` public (or route through the
existing `slugify` wrapper); update callers (`brief_engine.py:29`, `api/google.py` ×5,
`prep.py:36`).
**Acceptance:** no module imports another module's `_`-prefixed name (grep clean); behaviour
identical; full gate green.

### C2 — `print()` → `logging`
**Acceptance:** no `print()` in `backend/app` (grep); sync/daemon events still logged; gate
green.

### C3 — Deprecation sweep
`datetime.utcnow()` → `datetime.now(timezone.utc)`; `@app.on_event("startup")` → lifespan.
**Acceptance:** those deprecation warnings gone under `pytest -W`; timestamps still serialize
as `…Z`; startup/daemons still run; gate green.

### C4 — De-duplicate `_strip_fences`; centralize `MAX_DOC_CHARS`
`_strip_fences` is copy-pasted (`brief_engine.py:284`, `chat_service.py:55`); `8000` appears in
`sources.py:25`, `chat_service.py:32`, and config.
**Acceptance:** one shared impl/constant; brief + chat output byte-identical on mock fixtures;
gate green.

### C5 — Remove vestigial persona-toggle markup + `key_facts` 5-vs-4 mismatch
`BriefView.tsx:148-160` (dead "View as" buttons), `key_facts` capped at 5 in the engine but
sliced to 4 in the KPI strip.
**Acceptance:** dead controls removed; brief view otherwise visually unchanged (screenshot
diff); build + E2E green.

### C6 — Prune unused `xhtml2pdf` dependency
PDF export is client-side (`lib/pdf.ts`); `xhtml2pdf` in `requirements.txt` is residual.
**Acceptance:** removed; `pip install -r` + server start + brief/PDF flow all still work; gate
green.

---

## Epic D — Test coverage · P2

### D1 — Frontend unit tests (Vitest)
Cover `MarkdownView` citation parsing, `auth.initials`, `format.ts`, `BriefView`
polling/persona logic, **and the A2 escaping**.
**Acceptance:** `npm run test` passes; the listed units covered; existing gate not materially
slowed.

### D2 — Direct tests for `brief_render._md_to_html`
**Acceptance:** new backend tests assert bold/italic/link/escaping edge cases; pass.

---

## Epic E — Documentation · P2

### E1 — Reconcile `CLAUDE.md` + stale docstrings with reality
Fix "no test suite" (now 80 backend + 9 E2E), 3→6 personas, "hardcoded URL"→env-driven,
`brief_engine.py` docstring; add the auth-gate + CI/WIF facts.
**Acceptance:** a fresh read of `CLAUDE.md` matches the running code; no code impact.

---

## Recommended execution order

1. **A1** — the gate (highest risk-reduction), ship first.
2. **A2, A3** — XSS + headers (quick, high value).
3. **A5, A6, A7** — remaining security.
4. **B, C, D, E** — ops hygiene, quality, tests, docs (no user-facing risk).

## Definition of done (whole plan)

- Anonymous internet access to the app/API is closed (A1); the one true XSS is fixed (A2);
  security headers present (A3); Swagger gated (A5); OAuth CSRF-protected (A6); no internal
  error leakage (A7).
- Deploy secrets file locked to `600` (B1); ignore rules broadened (B2).
- No cross-module private-symbol coupling; `logging` in place; deprecations swept; small
  duplication/magic-constant debt removed (C1–C6).
- Frontend unit tests + `_md_to_html` tests added (D1–D2).
- `CLAUDE.md` matches reality (E1).
- Every merge kept the live app healthy; nothing changed what the application *does* beyond
  the password gate (A1) and friendlier error text (A7).
