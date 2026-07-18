# SI-9.4 — Dev workflow standard

| Field | Value |
|---|---|
| Issue type | Story |
| Parent epic | SI-9 — Engineering Workflow & Tooling |
| Status | Done |
| Priority | Medium |
| Story points | 2 |
| Component | DevEx / Tooling |
| Labels | devex, process, testing, agents, quality |

## User story
As a contributor (human or agent), I want a single mandatory development cycle written down as a skill, so that every non-trivial change is planned, built against locked contracts, tested, and verified before it ships — with no stale PRs.

## Description
Parallel, agent-driven development only stays coherent if everyone follows the **same cycle**. This story codifies that cycle as the `dev-workflow` Claude skill, making it the mandatory path for any feature, fix, or non-trivial change.

The cycle is: **plan** the change; **delegate** the work to subagents with **disjoint file ownership** (so parallel work never collides on the same file); **develop against locked contracts** (`schemas.py` / `contracts.py` are the read-only seam between agents); **write or backfill tests** for the change; **run the verification gate** — pytest **and** `npm run build` **and** the Playwright visual E2E — and require **no regressions**; then **ship via the git-workflow** (branch → PR). A change is not "done" until the gate is green.

Crucially, the skill requires **branching off an up-to-date `main` and rebasing onto `origin/main` *before* opening the PR**, so PRs are never stale against the base branch and merges stay clean. The whole standard lives in one file so it is easy to point every contributor and every subagent at it.

## Acceptance criteria
```gherkin
Scenario: A non-trivial change follows the full cycle
  Given a feature or fix that touches product code
  When a contributor picks it up
  Then they plan, delegate to subagents with disjoint file ownership, and develop against the locked contracts
  And they write or backfill tests before claiming completion
```

```gherkin
Scenario: The verification gate must pass before shipping
  Given a change is implemented
  When the contributor runs the verification gate
  Then pytest, npm build, and the Playwright E2E all pass with no regressions
  And only then is the change shipped via the git-workflow
```

```gherkin
Scenario: PRs are never stale against main
  Given a feature branch is ready to open as a PR
  When the contributor prepares the PR
  Then the branch was cut from an up-to-date main
  And it is rebased onto origin/main before the PR is opened
```

## Technical notes (reference)
- Key file: `.claude/skills/dev-workflow/SKILL.md`.
- Contract discipline: `backend/app/schemas.py` and `backend/app/contracts.py` are treated as read-only / append-only — the seam that lets subagents work in parallel without colliding.
- Verification gate composes the SI-8 tooling: pytest (backend), `npm run build` (frontend typecheck + build), and Playwright visual E2E; "no regressions" is the pass bar.
- Rebase-before-PR requirement ties into SI-9.3's git-workflow so the two skills compose into one ship path.

## Definition of Done
- [x] `dev-workflow` Claude skill documents plan → delegate → develop → test → verify → ship.
- [x] Subagent delegation with disjoint file ownership and locked contracts is specified.
- [x] Verification gate (pytest + npm build + Playwright E2E, no regressions) is the completion bar.
- [x] Skill requires branching off up-to-date `main` and rebasing onto `origin/main` before the PR.
- [x] Standard is self-contained in `.claude/skills/dev-workflow/SKILL.md`.
