---
name: dev-workflow
description: The mandatory development workflow for SalesIntel_AI. Use for any feature, fix, or non-trivial change. Enforces the cycle — plan → delegate to subagents (disjoint file ownership) → develop → write/backfill tests → run the verification gate (pytest + build + Playwright visual E2E, no regressions) → ship via the git-workflow (branch → PR). Never report a change done until the gate is green.
---

# SalesIntel_AI — development workflow

Every feature / fix / non-trivial change follows these six steps in order. This
pairs with the **`git-workflow`** skill (which governs branching, authorship, and
PRs) — this skill governs *how the change is built and verified* before it ships.

## 1. Plan

- **Start by creating a branch off an up-to-date default branch (`main`)** — always
  `git fetch origin && git checkout main && git pull --ff-only` first, then
  `git checkout -b <type>/<slug>`. Never work on `main`, never branch from a stale
  `main` (see `git-workflow` step 1).
- Understand the request and the affected code first (read the seam files:
  `backend/app/schemas.py`, `backend/app/contracts.py`, `frontend/src/api/types.ts`).
- For anything non-trivial, lay out the logical steps before writing code. Use plan
  mode / Explore agents to scope uncertain areas. Confirm intent when a choice is
  genuinely the user's to make.

## 2. Delegate (when parallelizable)

- Split independent work across subagents with **disjoint file ownership** so they
  never touch the same files (this is how the app was built):
  - Backend Agent → `backend/app/{main,config,db,models,api}`
  - AI-Engine Agent → `backend/app/services/`
  - Frontend Agent → `frontend/`
- The shared contracts (`schemas.py`, `contracts.py`) are **read-only / append-only**
  — lock them first; agents build against them. Use Explore agents for research
  fan-out. Skip delegation for small, single-file changes.

## 3. Develop

- Implement against the locked contracts; keep field names identical across
  `schemas.py`, `frontend/src/api/types.ts`, and the LLM JSON shape.
- Match the surrounding code's style and idioms. Respect the POC's deliberate
  shortcuts (see `CLAUDE.md`) — don't "fix" them without reason.
- Never stage secrets (`.env`, `share.config`, keys).

## 4. Write / backfill test cases

- Add or extend tests covering the change:
  - Backend → `backend/tests/` (pytest).
  - Frontend / end-to-end → `frontend/e2e/*.spec.ts` (Playwright).
- **Backfill missing tests** for earlier work you touch, so coverage only grows.

## 5. Run the verification gate (mandatory — before any commit/PR)

Deterministic modes keep this fast and quota-free: tests/E2E run with `MOCK_LLM=1`
and `MOCK_EMAIL=1` (see `backend/tests/conftest.py`, `frontend/playwright.config.ts`).

```powershell
# backend unit + API
backend\.venv\Scripts\python.exe -m pytest backend\tests -q
# frontend typecheck + build
cd frontend; npm run build
# Playwright visual E2E (boots its own mock servers; stop any running on :8000/:5173 first)
npx playwright test
```

- **Playwright is a visual pass**: confirm every affected screen renders and works,
  and that nothing regressed. Read the screenshots in `frontend/e2e/screenshots/`.
- Docs-only changes (no runtime surface) may skip Playwright — say so explicitly.
- **Do not report a change as done until the gate is green.** If tests fail, fix the
  cause; report failures honestly with the output.

## 6. Ship

Follow **`git-workflow`** to ship. In order:
1. **Rebase onto the latest `main` before raising the PR** so it's never stale:
   `git fetch origin && git rebase origin/main` (resolve any conflicts).
2. **Re-run the gate** (step 5 above) after the rebase — it can shift behavior.
3. **Push** the branch (`git push --force-with-lease` if it was pushed pre-rebase).
4. **Open a PR** into `main`. Never commit or push to `main` directly; commits are
   authored `indrani-projects` + `Co-Authored-By: Claude` automatically.

## Quick checklist

- [ ] Branched off an up-to-date `main`.
- [ ] Planned the steps; scoped the code.
- [ ] Delegated disjoint work to subagents (if parallelizable).
- [ ] Implemented against the locked contracts.
- [ ] Added/backfilled tests.
- [ ] `pytest` green · `npm run build` green · Playwright E2E green (screenshots checked).
- [ ] Rebased onto latest `main`, re-ran the gate, then opened a PR (never straight to `main`).
