# SI-17.3 — Persona-as-default + signed-in sidebar with Sign out

| Field | Value |
|---|---|
| Issue type | Story |
| Parent epic | SI-17 — Demo Login & Persona Selection |
| Status | Done |
| Priority | Medium |
| Story points | 3 |
| Component | App Experience |
| Labels | frontend, ux, auth-demo |

## User story
As a signed-in user, I want the app to show my name and persona and to default new meetings and brief views to my persona, so that the workspace reflects who I am instead of a hardcoded rep.

## Description
This story spends the identity captured at login across the shell. The sidebar `Layout` replaces the old hardcoded **"Rohan M."** with the real signed-in user: their name, their persona, and an **initials avatar** derived via the `initials()` helper from SI-17.1. A labeled **Sign out** button sits alongside it; clicking it calls `logout()`, clears the session, and returns the user to `/login`.

The chosen persona also becomes the default wherever a persona is picked. `MeetingDialog` pre-selects the user's persona when creating a new meeting, so the common case needs no extra clicks. `BriefView` defaults its persona tabs to the user's persona while keeping the tabs fully toggleable — the user can still inspect other personas' briefs, they just start on their own.

The result is that persona is a single source of truth flowing from login into meeting creation and brief viewing, with a clear way to sign out and switch identity.

## Acceptance criteria
```gherkin
Scenario: The sidebar shows the signed-in user
  Given an authenticated session with a name and persona
  When the sidebar renders
  Then it shows the user's name, their persona, and an initials avatar
  And the old hardcoded "Rohan M." is no longer shown
```

```gherkin
Scenario: Sign out returns to login
  Given a signed-in user
  When they click the "Sign out" button
  Then logout() clears the session
  And they are returned to /login
```

```gherkin
Scenario: New meetings default to the user's persona
  Given a signed-in user with a chosen persona
  When they open MeetingDialog to create a meeting
  Then the persona field is pre-selected to the user's persona
```

```gherkin
Scenario: Brief view defaults to the user's persona but stays toggleable
  Given a signed-in user with a chosen persona
  When they open a brief
  Then the persona tabs default to the user's persona
  And the user can still toggle to other personas
```

## Technical notes (reference)
- Key files: the sidebar `Layout`, `frontend/src/components/MeetingDialog.tsx` (or equivalent), `frontend/src/pages/BriefView.tsx`.
- Sidebar: renders `useAuth` name + persona + `initials()` avatar; a labeled Sign out button calls `logout()` and routes to `/login`. Replaces the hardcoded "Rohan M.".
- Defaults: `MeetingDialog` pre-selects the user's persona for new meetings; `BriefView` defaults its persona tabs to the user's persona (still toggleable).

## Definition of Done
- [x] The sidebar shows the signed-in user's name, persona, and initials avatar (no more hardcoded "Rohan M.").
- [x] A labeled Sign out button calls `logout()` and returns to `/login`.
- [x] `MeetingDialog` pre-selects the user's persona for new meetings.
- [x] `BriefView` defaults its persona tabs to the user's persona and remains toggleable.
