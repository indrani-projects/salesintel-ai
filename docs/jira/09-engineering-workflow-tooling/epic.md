# EPIC SI-9 — Engineering Workflow & Tooling

| Field | Value |
|---|---|
| Issue type | Epic |
| Suggested key | SI-9 |
| Status | Done |
| Priority | High |
| Component | DevEx / Tooling |
| Labels | devex, tooling, ci, git, ops |
| Story points (rollup) | 15 |

## Summary
The developer-experience layer that made the POC reproducible and safe to iterate on — a one-command local stack, one-command public sharing, an enforced git workflow, a mandatory dev workflow, and commit-identity/secret hygiene.

## Description
SalesIntel AI was built fast, across parallel agents with disjoint file ownership, on a single Windows machine that also had to demo it live. None of that is possible without a DevEx layer that makes the stack **trivial to run, trivial to share, and impossible to break through carelessness**. This epic collects that layer — the scripts, skills, hooks, and hygiene rules that surround the product code but never ship inside it.

The centrepiece is a **one-command local stack runner** (`stack.ps1` on Windows, `stack.sh` on macOS/Linux): `start` brings up the FastAPI backend on `:8000` and the Vite frontend on `:5173` detached, waits for health, prints the URLs, and tees logs to `.logs\`; `stop` tree-kills the tracked PIDs and sweeps the ports so **no orphaned processes** survive — closing a real bug where a half-killed dev server held its socket and the next `start` failed. `status` and `restart` round it out. The same script grew a **`share` action** that runs the frontend in share mode behind the Vite proxy and opens a public tunnel (ngrok static domain or a Cloudflare quick tunnel), so a reviewer anywhere gets one URL that serves both app and API.

Around the scripts sits the **process discipline**. A `git-workflow` Claude skill plus git hooks make direct pushes to `main`/`master` fail (`.githooks/pre-push`) and auto-stamp every commit with the `Co-Authored-By: Claude` trailer (`.githooks/commit-msg`); the rule is always branch → commit → rebase onto latest `main` → push → PR. A `dev-workflow` skill codifies the mandatory build cycle — plan → delegate to subagents → develop against locked contracts → write/backfill tests → run the verification gate (pytest + npm build + Playwright E2E) → ship via the git workflow. Finally, **commit-identity and secret hygiene**: history was rewritten to a single authorship (`indrani-projects` + `Co-Authored-By: Claude`), and `.gitignore` guards keep secrets (`.env`, `share.config`, `client_secret_*.json`) and runtime cruft (`.logs/`) out of the repo — one downloaded Google OAuth client-secret JSON was caught by a pre-commit secret scan before it could land.

None of this is product behaviour, but all of it is why the product could be built, demoed, and handed over without the "works on my machine" tax.

## Stories in this epic
| Key | Story | Points | Priority |
|---|---|---|---|
| SI-9.1 | One-command local stack (`stack.ps1` / `stack.sh`) | 5 | High |
| SI-9.2 | One-command public sharing (`stack.ps1 share`) | 3 | Medium |
| SI-9.3 | Git workflow standard + enforcement | 3 | High |
| SI-9.4 | Dev workflow standard | 2 | Medium |
| SI-9.5 | Commit identity & secret hygiene | 2 | High |

## Epic acceptance criteria
```gherkin
Scenario: One command brings the whole stack up
  Given a fresh clone with the backend venv and frontend deps installed
  When the developer runs the stack "start" action
  Then the backend comes up on :8000 and the frontend on :5173, detached
  And the script waits for health, prints both URLs, and logs to .logs\
```

```gherkin
Scenario: Stop leaves no orphaned processes
  Given the stack was started via the runner
  When the developer runs the "stop" action
  Then every tracked PID is tree-killed and both ports are swept
  And a subsequent "start" binds :8000 and :5173 cleanly
```

```gherkin
Scenario: Direct push to main is blocked
  Given the git hooks are enabled via core.hooksPath
  When a developer attempts to push commits directly to main
  Then the pre-push hook rejects the push
  And the developer must branch, push, and open a PR instead
```

```gherkin
Scenario: A secret is stopped before it is committed
  Given a downloaded Google OAuth client-secret JSON in the working tree
  When the developer attempts to commit
  Then the secret scan / .gitignore guard prevents the file from being committed
```

## Out of scope
- Product features, brief content, or LLM behaviour (owned by other epics).
- Hosted CI runners / cloud deployment pipelines (local-first POC).
- Server-side branch protection (a paid feature on private Free repos — evaluated and deferred).

## Dependencies
- Backend venv and frontend `node_modules` present (the runner orchestrates, it does not install).
- The verification gate referenced by the dev-workflow skill (pytest suite, `npm run build`, Playwright E2E) delivered under SI-8.
