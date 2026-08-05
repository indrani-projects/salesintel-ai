# SI-9.5 — Commit identity & secret hygiene

| Field | Value |
|---|---|
| Issue type | Story |
| Parent epic | SI-9 — Engineering Workflow & Tooling |
| Status | Done |
| Priority | High |
| Story points | 2 |
| Component | DevEx / Tooling |
| Labels | devex, git, security, secrets, hygiene |

## User story
As a maintainer, I want every commit to carry one consistent identity and no secret to ever enter the repo, so that the git history is clean and attributable and no credential is leaked to anyone who clones it.

## Description
Two adjacent hygiene concerns, one story. First, **commit identity**: every commit is authored as `indrani-projects <indrani-projects@users.noreply.github.com>` with a `Co-Authored-By: Claude` trailer. The git history was **rewritten to remove a personal identity** that had crept into early commits, so the whole log presents a single, intentional author. (The trailer is kept automatic by the `commit-msg` hook from SI-9.3.)

Second, **secret hygiene**: `.gitignore` guards keep sensitive and runtime files out of version control — never commit `.env` (LLM/SMTP credentials), `share.config` (tunnel/ngrok config), `.logs/` (runtime logs), or `client_secret_*.json`. That last pattern is not hypothetical: a downloaded **Google OAuth client-secret JSON was caught by a pre-commit secret scan** before it could be committed, and the ignore pattern was added so it can never slip in again.

**Server-side branch protection** — the GitHub-side rule that would block force-pushes and required-review bypass at the origin — was **evaluated but deferred**: it is a paid feature for private repos on the Free plan (available free only on public repos). The decision and its rationale are documented so the deferral is a known, deliberate gap rather than an oversight, with local pre-push enforcement (SI-9.3) covering the day-to-day case.

## Acceptance criteria
```gherkin
Scenario: History presents a single consistent author
  Given the rewritten git history
  When the log is inspected
  Then every commit is authored as indrani-projects <indrani-projects@users.noreply.github.com>
  And carries a Co-Authored-By: Claude trailer
  And no personal identity remains in the history
```

```gherkin
Scenario: Secrets and runtime files are ignored
  Given .gitignore is in effect
  When .env, share.config, .logs/, or client_secret_*.json exist in the working tree
  Then none of them are tracked or stageable by default
```

```gherkin
Scenario: A downloaded OAuth secret is caught before commit
  Given a client_secret_*.json in the working tree
  When a commit is attempted
  Then the pre-commit secret scan / .gitignore guard prevents it from being committed
```

```gherkin
Scenario: Branch protection is a documented, deliberate deferral
  Given the repo is private on the GitHub Free plan
  When server-side branch protection is considered
  Then it is recorded as evaluated and deferred because it is a paid feature there
  And local pre-push enforcement is noted as the interim control
```

## Technical notes (reference)
- Key files: `.gitignore`, repo git config (author identity), and the SI-9.3 `commit-msg` hook (trailer).
- `.gitignore` patterns include `.env`, `share.config`, `.logs/`, and `client_secret_*.json`; the last was added after a pre-commit secret scan intercepted a downloaded Google OAuth client-secret file.
- History rewrite normalized author/committer to `indrani-projects <indrani-projects@users.noreply.github.com>`; the `Co-Authored-By: Claude` trailer is enforced going forward by the commit-msg hook.
- Server-side branch protection is unavailable free on private repos (Free plan); evaluated and deferred, with local `pre-push` (SI-9.3) as the interim guardrail.

## Definition of Done
- [x] All commits authored `indrani-projects <indrani-projects@users.noreply.github.com>` + `Co-Authored-By: Claude`.
- [x] History rewritten to remove the personal identity; log presents one consistent author.
- [x] `.gitignore` guards `.env`, `share.config`, `.logs/`, and `client_secret_*.json`.
- [x] Downloaded OAuth client-secret JSON verified caught before commit.
- [x] Server-side branch protection evaluated and its deferral documented with rationale.
