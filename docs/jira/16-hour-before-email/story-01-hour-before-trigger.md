# SI-16.1 — 1-hour-before pre-meeting email (windowed + guarded)

| Field | Value |
|---|---|
| Issue type | Story |
| Parent epic | SI-16 — Scheduled 1-Hour-Before Persona Email (+ per-persona routing) |
| Status | Done |
| Priority | High |
| Story points | 3 |
| Component | Brief Delivery |
| Labels | backend, email, automation, config |

## User story
As a sales rep, I want a prospect's brief emailed to me when the meeting is about an hour away, so that I get a final, ready-to-use brief just before I walk into the call.

## Description
This story delivers the **pre-meeting email**: once a meeting's brief is ready, its persona brief is emailed when the meeting's `start_time` is within `REMINDER_LEAD_MINUTES` (default **60** — i.e. the meeting is in about an hour or less). It is config-driven and rides the **existing reminder poll loop** — no new scheduler — so `reminder_loop` runs the pre-meeting send on each tick.

The send is exactly-once via the `Meeting.reminder_sent_at` guard column, stamped when the email goes out. The timed sends share one helper, `_send_due(guard, window_minutes, subject_fn)`; `send_due_reminders()` calls it with the 60-minute window and the `reminder_sent_at` guard, and a "{company} meeting in ~60 min — your brief" subject. When a brief becomes ready while the meeting is already inside the 1-hour window, the on-ready send also stamps `reminder_sent_at`, so a brief that becomes ready less than an hour out doubles as its own pre-meeting email and no near-duplicate is sent later.

> An earlier iteration scheduled this a *day* before the meeting (`DAY_BEFORE_*` config + a `day_before_sent_at` guard). That was a misunderstanding: the intended behaviour is **1 hour before**, so the day-before tier, its config, and its guard column were removed and the pre-meeting send is the 1-hour reminder.

## Acceptance criteria
```gherkin
Scenario: Pre-meeting email sends inside the 1-hour window
  Given a meeting whose brief is ready and whose start_time is within REMINDER_LEAD_MINUTES
  When the reminder poll loop ticks
  Then the meeting's persona brief is emailed
  And Meeting.reminder_sent_at is stamped
```

```gherkin
Scenario: The pre-meeting send is idempotent
  Given a meeting whose reminder_sent_at is already stamped
  When the poll loop ticks again inside the window
  Then no second pre-meeting email is sent
```

```gherkin
Scenario: Outside the window nothing sends
  Given a meeting whose start is more than REMINDER_LEAD_MINUTES away
  When the poll loop ticks
  Then no pre-meeting email is sent
```

```gherkin
Scenario: On-ready doubles as the pre-meeting send inside the window
  Given a brief becomes ready while the meeting is already within the 1-hour window
  When the on-ready send runs
  Then it stamps reminder_sent_at
  And no separate pre-meeting email is sent later
```

## Technical notes (reference)
- Config: `REMINDER_LEAD_MINUTES` (default 60) + `REMINDER_POLL_SECONDS` (60). No day-before config.
- Guard: `Meeting.reminder_sent_at` (existing column) enforces exactly-once.
- Notifier: `_send_due(guard, window_minutes, subject_fn)` shared helper; `send_due_reminders()` uses the 60-minute window + `reminder_sent_at` guard. `reminder_loop` runs it each tick.
- The on-ready send stamps `reminder_sent_at` when already inside the window to prevent a near-duplicate.

## Definition of Done
- [x] The pre-meeting email sends when the meeting is within `REMINDER_LEAD_MINUTES` (60) of start.
- [x] Exactly-once via the `reminder_sent_at` guard; idempotent across poll ticks.
- [x] Nothing sends outside the window.
- [x] On-ready send stamps `reminder_sent_at` when already inside the window (no near-duplicate).
- [x] The mistaken day-before tier (config, guard column, `send_due_day_before`) removed.
- [x] pytest green: sends in-window + idempotent; on-ready doubles as the pre-meeting send.
