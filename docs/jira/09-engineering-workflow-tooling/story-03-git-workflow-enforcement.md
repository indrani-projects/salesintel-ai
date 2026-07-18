# SI-9.3 — Git workflow standard + enforcement

| Field | Value |
|---|---|
| Issue type | Story |
| Parent epic | SI-9 — Engineering Workflow & Tooling |
| Status | Done |
| Priority | High |
| Story points | 3 |
| Component | DevEx / Tooling |
| Labels | devex, git, hooks, process, safety |

## User story
As a maintainer, I want a documented git workflow that is enforced by hooks rather than by memory, so that no one — human or agent — can push straight to `main`, and every commit is consistently attributed.

## Description
The repo's rule is simple: **never commit or push to `main`/`master` directly**. The correct path is always **branch → commit → rebase onto latest `main` → push → PR**. But a rule that lives only in a doc gets broken, so this story makes it **enforced locally by git hooks** and **codified as a Claude skill** so both people and agents follow the same path.

`.githooks/pre-push` **blocks any push whose target is `main` or `master`**, with an explicit escape hatch (`SALESINTEL_ALLOW_MAIN=1`) for the rare intentional case. `.githooks/commit-msg` **auto-appends the `Co-Authored-By: Claude` trailer** to every commit message that lacks it, so attribution is automatic rather than something to remember. Hooks are opt-in per clone via `git config core.hooksPath .githooks`, wired up by `bootstrap.ps1` / `bootstrap.sh` so a fresh clone is one command away from being protected. Because the hooks are shell scripts that must keep LF endings on Windows, `.gitattributes` **forces LF on the hook files** so they stay executable and parseable.

The `git-workflow` Claude skill documents the same standard for agent use: branch off an up-to-date `main`, commit with the standard identity, rebase onto latest `main`, push the branch, open the PR. The workflow is also written up in `docs\RUNBOOK.md` **§10**.

## Acceptance criteria
```gherkin
Scenario: Direct push to main is rejected
  Given core.hooksPath points at .githooks
  When a developer pushes commits whose target ref is main or master
  Then the pre-push hook aborts the push with a clear message
  And the developer must use a feature branch and a PR instead
```

```gherkin
Scenario: Intentional override is possible
  Given a maintainer must push to main deliberately
  When SALESINTEL_ALLOW_MAIN=1 is set for that push
  Then the pre-push hook allows it through
```

```gherkin
Scenario: Co-author trailer is added automatically
  Given a commit message without the Co-Authored-By: Claude trailer
  When the commit is created with hooks enabled
  Then the commit-msg hook appends the trailer
```

```gherkin
Scenario: Hooks are enabled on a fresh clone
  Given a newly cloned repo
  When the developer runs bootstrap.ps1 or bootstrap.sh
  Then git config core.hooksPath is set to .githooks
  And the pre-push and commit-msg hooks are active
```

## Technical notes (reference)
- Key files: `.claude/skills/git-workflow/SKILL.md`, `.githooks/pre-push`, `.githooks/commit-msg`, `bootstrap.ps1`, `bootstrap.sh`, `.gitattributes`, `docs\RUNBOOK.md` (§10).
- `pre-push` inspects the target refs and exits non-zero when pushing to `main`/`master` unless `SALESINTEL_ALLOW_MAIN=1`; `commit-msg` appends `Co-Authored-By: Claude ...` when absent.
- Activation: `git config core.hooksPath .githooks` (run directly or via `bootstrap.*`). `.gitattributes` marks the hooks as LF so they remain valid POSIX scripts when checked out on Windows.
- Standard workflow (skill + RUNBOOK §10): branch off up-to-date `main` → commit → rebase onto latest `main` → push branch → open PR into `main`.

## Definition of Done
- [x] `.githooks/pre-push` blocks pushes to `main`/`master`, with `SALESINTEL_ALLOW_MAIN=1` override.
- [x] `.githooks/commit-msg` auto-adds the `Co-Authored-By: Claude` trailer.
- [x] Hooks enabled via `core.hooksPath .githooks`, wired by `bootstrap.ps1` / `bootstrap.sh`.
- [x] `.gitattributes` forces LF on the hook files.
- [x] `git-workflow` Claude skill documents branch → commit → rebase → push → PR.
- [x] Workflow written up in RUNBOOK §10.
