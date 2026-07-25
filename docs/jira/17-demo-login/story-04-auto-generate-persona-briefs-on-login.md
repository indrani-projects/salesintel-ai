# SI-17.4 — Auto-generate the selected persona's briefs on login

| Field | Value |
|---|---|
| Issue type | Story |
| Parent epic | SI-17 — Demo Login & Persona Selection |
| Status | Done |
| Priority | Medium |
| Story points | 5 |
| Component | App Experience |
| Labels | backend, frontend, auth-demo, api |

## User story
As a user who just signed in with a persona, I want that persona's briefs to start generating for every meeting in the background, so that the briefs are ready as I browse instead of me waiting for each one on demand.

## Description
This story warms up the workspace at sign-in. Generation queues **background** work for the signed-in persona's brief for **every** meeting. The operation is **idempotent**: any meeting already `ready` for that persona is skipped, so repeated sign-ins or repeated calls never duplicate work or re-run generation that is already complete. The trigger returns immediately (202) while the work proceeds via the existing background-task mechanism.

Login now warms briefs through the **session endpoint `PUT /session/persona`** rather than the bare `POST /briefs/generate`. As part of SI-17.5, `PUT /session/persona` sets the signed-in user's **active persona** server-side **and** queues that persona's generation across all meetings — one call that both establishes identity and warms the workspace. The underlying fan-out endpoint `POST /briefs/generate?persona=` (`generate_persona_briefs` in `meetings.py`) still exists and is reused internally; login just no longer calls it bare.

The frontend calls `PUT /session/persona` from the sign-in flow (SI-17.1 / SI-17.2), passing the user's chosen persona. By the time the user navigates to a meeting, that persona's brief is already being prepared or done. This reuses the existing per-persona brief generation path — no new synthesis logic — it simply fans the trigger across all meetings at login.

## Acceptance criteria
```gherkin
Scenario: Login queues persona briefs for every meeting
  Given the user signs in with a chosen persona
  When PUT /session/persona is called with that persona
  Then it sets the active persona and returns success
  And background generation is queued for that persona's brief on every meeting
```

```gherkin
Scenario: Already-ready meetings are skipped
  Given some meetings already have a ready brief for the persona
  When generate_persona_briefs runs
  Then those meetings are skipped
  And only the missing persona briefs are generated
```

```gherkin
Scenario: The persona brief becomes ready with its sections
  Given generation is queued for a persona
  When a meeting's brief finishes generating
  Then the brief for that persona becomes ready
  And it renders its six sections
```

## Technical notes (reference)
- Login trigger: `PUT /session/persona` (SI-17.5) sets the active persona **and** queues per-persona generation across all meetings; this is what the sign-in flow calls.
- Underlying fan-out: `POST /briefs/generate?persona=` → `generate_persona_briefs` in `backend/app/api/meetings.py`; queues background generation for that persona across all meetings, idempotently (skips meetings already ready for the persona); returns 202. Still exists and reused internally — login no longer calls it bare.
- Frontend: sign-in flow calls `setSessionPersona` (`PUT /session/persona`) with the user's persona so briefs warm up as the user browses.
- Reuses the existing per-persona brief generation path — no new synthesis call.
- Verified by backend pytest `test_generate_briefs_for_persona` (persona brief becomes ready with its 6 sections).

## Definition of Done
- [x] Login warms briefs via `PUT /session/persona`, which sets the active persona and queues generation of that persona's brief for every meeting.
- [x] The underlying `POST /briefs/generate?persona=` (`generate_persona_briefs`) fan-out still exists and is reused internally.
- [x] The operation is idempotent — meetings already ready for that persona are skipped.
- [x] Generation runs via the existing background task.
- [x] The sign-in flow calls `setSessionPersona` (`PUT /session/persona`) with the user's chosen persona.
- [x] `test_generate_briefs_for_persona` passes: the persona brief becomes ready with its 6 sections.
