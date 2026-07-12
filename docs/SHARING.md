# Sharing SalesIntel AI with your team (no deploy)

How to give non-technical peers a public link to the app running on your machine —
no infra, no build step. For general setup / run / troubleshooting see
[`RUNBOOK.md`](RUNBOOK.md); for what the app is, [`../README.md`](../README.md).

---

## Quick start

One command starts the backend, the frontend (in shared-demo mode), and a public
tunnel:

```powershell
cd frontend
npm run share          # or, from the repo root:  .\share-demo.ps1
```

It opens two server windows and prints (and copies to your clipboard) an
`https://…` URL. Send that to anyone — they open it in a browser, nothing to
install. The link is **live only while the command is running**; close the
windows to take it offline.

Requirements while sharing:
- A real `LLM_API_KEY` in `backend/.env` (or briefs land in `status=error`).
- Your machine stays awake and online.

---

## Fixed URL (recommended — one-time ~3 min)

By default the tunnel is a free **Cloudflare quick tunnel**: zero setup, but the
URL is **random each run**. For a URL that never changes, use a free **ngrok
static domain**:

1. Sign up free at <https://ngrok.com> and copy your authtoken (dashboard → *Your
   Authtoken*).
2. Register it once on this machine:
   ```powershell
   ngrok config add-authtoken <YOUR_TOKEN>
   ```
3. Claim your free static domain in the ngrok dashboard (**Universal Gateway →
   Domains → Create Domain**), e.g. `sleep-demo.ngrok-free.app`.
4. Point the launcher at it — copy the template and fill in the domain:
   ```powershell
   copy share.config.example share.config
   # then edit share.config:  NGROK_DOMAIN=sleep-demo.ngrok-free.app
   ```

Now every `npm run share` serves that **same URL, forever**. `share.config` is
gitignored (it's yours). You can also override per-run without the file:

```powershell
.\share-demo.ps1 -Domain sleep-demo.ngrok-free.app
.\share-demo.ps1 -Provider cloudflare      # force the random tunnel even if ngrok is set up
```

**Heads-up:** ngrok's free tier shows visitors a one-time "Visit Site"
interstitial before the app loads — a minor speed bump. Cloudflare quick tunnels
have no interstitial but a random URL. Pick your trade-off.

---

## How it works (why one URL serves everything)

The frontend hardcodes the backend at `http://localhost:8000`, and browsers block
a public page from calling `localhost` (Private Network Access). So share mode
routes the API **same-origin** instead:

- `npm run share` runs the frontend as `vite --mode share`, which loads
  `frontend/.env.share` → `VITE_API_URL=/api`.
- `frontend/src/api/client.ts` then points the axios base at `/api`.
- `frontend/vite.config.ts` proxies `/api/*` → `http://localhost:8000` and sets
  `allowedHosts: true` so the tunnel host is accepted.

Result: **one tunnel URL serves both the app and the API** — no CORS, no second
URL. Normal `npm run dev` is unaffected (it still talks to `localhost:8000`
directly), so local dev and the E2E tests behave exactly as before.

Verified end-to-end over a live Cloudflare tunnel from a fresh (incognito) browser:
app loads → create meeting (POST) → dashboard → brief generates & renders (9
sections) → Scout answers — with **zero requests hitting localhost**.

---

## Tooling / files

| Thing | Where |
|---|---|
| Launcher | `share-demo.ps1` (repo root); `npm run share` alias in `frontend/package.json` |
| Share-mode env | `frontend/.env.share` (`VITE_API_URL=/api`); script `dev:share` |
| Fixed-domain config | `share.config` (gitignored); template `share.config.example` |
| Tunnel binaries | `%USERPROFILE%\bin\cloudflared.exe`, `%USERPROFILE%\bin\ngrok.exe` |

Re-download a tunnel binary if it goes missing:

```powershell
# cloudflared
Invoke-WebRequest "https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-windows-amd64.exe" -OutFile "$env:USERPROFILE\bin\cloudflared.exe"
# ngrok
Invoke-WebRequest "https://bin.equinox.io/c/bNyj1mQVY4c/ngrok-v3-stable-windows-amd64.zip" -OutFile "$env:TEMP\ngrok.zip"
Expand-Archive "$env:TEMP\ngrok.zip" "$env:USERPROFILE\bin" -Force
```

---

## Troubleshooting (sharing-specific)

For general app issues (briefs stuck, empty `/companies`, LLM key) see
[`RUNBOOK.md` §8](RUNBOOK.md). Tunnel-specific:

| Symptom | Fix |
|---|---|
| Tunnel URL shows **502 / "Bad Gateway"** | Frontend not up yet — wait a few seconds and refresh. |
| Fresh Cloudflare URL returns **530** for ~15s | Normal cold-start edge propagation; retry shortly. |
| Peers see a **CORS / "loopback address space"** error | Frontend isn't in share mode. Use `npm run share` / `dev:share`, not `npm run dev`. |
| ngrok "authentication failed" | Run `ngrok config add-authtoken <TOKEN>` once. |
| ngrok domain in use / "reserved" | The static domain is already claimed by another agent — stop other ngrok sessions. |

---

## Want a permanent link instead? (out of scope for now)

Tunnels need your machine on. For an always-on URL, deploy the backend (Render /
Fly / Railway free tier) and the frontend (Vercel / Netlify), set `VITE_API_URL`
to the deployed backend and open CORS. ~30–60 min; not needed for live-demo
sharing.
