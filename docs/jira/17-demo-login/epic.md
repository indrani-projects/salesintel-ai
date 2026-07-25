# EPIC SI-17 — Demo Login & Persona Selection

| Field | Value |
|---|---|
| Issue type | Epic |
| Suggested key | SI-17 |
| Status | Done |
| Priority | Medium |
| Component | App Experience |
| Labels | frontend, backend, ux, auth-demo |
| Story points (rollup) | 18 |

## Summary
Add a lightweight login gate — **not real authentication** — that captures the user's name and working persona, personalizes the workspace around them, and warms up that persona's briefs on sign-in. The session is just `{name, persona}` in `localStorage`; there is no server-side auth, no password check, and no tokens.

## Description
Until now the app dropped straight into the workspace with a hardcoded rep ("Rohan M.") and no notion of *who* is using it or *how* they want to work. This epic puts a front door on the demo: a split-screen login page collects a **Name**, **any password** (accepted but never verified), and a **persona** chosen from a dropdown (default **Sales Representative**, all six personas selectable). Those two facts — name and persona — become the identity the rest of the app dresses itself in.

The gate is deliberately a **personalization layer, not a security layer**. A client-side auth context (`AuthProvider` / `useAuth`) persists the session in `localStorage`, exposes `login` / `logout` and an `initials()` helper, and is wired at the root in `main.tsx`. A `RequireAuth` route guard in `App.tsx` bounces unauthenticated visitors to `/login`. Once signed in, the persona threads through the product: the sidebar shows the user's name, persona, and an initials avatar with a labeled **Sign out** button; `MeetingDialog` pre-selects the user's persona for new meetings; and `BriefView` defaults its persona tabs to the user's choice while remaining toggleable.

To make the workspace feel ready the instant the user lands, sign-in also fires `POST /briefs/generate?persona=` (backend `generate_persona_briefs`), which queues background generation of that persona's brief for **every** meeting, idempotently — meetings already `ready` for that persona are skipped. So by the time the user opens a meeting, the brief for their persona is already being prepared. The intelligence in this epic is entirely in the *experience seam* — a client auth context (SI-17.1), an on-brand login page (SI-17.2), persona-as-default personalization (SI-17.3), and login-triggered brief warm-up (SI-17.4). No real credentials are introduced anywhere.

## Stories in this epic
| Key | Story | Points | Priority |
|---|---|---|---|
| SI-17.1 | Client-side auth context + route guard | 5 | Medium |
| SI-17.2 | Trending split-screen login page | 5 | Medium |
| SI-17.3 | Persona-as-default + signed-in sidebar with Sign out | 3 | Medium |
| SI-17.4 | Auto-generate the selected persona's briefs on login | 5 | Medium |

## Epic acceptance criteria
```gherkin
Scenario: An unauthenticated user is gated to login
  Given no session exists in localStorage
  When the user opens any app route
  Then they are redirected to /login
  And they cannot reach the workspace until they enter a name and persona
```

```gherkin
Scenario: Signing in personalizes the workspace
  Given a user enters a name, any password, and picks a persona
  When they click "Enter workspace"
  Then a {name, persona} session is stored in localStorage
  And the sidebar shows their name, persona, and initials avatar
  And new meetings and brief views default to their persona
```

```gherkin
Scenario: Sign-in warms up the persona's briefs
  Given the user has signed in with a chosen persona
  When the session is created
  Then background generation is queued for that persona's brief on every meeting
  And meetings already ready for that persona are skipped
```

```gherkin
Scenario: Signing out clears the session
  Given a signed-in user
  When they click "Sign out"
  Then the session is cleared from localStorage
  And they are returned to /login
```

## Out of scope
- **Any real authentication.** There is no backend auth, no password verification, no credential store, no session tokens or cookies, and no RBAC — this is a demo personalization gate only.
- User accounts, sign-up, password reset, or multi-user isolation.
- Server-side enforcement of the persona (the persona is a UI/default hint, not an authorization boundary).
- Persisting the session anywhere other than the browser's `localStorage`.

## Dependencies
- Persona/brief epics (SI-3 and the persona work) — supplies the persona list and the per-persona brief generation this epic triggers.
- Shared contract files `schemas.py` / `contracts.py` / `frontend/src/api/types.ts`.
- Frontend shell — `main.tsx`, `App.tsx`, the sidebar `Layout`, `MeetingDialog`, and `BriefView`.

## Verification
- **Backend pytest** `test_generate_briefs_for_persona` — `POST /briefs/generate?persona=` returns 202 and the persona's brief becomes `ready` with its 6 sections.
- **Playwright 7/7** — existing tests seed the demo auth; a new login-flow test fills name/password, picks a persona, clicks "Enter workspace" → lands on the app, then "Sign out" → back to `/login`.
- **npm build** clean; login screenshot saved.
- Shipped as **PR #16** (branch `feat/login`).
