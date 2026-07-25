# SI-17.6 — Clear Scout chat history on login

| Field | Value |
|---|---|
| Issue type | Story |
| Parent epic | SI-17 — Demo Login & Persona Selection |
| Status | Done |
| Priority | Medium |
| Story points | 2 |
| Component | App Experience |
| Labels | backend, frontend, auth-demo, api |

## User story
As a user signing in for a fresh session, I want the Scout assistant to start with an empty chat, so that I never inherit a previous session's conversation and every login begins clean.

## Description
This story makes each login reset the Scout assistant. The same **`PUT /session/persona`** call that sign-in already makes (SI-17.5) also **deletes all `ChatMessage` rows server-side**, so the persisted chat history is wiped as the active persona is set. On the client, the login flow drops the `["chat"]` query cache so any in-memory chat state is cleared to match the server.

The result is that signing in gives a fresh Scout — no leftover Q&A from an earlier session on either side of the wire. This is intentionally coupled to the login/session endpoint so there is a single, predictable moment where chat is reset.

## Acceptance criteria
```gherkin
Scenario: Login clears persisted chat history
  Given a meeting has existing Scout chat messages
  When PUT /session/persona is called on login
  Then all ChatMessage rows are deleted server-side
  And that meeting's chat history is empty
```

```gherkin
Scenario: The client cache is dropped on login
  Given the frontend holds a ["chat"] query cache
  When the login flow runs
  Then the ["chat"] query cache is dropped
  And Scout starts with a fresh, empty conversation
```

## Technical notes (reference)
- Backend: `PUT /session/persona` deletes all `ChatMessage` rows as part of setting the active persona.
- Frontend: login flow invalidates/drops the `["chat"]` query cache so client state matches the cleared server state.
- Verified by pytest — a login (via `PUT /session/persona`) empties a meeting's chat history.
- Shipped in **PR #19**.

## Definition of Done
- [x] `PUT /session/persona` deletes all `ChatMessage` rows server-side.
- [x] The login flow drops the client-side `["chat"]` query cache.
- [x] Each login starts with a fresh Scout assistant (no leftover conversation).
- [x] pytest passes: a login empties a meeting's chat history.
