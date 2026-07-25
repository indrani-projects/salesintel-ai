# EPIC SI-16 — Scheduled Day-Before Persona Email (+ per-persona routing)

| Field | Value |
|---|---|
| Issue type | Epic |
| Suggested key | SI-16 |
| Status | Done |
| Priority | High |
| Component | Brief Delivery |
| Labels | backend, frontend, email, automation, config |
| Story points (rollup) | 13 |

## Summary
Add a **third automated-email trigger** — send a prospect's persona brief **~1 day before** the meeting — and route every auto-email to a **per-persona** recipient. Extends the existing automation (on-ready + 1-hour reminder) with a 24h day-before window guarded by an idempotent column, and delivers each brief to the meeting persona's configured address. Shipped as PR #15 (branch `feat/day-before-email`).

## Description
The automated-email feature already fired on two triggers: once when a brief becomes ready, and once ~1 hour before the meeting. Both sent to a single default recipient. This epic closes two gaps that a real sales workflow exposes — reps want the brief in hand the day before, not just the hour before, and the brief should land with the *person who owns that persona*, not one shared inbox.

The first change is a **day-before trigger**. Once a meeting's brief is ready, its persona brief is emailed when the meeting enters the day-before window. The behaviour is config-driven — `DAY_BEFORE_EMAIL_ENABLED` (default true) and `DAY_BEFORE_LEAD_MINUTES` (1440 = 24h) — and made idempotent by a new `Meeting.day_before_sent_at` guard column, added through the existing `_ADDED_COLUMNS` SQLite migration path so no schema reset is needed. It fires from the same reminder poll loop that already drives the 1-hour reminder, so no new scheduler is introduced.

The second change is **per-persona recipient routing**. A `PERSONA_EMAILS` JSON map (`persona -> email`) in `.env`, read via `settings.recipient_for_persona(persona)`, resolves each meeting's persona to its own address, falling back to `DEFAULT_RECIPIENT`. All three triggers — on-ready, day-before, and 1-hour reminder — now route to the persona's address, so a Sales Representative meeting's brief goes to the Sales Representative's inbox. The timed sends are refactored to share one `_send_due(guard, window_minutes, subject_fn)` helper, and the whole thing is surfaced: `automation_status()` and the `EmailAutomationStatus` DTO expose `day_before_enabled` / `day_before_minutes` / `personalized`, and the Settings "Automated emails" card shows the day-before line and per-persona routing.

## Stories in this epic
| Key | Story | Points | Priority |
|---|---|---|---|
| SI-16.1 | Day-before trigger + guard column + migration | 5 | High |
| SI-16.2 | Per-persona recipient routing across all triggers | 5 | High |
| SI-16.3 | Automation status + Settings card surfacing | 3 | Medium |

## Epic acceptance criteria
```gherkin
Scenario: Brief is emailed the day before the meeting
  Given a meeting whose brief is ready and that has entered the 24h day-before window
  When the reminder poll loop ticks
  Then the meeting persona's brief is emailed to that persona's recipient address
  And Meeting.day_before_sent_at is stamped so it is not re-sent
```

```gherkin
Scenario: Auto-emails route to the meeting persona
  Given PERSONA_EMAILS maps a persona to an address
  When any trigger (on-ready, day-before, or 1-hour reminder) sends
  Then the email is delivered to that persona's address
  And a persona with no mapping falls back to DEFAULT_RECIPIENT
```

```gherkin
Scenario: On-ready doubles as day-before inside the window
  Given a brief becomes ready while the meeting is already within the 24h window
  When the on-ready send runs
  Then it also stamps day_before_sent_at (and reminder_sent_at when applicable)
  And no near-duplicate day-before email is sent later
```

## Out of scope
- Any new scheduler or job queue — the day-before send rides the existing reminder poll loop.
- Sending more than one email per trigger per meeting (each guard column enforces single-send).
- A per-user address book UI — persona routing is `.env`-configured via `PERSONA_EMAILS`.
- Changing brief content or format per recipient (the persona brief is unchanged).

## Dependencies
- Automated-email feature (on-ready + 1-hour reminder) — the two existing triggers this epic extends.
- Brief generation epic (SI-3) — the persona brief that is delivered.
- Shared contract files `schemas.py` / `contracts.py` / `frontend/src/api/types.ts` (the `EmailAutomationStatus` DTO).
- SQLite `_ADDED_COLUMNS` migration path — reused to add `day_before_sent_at`.

## Verification
- **Backend pytest all green** — day-before sends within the 24h window and are idempotent; skips outside it; on-ready doubles as day-before inside the window; persona routing (fallback to default; a `sales_rep` meeting routes to its persona email via a send-spy); automation-endpoint shape updated.
- **npm build** clean, **Playwright 6/6** — the Settings "Automated emails" card screenshot shows the "Day before ~24h" line.
