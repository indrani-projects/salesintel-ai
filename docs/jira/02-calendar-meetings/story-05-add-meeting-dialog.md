# SI-2.5 — Add-meeting dialog (subject, company, why, agenda, persona, time)

| Field | Value |
|---|---|
| Issue type | Story |
| Parent epic | SI-2 — Calendar & Meeting Management |
| Status | Done |
| Priority | High |
| Story points | 3 |
| Component | Meetings |
| Labels | frontend, ux |

## User story
As a sales rep, I want a short dialog to describe my meeting — including why I'm meeting and what I want to cover — so that the briefing that gets generated is tailored to my actual angle, not a generic company summary.

## Description
This is the form the rep fills in to create a meeting, and it is where the product's intelligence is seeded. The dialog collects six fields: the meeting subject, the prospect company (a seeded dropdown of known prospects that also accepts free text, per SI-2.2), a free-text "why" (why the rep is meeting this prospect), a free-text "agenda" (what they want to cover), the target persona (AE / SDR / SE), and the start time. On save it POSTs to `/meetings`, which persists the meeting and auto-triggers brief generation.

The "why" and "agenda" fields are the differentiator. They are injected verbatim into the LLM prompt, and they shift the emphasis of the generated brief — for example, an agenda mentioning "scaling support" pulls Zoho Desk to the foreground of the recommendations. This is what makes the brief feel intelligent and bespoke rather than a templated dump, and it is the demo's proof that real synthesis is happening. The persona choice similarly tailors the framing (an AE brief reads differently from an SDR brief).

The dialog is designed for speed: it opens pre-seeded with the date the rep clicked on the calendar, defaults sensible values, and validates that the required fields are present before enabling save. After a successful save it closes and the calendar refreshes to show the new meeting, whose brief is already generating in the background.

## Acceptance criteria
```gherkin
Scenario: Submit a complete meeting
  Given the add-meeting dialog is open with a seeded date
  When the rep fills in subject, company, why, agenda, persona, and time and saves
  Then a POST /meetings is sent with all six fields
  And the dialog closes and the calendar shows the new meeting
```

```gherkin
Scenario: Why and agenda shape the brief
  Given the rep enters an agenda of "scaling customer support"
  When the meeting is created and its brief generates
  Then the why and agenda are passed into brief generation
  And the resulting brief emphasizes the matching Zoho product angle (e.g. Zoho Desk)
```

```gherkin
Scenario: Required fields are validated before save
  Given the rep leaves the subject or company empty
  When they attempt to save
  Then save is blocked until the required fields are provided
```

## Technical notes (reference)
- Key files: `frontend/src/components/MeetingDialog.tsx` (form fields, validation, submit), `backend/app/schemas.py` (`MeetingCreate`, `Persona`), `backend/app/api/meetings.py` (`create_meeting`)
- The `why` and `agenda` strings flow through `create_meeting` into `brief_engine.generate_brief(...)`, which injects them into the LLM prompt to shift emphasis — the demo's proof that synthesis is real.
- Persona is one of AE / SDR / SE and becomes the meeting's primary persona (drives which brief generates first).
- The dialog is seeded with the date clicked on the calendar (SI-2.4).

## Definition of Done
- [x] Dialog collects subject, company, why, agenda, persona, and start time
- [x] Company field is a seeded dropdown that also accepts free text
- [x] Save POSTs `MeetingCreate` to `/meetings` and closes on success
- [x] `why` / `agenda` are carried into brief generation to shift emphasis
- [x] Required fields are validated before save is allowed
