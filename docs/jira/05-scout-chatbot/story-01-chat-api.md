# SI-5.1 — Chat API (post question + per-meeting history)

| Field | Value |
|---|---|
| Issue type | Story |
| Parent epic | SI-5 — Scout Chatbot (Grounded Q&A) |
| Status | Done |
| Priority | Medium |
| Story points | 2 |
| Component | Scout |
| Labels | backend, api |

## User story
As a sales rep, I want my questions to Scout and its answers to be saved against the meeting, so that my conversation persists across reloads and Scout can use earlier turns as context.

## Description
This story delivers the HTTP surface for Scout: two endpoints scoped to a single meeting. `POST /meetings/{meeting_id}/chat` accepts a question, and `GET /meetings/{meeting_id}/chat` returns the full ordered chat history for that meeting.

On a POST, the API first resolves which brief to ground on. It looks up all briefs for the meeting, keeps only those in status `ready` with saved content, and prefers the brief matching the meeting's primary persona — falling back to any ready brief. If no ready brief exists, the request is rejected with `409 Conflict` ("Brief is not ready"), because Scout has nothing to ground on yet. If the meeting itself does not exist, the API returns `404`.

The router is intentionally thin. It validates the stored brief JSON into a `BriefContent`, loads prior `ChatMessage` rows (ordered by creation time) to pass as conversation context, persists the incoming user message, delegates the actual answer generation to the grounded Q&A service (SI-5.2), and then persists Scout's answer. Both the user turn and the assistant turn are written as `ChatMessage` rows in SQLite, keyed by `meeting_id`, giving durable per-meeting history. The endpoint returns the `ChatResponse` (answer markdown, citations, grounded flag) to the caller.

## Acceptance criteria
```gherkin
Scenario: Post a question to a meeting with a ready brief
  Given a meeting whose brief status is "ready"
  When a client POSTs a question to /meetings/{id}/chat
  Then the user message and the assistant answer are both persisted as ChatMessage rows
  And the response contains the answer, its citations, and the grounded flag
```

```gherkin
Scenario: Retrieve per-meeting history in order
  Given several chat messages exist for a meeting
  When a client GETs /meetings/{id}/chat
  Then all messages for that meeting are returned ordered by created_at
```

```gherkin
Scenario: Question before the brief is ready
  Given a meeting whose brief is still pending or generating
  When a client POSTs a question to /meetings/{id}/chat
  Then the API responds 409 Conflict with "Brief is not ready"
  And no assistant answer is generated
```

```gherkin
Scenario: Unknown meeting
  Given no meeting exists with the given id
  When a client POSTs a question to /meetings/{id}/chat
  Then the API responds 404 Not Found
```

## Technical notes (reference)
- Key files: `backend/app/api/chat.py`
- Brief selection prefers the meeting's persona brief, else the first `ready` brief; `content_json` is re-validated into `BriefContent` on read.
- History is loaded and passed to `chat_service.answer_question` before the new user message is persisted, so the model sees prior turns as context.
- DTOs: `ChatRequest`, `ChatResponse`, `ChatMessageRead` from `app.schemas`; persistence via the `ChatMessage` SQLModel table.

## Definition of Done
- [x] `POST /meetings/{meeting_id}/chat` accepts a question and returns a grounded `ChatResponse`
- [x] `GET /meetings/{meeting_id}/chat` returns per-meeting history ordered by creation time
- [x] User and assistant messages persist as `ChatMessage` rows in SQLite
- [x] Returns 404 for unknown meeting and 409 when no `ready` brief exists
- [x] Persona-matched brief is preferred, with fallback to any ready brief
