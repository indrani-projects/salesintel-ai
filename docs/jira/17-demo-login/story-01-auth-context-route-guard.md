# SI-17.1 — Client-side auth context + route guard

| Field | Value |
|---|---|
| Issue type | Story |
| Parent epic | SI-17 — Demo Login & Persona Selection |
| Status | Done |
| Priority | Medium |
| Story points | 5 |
| Component | App Experience |
| Labels | frontend, auth-demo, ux |

## User story
As a user of the demo, I want the app to remember who I am and which persona I picked, and to send me to the login screen when I have not signed in, so that the workspace is always personalized without anyone standing up a real auth system.

## Description
This story introduces the client-only identity layer that every other story in the epic builds on. `frontend/src/lib/auth.tsx` provides an `AuthProvider` and a `useAuth` hook backed entirely by `localStorage` — there is **no server round-trip and no password check**. The stored session is just `{name, persona}`.

The context exposes:

- **`login(name, persona)`** — writes the `{name, persona}` session to `localStorage` and updates context state. The supplied password is accepted but never sent anywhere or validated.
- **`logout()`** — clears the session from `localStorage` and drops context state back to unauthenticated.
- **`initials(name)`** — a helper that derives a compact avatar label from the user's name (used by the sidebar).

`AuthProvider` is wired at the application root in `frontend/src/main.tsx` so the whole tree can read the session. The route guard lives in `frontend/src/App.tsx`: a dedicated `/login` route, plus a `RequireAuth` wrapper around the app routes that redirects any unauthenticated user to `/login`. Because the session is read from `localStorage` on load, a returning user stays signed in across refreshes until they sign out.

## Acceptance criteria
```gherkin
Scenario: Unauthenticated access is redirected
  Given no {name, persona} session exists in localStorage
  When the user navigates to a guarded route
  Then RequireAuth redirects them to /login
```

```gherkin
Scenario: login persists the session
  Given a name and a chosen persona
  When login(name, persona) is called
  Then a {name, persona} object is written to localStorage
  And useAuth reports the user as authenticated
```

```gherkin
Scenario: logout clears the session
  Given an authenticated session
  When logout() is called
  Then the session is removed from localStorage
  And useAuth reports the user as unauthenticated
```

```gherkin
Scenario: Session survives a refresh
  Given a session exists in localStorage
  When the app reloads
  Then AuthProvider restores the session and the user stays signed in
```

## Technical notes (reference)
- Key file: `frontend/src/lib/auth.tsx` — `AuthProvider`, `useAuth`, `login`, `logout`, `initials()`.
- Storage: `localStorage` only; session shape is `{name, persona}`. Password is never checked or stored.
- Root wiring: `AuthProvider` mounted in `frontend/src/main.tsx`.
- Guard: `/login` route + `RequireAuth` wrapper in `frontend/src/App.tsx` redirects unauthenticated users to `/login`.

## Definition of Done
- [x] `lib/auth.tsx` provides `AuthProvider` / `useAuth` backed by `localStorage`.
- [x] `login` / `logout` and an `initials()` helper are implemented; no password verification.
- [x] `AuthProvider` is wired at the root in `main.tsx`.
- [x] `App.tsx` has a `/login` route and a `RequireAuth` guard that redirects unauthenticated users.
- [x] The session survives a page refresh via `localStorage`.
