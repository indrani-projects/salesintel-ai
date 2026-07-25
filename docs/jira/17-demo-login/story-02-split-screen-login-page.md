# SI-17.2 — Trending split-screen login page

| Field | Value |
|---|---|
| Issue type | Story |
| Parent epic | SI-17 — Demo Login & Persona Selection |
| Status | Done |
| Priority | Medium |
| Story points | 5 |
| Component | App Experience |
| Labels | frontend, ux, auth-demo |

## User story
As a user opening the demo, I want an on-brand login screen where I enter my name, a password, and pick how I want to work, so that entering the workspace feels intentional and sets up my persona from the first click.

## Description
This story delivers `frontend/src/pages/Login.tsx`, a split-screen authentication UI. On one side sits a dark **brand panel** — gradient blobs, the headline *"Walk into every meeting already prepared."*, and a row of persona chips that convey the product's range at a glance. On the other side sits the **form**: a **Name** field, a **Password** field, and a **"Work as persona"** dropdown that surfaces the selected persona's tagline as you change it, capped by a gradient **"Enter workspace"** CTA.

The form is intentionally frictionless because this is a demo gate, **not real auth**. Any password is accepted — nothing is verified. The persona dropdown defaults to **Sales Representative** and lets the user choose any of the six personas; the live tagline gives each choice a bit of context before committing. Submitting calls the auth context's `login(name, persona)` from SI-17.1, which writes the `{name, persona}` session and lets the route guard release the user into the workspace.

The page is styled to match the rest of the product (gradient accents, rounded cards, dark surface) so the login reads as part of the app rather than a bolted-on form.

## Acceptance criteria
```gherkin
Scenario: The login page renders both panels
  Given a user opens /login
  Then a dark brand panel shows the headline and persona chips
  And a form shows Name, Password, and a "Work as persona" dropdown with an "Enter workspace" CTA
```

```gherkin
Scenario: The persona dropdown defaults and describes
  Given the login form
  When the user opens the "Work as persona" dropdown
  Then Sales Representative is pre-selected
  And all six personas are selectable
  And the selected persona's tagline is shown
```

```gherkin
Scenario: Any password is accepted
  Given a name and any password value
  When the user clicks "Enter workspace"
  Then login(name, persona) is called
  And the user is admitted without any password verification
```

## Technical notes (reference)
- Key file: `frontend/src/pages/Login.tsx`.
- Layout: split-screen — dark brand panel (gradient blobs, headline "Walk into every meeting already prepared.", persona chips) beside the form.
- Form: Name, Password (accepted, never checked), "Work as persona" dropdown (default Sales Representative, all six selectable, shows the persona tagline), gradient "Enter workspace" CTA.
- On submit: calls `login(name, persona)` from `lib/auth.tsx`; the `RequireAuth` guard then releases the user into the app.

## Definition of Done
- [x] `Login.tsx` renders a split-screen page: brand panel + form.
- [x] Form has Name, Password, and a "Work as persona" dropdown defaulting to Sales Representative with all six personas.
- [x] The dropdown shows the selected persona's tagline.
- [x] "Enter workspace" CTA calls `login(name, persona)`; any password is accepted.
- [x] Styling is on-brand (gradient blobs / accents, dark surface) and a login screenshot is saved.
