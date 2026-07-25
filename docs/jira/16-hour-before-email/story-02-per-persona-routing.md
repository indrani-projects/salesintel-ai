# SI-16.2 — Per-persona recipient routing across all triggers

| Field | Value |
|---|---|
| Issue type | Story |
| Parent epic | SI-16 — Scheduled 1-Hour-Before Persona Email (+ per-persona routing) |
| Status | Done |
| Priority | High |
| Story points | 5 |
| Component | Brief Delivery |
| Labels | backend, email, automation, config |

## User story
As a sales team, we want each meeting's brief delivered to the address of the persona it targets, so that the Sales Representative gets the Sales Representative's brief and no one has to forward from a shared inbox.

## Description
This story routes every auto-email to a **per-persona** recipient instead of one shared default. A `PERSONA_EMAILS` map — a JSON `persona -> email` object in `.env` — is read via `settings.recipient_for_persona(persona)`, which returns that persona's address when present and otherwise falls back to `DEFAULT_RECIPIENT`.

**Both** triggers now route through this resolver: the on-ready send and the 1-hour pre-meeting send (SI-16.1). Each looks up the meeting's persona and delivers to that persona's address. For example, a Sales Representative meeting's brief is emailed to the Sales Representative's configured email; a persona with no `PERSONA_EMAILS` entry cleanly falls back to `DEFAULT_RECIPIENT`, so nothing is ever dropped for an unmapped persona.

Because the shared `_send_due(guard, window_minutes, subject_fn)` helper and the on-ready path both resolve the recipient the same way, routing is consistent across triggers with no per-trigger special-casing. Verification uses a send-spy: a `sales_rep` meeting is confirmed to route to its persona email, and an unmapped persona is confirmed to fall back to the default.

## Acceptance criteria
```gherkin
Scenario: A persona brief routes to that persona's address
  Given PERSONA_EMAILS maps "sales_rep" to an address
  When any trigger sends a sales_rep meeting's brief
  Then the email is delivered to the sales_rep address
```

```gherkin
Scenario: Unmapped persona falls back to default
  Given a meeting persona has no entry in PERSONA_EMAILS
  When a trigger sends that meeting's brief
  Then the email is delivered to DEFAULT_RECIPIENT
```

```gherkin
Scenario: Routing is consistent across both triggers
  Given a persona is mapped in PERSONA_EMAILS
  When the on-ready and 1-hour pre-meeting triggers each send
  Then both deliver to that persona's address
```

## Technical notes (reference)
- Config: `PERSONA_EMAILS` — JSON `persona -> email` object in `.env`.
- Resolver: `settings.recipient_for_persona(persona)` returns the persona's address, else `DEFAULT_RECIPIENT`.
- Both triggers (on-ready, 1-hour pre-meeting) resolve the recipient the same way — no per-trigger special-casing.
- Verified with a send-spy: a `sales_rep` meeting routes to its persona email; an unmapped persona falls back to the default.

## Definition of Done
- [x] `PERSONA_EMAILS` JSON map added to config.
- [x] `settings.recipient_for_persona(persona)` returns the persona address or `DEFAULT_RECIPIENT`.
- [x] On-ready and the 1-hour pre-meeting trigger both route to the persona address.
- [x] Unmapped persona falls back to `DEFAULT_RECIPIENT`.
- [x] pytest green: send-spy confirms `sales_rep` routes to its persona email; fallback confirmed.
