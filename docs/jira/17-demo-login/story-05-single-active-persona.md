# SI-17.5 — Single active persona (the signed-in user's role)

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
As a signed-in user, I want the app to operate as my persona only — no switching to other roles and no default "Sales Representative" briefs appearing behind my back — so that everything I see (imports, meetings, brief tabs) is prepared for the one role I actually am.

## Description
This story collapses the app from "many personas, one defaulted" down to a **single active persona** — the signed-in user's. The backend gains a single-row `AppState` table with an `active_persona` column. Sign-in calls the new **`PUT /session/persona`** (session endpoint), which persists the chosen persona as the active one **and** queues generation of that persona's brief across every meeting; **`GET /session/persona`** reads the current active persona back. The frontend login flow calls `setSessionPersona` (this `PUT`) instead of the old bare `POST /briefs/generate` — one call now both sets identity server-side and warms up the briefs.

Persisting the active persona server-side matters because **calendar sync/import runs with no user context**. Import now resolves `get_active_persona()` for the meetings it creates instead of the previously hardcoded `persona="sales_rep"`. So an imported meeting generates **only** the active persona's brief and never a stray default Sales Representative one.

On the client, the persona stops being a *choice* and becomes a *fact*. `BriefView` renders a **single persona tab** — the user's — with no toggle to other personas. `MeetingDialog`'s persona picker grid is replaced by a **read-only "your role" chip**; new meetings are always prepared for the signed-in persona. The net effect is one coherent identity end to end: no persona switcher, no default-Sales-Rep generation, no other personas' tabs.

## Acceptance criteria
```gherkin
Scenario: Login sets the active persona and warms its briefs
  Given a user signs in with a chosen persona
  When PUT /session/persona is called with that persona
  Then AppState.active_persona is set to that persona
  And background generation is queued for that persona's brief across all meetings
```

```gherkin
Scenario: The active persona is readable
  Given an active persona has been set
  When GET /session/persona is called
  Then it returns the current active persona
```

```gherkin
Scenario: Imported meetings use the active persona, not a default
  Given an active persona is persisted in AppState
  When calendar sync imports a meeting server-side
  Then the import uses get_active_persona() for that meeting
  And it generates only the active persona's brief
  And no default "sales_rep" brief is generated
```

```gherkin
Scenario: The workspace shows only the user's persona
  Given a signed-in user with an active persona
  When they open a brief
  Then BriefView shows a single persona tab — their own
  And there is no switcher to other personas
  And MeetingDialog shows a read-only "your role" chip instead of a persona picker grid
```

## Technical notes (reference)
- Backend: single-row `AppState` table with `active_persona`; `PUT /session/persona` sets it **and** queues per-persona brief generation across all meetings; `GET /session/persona` reads it; helper `get_active_persona()`.
- Calendar sync/import (`services`/`api` calendar path) now calls `get_active_persona()` for imported meetings instead of the hardcoded `persona="sales_rep"` — sync runs server-side with no user context, which is why the active persona is persisted.
- Frontend: login flow calls `setSessionPersona` (the `PUT`) in place of the old bare `POST /briefs/generate`. `BriefView` renders a single persona tab (no switching). `MeetingDialog`'s persona picker grid replaced by a read-only "your role" chip.
- Shipped in **PR #19**.

## Definition of Done
- [x] `AppState.active_persona` single-row table; `PUT /session/persona` sets active persona and queues per-persona generation across all meetings; `GET /session/persona` reads it.
- [x] Calendar sync/import uses `get_active_persona()` for imported meetings — no hardcoded `persona="sales_rep"`, no default Sales Representative brief.
- [x] Login flow calls `setSessionPersona` (`PUT /session/persona`) instead of the bare `POST /briefs/generate`.
- [x] `BriefView` shows a single persona tab (the user's) with no persona switching.
- [x] `MeetingDialog`'s persona picker grid replaced by a read-only "your role" chip; new meetings always prepared for the signed-in persona.
- [x] pytest passes: `PUT`/`GET /session/persona` sets active + generates; npm build green; Playwright 7/7 asserts only the user's persona tab is present.
