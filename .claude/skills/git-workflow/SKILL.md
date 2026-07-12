---
name: git-workflow
description: The mandatory git workflow for the SalesIntel_AI repo. Use whenever committing, branching, pushing, opening a PR, or handling authorship in this repo. Enforces — never commit or push to main/master directly; work on a feature branch or worktree; commit as indrani-projects + Co-Authored-By Claude; push the branch; open a PR into main.
---

# SalesIntel_AI — git standard workflow

**Golden rule: `main` (and `master`) are protected. Never commit to them, never
push to them directly, never force-push them.** `main` advances only by **merging a
PR**. All work happens on a short-lived feature branch (or worktree), then a PR.

This is enforced by git hooks (`.githooks/pre-push`, `.githooks/commit-msg`) — see
Enforcement below. The hooks are a safety net; follow the steps regardless.

## Authorship (required on every commit)

- **Author:** `indrani-projects <indrani.patra.projects@gmail.com>`
- **Co-author trailer:** `Co-Authored-By: Claude <noreply@anthropic.com>`

The repo's local git config already sets the author; the `commit-msg` hook adds the
co-author trailer automatically. Do **not** use the machine's default identity
(Shantanu). If `git config user.email` is anything else in this repo, fix it:
```
git config user.name  "indrani-projects"
git config user.email "indrani.patra.projects@gmail.com"
```

## One-time setup per clone

A fresh clone must opt into the shared hooks (git can't auto-enable them):
```
git config core.hooksPath .githooks
```
(Also run the two `git config user.*` lines above if the clone's identity is wrong.)

## The workflow for every change

1. **Start from an up-to-date main, on a new branch** — never work on `main`:
   ```
   git checkout main && git pull --ff-only
   git checkout -b <type>/<slug>        # type = feat | fix | chore | docs | refactor
   ```
   Example: `git checkout -b feat/email-attachments`

2. **Do the work and commit** (as many logical commits as needed) on the branch.
   Author + co-author are applied automatically:
   ```
   git add -A
   git commit -m "feat: short imperative summary

   Optional body explaining what and why."
   ```
   Before committing: never stage secrets (`.env`, `share.config`, keys). `.env` and
   `share.config` are git-ignored; keep it that way.

3. **Push the branch** (not main):
   ```
   git push -u origin <type>/<slug>
   ```

4. **Open a PR into `main`** — do not merge by pushing:
   ```
   gh pr create --base main --head <type>/<slug> --title "..." --body "..."
   ```
   If `gh` isn't installed, open the "Create a pull request" URL that `git push`
   prints, or: `https://github.com/indrani-projects/salesintel-ai/compare/<branch>?expand=1`

5. **After the PR is merged**, clean up:
   ```
   git checkout main && git pull --ff-only
   git branch -d <type>/<slug>
   git push origin --delete <type>/<slug>
   ```

## Worktrees (optional, for parallel work)

To work on two branches at once without stashing:
```
git worktree add ../salesintel-<slug> -b <type>/<slug>
# ...work in that folder..., commit, push, PR as above...
git worktree remove ../salesintel-<slug>
```

## Verification gate (unchanged)

Before opening a PR that touches code, run the mandatory checks: backend `pytest`,
`npm run build`, and Playwright E2E. Docs-only changes may skip Playwright.

## Enforcement (how the guardrails work)

| Hook | Effect |
|---|---|
| `.githooks/pre-push` | **Rejects** any push whose target is `main`/`master`. |
| `.githooks/commit-msg` | Appends `Co-Authored-By: Claude` if missing. |
| git config `user.*` | Author is always `indrani-projects`. |

Escape hatch (rare, e.g. a one-time history fix): `SALESINTEL_ALLOW_MAIN=1 git push ...`.

## Never do

- `git commit` or `git push` while on `main`/`master`.
- `git push origin main`, `git push --force origin main`, `HEAD:main`.
- Commit with the machine's default identity, or without the Claude co-author.
- Stage `.env`, `share.config`, or any credential.
