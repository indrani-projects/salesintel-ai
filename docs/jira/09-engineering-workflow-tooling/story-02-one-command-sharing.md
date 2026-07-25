# SI-9.2 — One-command public sharing (`stack.ps1 share`)

| Field | Value |
|---|---|
| Issue type | Story |
| Parent epic | SI-9 — Engineering Workflow & Tooling |
| Status | Done |
| Priority | Medium |
| Story points | 3 |
| Component | DevEx / Tooling |
| Labels | devex, tooling, sharing, tunnel, frontend |

## User story
As a demo operator, I want one command that exposes the running app to a public URL, so that a reviewer anywhere can try SalesIntel AI without installing anything, and I can tear it down as cleanly as I started it.

## Description
Showing the POC to someone off the machine used to mean a separate `share-demo.ps1` script and a mental model of "which thing tunnels what." This story **consolidates that into `stack.ps1 share`** — one action on the same runner that already manages the local stack.

`share` runs the **frontend in share mode** (`vite --mode share`) with `VITE_API_URL=/api`, so the app calls the API through the **Vite dev proxy** rather than `http://localhost:8000`. That single change means one tunnel URL serves **both the app and its API** — the browser only ever talks to the tunnel origin, and the proxy forwards `/api/*` to the local backend. The action then opens a **public tunnel**: an **ngrok static domain** if `share.config` supplies one (stable URL across restarts), otherwise a **Cloudflare quick tunnel** (zero-config, ephemeral URL). The tunnel process is launched **detached and tracked** the same way the stack services are, so `stack.ps1 stop` kills it too and no tunnel is left dangling.

Configuration lives in `frontend\.env.share` (share-mode env), `frontend\vite.config.ts` (the `/api` proxy + share mode), and `frontend\package.json` (`dev:share` and `share` scripts). The flow is documented in `docs\SHARING.md`.

> Note: the running machine has **only new Outlook (no COM automation)** — unrelated to sharing, but it is why the email feature is SMTP/Gmail-only rather than driving a desktop Outlook client.

## Acceptance criteria
```gherkin
Scenario: One command exposes app and API on a single public URL
  Given the local backend is available on :8000
  When the operator runs the "share" action
  Then the frontend runs in share mode with VITE_API_URL=/api
  And a public tunnel opens serving both the app and the proxied API from one origin
  And the operator is given the public URL
```

```gherkin
Scenario: Static domain when configured, quick tunnel otherwise
  Given share.config may or may not define an ngrok static domain
  When the operator runs "share"
  Then a stable ngrok domain is used when share.config is set
  And a Cloudflare quick tunnel is used when it is not
```

```gherkin
Scenario: Stop also tears down the tunnel
  Given a share session is running
  When the operator runs the "stop" action
  Then the tracked tunnel process is killed along with the stack
  And no tunnel or share-mode frontend is left running
```

## Technical notes (reference)
- Key files: `stack.ps1` (`share` action), `docs\SHARING.md`, `frontend\.env.share`, `frontend\vite.config.ts`, `frontend\package.json` (`dev:share`, `share`).
- Share mode: `vite --mode share` loads `.env.share` with `VITE_API_URL=/api`; `vite.config.ts` proxies `/api` → `http://localhost:8000`, so the app and API are same-origin behind one tunnel URL.
- Tunnel selection: ngrok with a static domain when `share.config` provides one (persistent URL), else a Cloudflare quick tunnel (ephemeral). The tunnel is launched detached and its PID tracked so `stop` reaps it.
- Consolidation: the previous standalone `share-demo.ps1` was folded into `stack.ps1 share` so there is a single entry point for local and public runs.

## Definition of Done
- [x] `stack.ps1 share` runs the frontend in share mode (`vite --mode share`, `VITE_API_URL=/api`) behind the Vite proxy.
- [x] One tunnel URL serves both the app and the API.
- [x] ngrok static domain used when `share.config` is set; Cloudflare quick tunnel otherwise.
- [x] Tunnel launched detached and tracked so `stop` kills it — no dangling tunnels.
- [x] Old `share-demo.ps1` consolidated into `stack.ps1 share`.
- [x] Flow documented in `docs\SHARING.md`; share config wired in `.env.share`, `vite.config.ts`, `package.json`.
