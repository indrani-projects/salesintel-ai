# SI-16.1 — Day-before trigger + guard column + migration

| Field | Value |
|---|---|
| Issue type | Story |
| Parent epic | SI-16 — Scheduled Day-Before Persona Email (+ per-persona routing) |
| Status | Done |
| Priority | High |
| Story points | 5 |
| Component | Brief Delivery |
| Labels | backend, email, automation, config |

## User story
As a sales rep, I want a prospect's brief emailed to me roughly a day before the meeting, so that I can prepare the night before instead of scrambling in the hour before the call.

## Description
This story adds a **third automated-email trigger** that fires ~1 day before a meeting, once its brief is ready. It is config-driven: `DAY_BEFORE_EMAIL_ENABLED` (default true) turns it on, and `DAY_BEFORE_LEAD_MINUTES` (1440 = 24h) sets the window. The send rides the **existing reminder poll loop** — no new scheduler — so `reminder_loop` now runs the day-before send and the 1-hour reminder on each tick.

To make the send exactly-once, a new `Meeting.day_before_sent_at` guard column is added and stamped when the day-before email goes out. The column is created through the existing `_ADDED_COLUMNS` SQLite migration path, so an existing database picks it up idempotently with no reset.

The timed sends are refactored to share one helper, `_send_due(guard, window_minutes, subject_fn)`. `send_due_day_before()` calls it with the 24h window and the `day_before_sent_at` guard; `send_due_reminders()` calls it with the 60m window and the `reminder_sent_at` guard. Crucially, the on-ready send also stamps `day_before_sent_at` (and `reminder_sent_at`) when the meeting is already inside those windows — so a brief that becomes ready less than a day out doubles as its own day-before email and no near-duplicate is sent later.

## Acceptance criteria
```gherkin
Scenario: Day-before email sends inside the 24h window
  Given a meeting whose brief is ready and that is within DAY_BEFORE_LEAD_MINUTES of start
  When the reminder poll loop ticks
  Then the meeting's persona brief is emailed
  And Meeting.day_before_sent_at is stamped
```

```gherkin
Scenario: The day-before send is idempotent
  Given a meeting whose day_before_sent_at is already stamped
  When the poll loop ticks again inside the window
  Then no second day-before email is sent
```

```gherkin
Scenario: Outside the window nothing sends
  Given a meeting whose start is more than DAY_BEFORE_LEAD_MINUTES away
  When the poll loop ticks
  Then no day-before email is sent
```

```gherkin
Scenario: On-ready doubles as day-before inside the window
  Given a brief becomes ready while the meeting is already within the 24h window
  When the on-ready send runs
  Then it stamps day_before_sent_at
  And no separate day-before email is sent later
```

## Technical notes (reference)
- Config: `DAY_BEFORE_EMAIL_ENABLED` (default true) + `DAY_BEFORE_LEAD_MINUTES` (1440).
- Model: new `Meeting.day_before_sent_at` column; added via the existing `_ADDED_COLUMNS` SQLite migration path (idempotent, no reset).
- Notifier: `_send_due(guard, window_minutes, subject_fn)` shared helper; `send_due_day_before()` uses the 24h window + `day_before_sent_at` guard.
- `reminder_loop` runs day-before + reminder each tick; the on-ready send also stamps `day_before_sent_at`/`reminder_sent_at` when already inside those windows to prevent near-duplicates.

## Definition of Done
- [x] `DAY_BEFORE_EMAIL_ENABLED` + `DAY_BEFORE_LEAD_MINUTES` (1440) config added.
- [x] `Meeting.day_before_sent_at` guard column added via the `_ADDED_COLUMNS` migration path (idempotent).
- [x] `send_due_day_before()` sends inside the 24h window and is exactly-once via the guard.
- [x] `reminder_loop` runs the day-before send alongside the 1-hour reminder each tick.
- [x] On-ready send stamps `day_before_sent_at` when already inside the window (no near-duplicate).
- [x] pytest green: sends in-window + idempotent; skips out-of-window; on-ready doubles as day-before.
