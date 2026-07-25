# SI-9.1 — One-command local stack (`stack.ps1` / `stack.sh`)

| Field | Value |
|---|---|
| Issue type | Story |
| Parent epic | SI-9 — Engineering Workflow & Tooling |
| Status | Done |
| Priority | High |
| Story points | 5 |
| Component | DevEx / Tooling |
| Labels | devex, tooling, ops, windows, cross-platform |

## User story
As a developer or demo operator, I want a single command that starts, stops, restarts, and inspects the whole local stack, so that I can run SalesIntel AI end-to-end without juggling two terminals or leaving orphaned processes behind.

## Description
Running the POC by hand means two long-lived commands in two terminals — `uvicorn app.main:app` from `backend/` and `npm run dev` from `frontend/` — plus remembering which one to Ctrl-C first and hoping neither leaked. This story replaces that with a **one-command stack runner**: `stack.ps1` for Windows PowerShell and a parallel `stack.sh` for macOS/Linux, each exposing four actions.

`start` launches the backend on `:8000` and the frontend on `:5173` **detached**, records their PIDs, **waits for each to report healthy** (backend health endpoint reachable, Vite serving), then prints the two URLs so the operator can click straight through. All child output is tee'd to timestamped files under `.logs\` so a crash is diagnosable after the fact rather than lost to a closed terminal.

`stop` is the story's real weight. It **tree-kills the tracked PIDs** (parent *and* the child node/python processes they spawn) and then does a **port sweep** on `:8000` and `:5173` to reap anything the PID list missed — this fixes a real bug where a partially-killed dev server kept its listening socket, so the next `start` failed to bind. After `stop`, **no orphaned processes remain** and the ports are free. `status` reports whether each service is up (by PID and by port), and `restart` is a clean `stop` then `start`.

The Windows script is **ASCII-only by deliberate constraint**: an em-dash in an early version tripped a PowerShell 5.1 parser bug, so the script sticks to plain ASCII punctuation. The macOS/Linux `stack.sh` mirrors the same four actions with equivalent process-group kills and `lsof`/port checks. Usage is documented in README **Step 5** and in `docs\RUNBOOK.md` **§3**.

## Acceptance criteria
```gherkin
Scenario: Start brings both services up detached and healthy
  Given a clone with the backend venv and frontend deps installed
  When the operator runs the "start" action
  Then the backend starts on :8000 and the frontend on :5173, detached
  And the script waits until each reports healthy before returning
  And it prints both URLs and writes logs under .logs\
```

```gherkin
Scenario: Stop leaves no orphans and frees the ports
  Given the stack was started via the runner
  When the operator runs the "stop" action
  Then every tracked PID and its child processes are killed
  And :8000 and :5173 are swept so nothing keeps listening
  And a subsequent "start" binds both ports cleanly
```

```gherkin
Scenario: Status and restart
  Given the stack may or may not be running
  When the operator runs "status"
  Then it reports up/down for each service by PID and by port
  And "restart" performs a clean stop followed by start
```

```gherkin
Scenario: Windows PowerShell 5.1 parses the script (edge case)
  Given the script runs under Windows PowerShell 5.1
  When it is parsed and executed
  Then it contains only ASCII punctuation
  And it does not trip the em-dash parser bug that broke an earlier version
```

## Technical notes (reference)
- Key files: `stack.ps1`, `stack.sh`, `README.md` (Step 5), `docs\RUNBOOK.md` (§3).
- `start` launches backend (`.venv\Scripts\python.exe -m uvicorn app.main:app --port 8000`) and frontend (`npm run dev`, Vite `:5173`) as detached/background processes, persists PIDs, health-polls each, then echoes URLs; stdout/stderr tee to `.logs\`.
- `stop` reads the tracked PIDs and tree-kills them (`Stop-Process` on the process tree / `kill` on the process group), then sweeps `:8000` and `:5173` by port to reap orphans that outlived their parent PID — the fix for the orphaned-socket bind failure.
- `stack.ps1` is ASCII-only (no em-dashes) to avoid a Windows PowerShell 5.1 parse error; `stack.sh` mirrors the same `start`/`stop`/`status`/`restart` actions for macOS/Linux.

## Definition of Done
- [x] `stack.ps1` and `stack.sh` implement `start`, `stop`, `status`, `restart`.
- [x] `start` runs both services detached, waits for health, prints URLs, and logs to `.logs\`.
- [x] `stop` tree-kills tracked PIDs and sweeps both ports so no orphaned processes survive.
- [x] Orphaned-socket bind bug fixed and verified by a start → stop → start cycle.
- [x] `stack.ps1` is ASCII-only and parses under Windows PowerShell 5.1.
- [x] Usage documented in README Step 5 and RUNBOOK §3.
