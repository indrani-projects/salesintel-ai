# EPIC SI-16 — Scheduled 1-Hour-Before Persona Email (+ per-persona routing)

| Field | Value |
|---|---|
| Issue type | Epic |
| Suggested key | SI-16 |
| Status | Done |
| Priority | High |
| Component | Brief Delivery |
| Labels | backend, frontend, email, automation, config |
| Story points (rollup) | 11 |

## Summary
Deliver a prospect's **persona brief by email when the meeting is within ~1 hour of its start**, and route every auto-email to a **per-persona** recipient. The scheduled pre-meeting email fires from the existing reminder poll loop when `start_time` is inside `REMINDER_LEAD_MINUTES` (default 60), guarded by an idempotent column, and lands with the *person who owns that persona*. Shipped as PR #15, corrected to the 1-hour window in a follow-up (branch `feat/hour-before-email`).

> **Timing note:** an earlier iteration scheduled this a *day* before the meeting; the intended behaviour is **1 hour before** (send when the meeting is in about an hour or less), so the day-before tier was removed and this epic documents the corrected 1-hour behaviour.

## Description
The automated-email feature fires on two triggers: once when a brief becomes ready, and once as a **pre-meeting send when the meeting is within ~1 hour of its start**. Historically both went to a single default recipient. This epic makes the pre-meeting email carry the persona brief with a clear "your brief" subject, and closes the gap that a real sales workflow exposes — the brief should land with the *person who owns that persona*, not one shared inbox.

The pre-meeting send is **config-driven and idempotent**: `REMINDER_LEAD_MINUTES` (default 60) defines the window, and a `Meeting.reminder_sent_at` guard column ensures a single send. It rides the same reminder poll loop that the app already runs (no new scheduler). When a brief becomes ready while the meeting is already inside the 1-hour window, the on-ready send also stamps `reminder_sent_at` so there is no near-duplicate.

The second change is **per-persona recipient routing**. A `PERSONA_EMAILS` JSON map (`persona -> email`) in `.env`, read via `settings.recipient_for_persona(persona)`, resolves each meeting's persona to its own address, falling back to `DEFAULT_RECIPIENT`. Both triggers — on-ready and the 1-hour pre-meeting send — route to the persona's address, so a Sales Representative meeting's brief goes to the Sales Representative's inbox. The timed sends share one `_send_due(guard, window_minutes, subject_fn)` helper, and it's surfaced: `automation_status()` and the `EmailAutomationStatus` DTO expose `personalized`, and the Settings "Automated emails" card shows the pre-meeting window and per-persona routing.

## Stories in this epic
| Key | Story | Points | Priority |
|---|---|---|---|
| SI-16.1 | 1-hour-before pre-meeting email (windowed + guarded) | 3 | High |
| SI-16.2 | Per-persona recipient routing across all triggers | 5 | High |
| SI-16.3 | Automation status + Settings card surfacing | 3 | Medium |

## Epic acceptance criteria
```gherkin
Scenario: Brief is emailed about an hour before the meeting
  Given a meeting whose brief is ready and whose start_time is within REMINDER_LEAD_MINUTES (60)
  When the reminder poll loop ticks
  Then the meeting persona's brief is emailed to that persona's recipient address
  And Meeting.reminder_sent_at is stamped so it is not re-sent
```

```gherkin
Scenario: Auto-emails route to the meeting persona
  Given PERSONA_EMAILS maps a persona to an address
  When any trigger (on-ready or the 1-hour pre-meeting send) sends
  Then the email is delivered to that persona's address
  And a persona with no mapping falls back to DEFAULT_RECIPIENT
```

```gherkin
Scenario: On-ready doubles as the pre-meeting send inside the window
  Given a brief becomes ready while the meeting is already within the 1-hour window
  When the on-ready send runs
  Then it also stamps reminder_sent_at
  And no near-duplicate pre-meeting email is sent later
```

## Out of scope
- Any new scheduler or job queue — the pre-meeting send rides the existing reminder poll loop.
- A *day-before* email tier — the intended behaviour is 1 hour before, so no separate day-before send exists.
- Sending more than one email per trigger per meeting (the guard column enforces single-send).
- A per-user address book UI — persona routing is `.env`-configured via `PERSONA_EMAILS`.

## Dependencies
- Automated-email feature (on-ready + pre-meeting reminder) — the triggers this epic shapes.
- Brief generation epic (SI-3) — the persona brief that is delivered.
- Shared contract files `schemas.py` / `frontend/src/api/types.ts` (the `EmailAutomationStatus` DTO).

## Verification
- **Backend pytest all green** — the pre-meeting send fires inside the 1-hour window and is idempotent; on-ready doubles as the pre-meeting send inside the window; persona routing (fallback to default; a `sales_rep` meeting routes to its persona email via a send-spy); automation-endpoint shape updated (no day-before fields).
- **npm build** clean, **Playwright 7/7** — the Settings "Automated emails" card shows the pre-meeting window ("within 60 min") and per-persona routing.
