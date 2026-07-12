# SI-5.3 — Scout chat panel UI

| Field | Value |
|---|---|
| Issue type | Story |
| Parent epic | SI-5 — Scout Chatbot (Grounded Q&A) |
| Status | Done |
| Priority | Medium |
| Story points | 3 |
| Component | Scout |
| Labels | frontend, ux |

## User story
As a sales rep, I want a "Scout" chat panel right next to the brief where I can ask questions and see grounded answers, so that I can dig into the account without leaving the briefing.

## Description
This story delivers the Scout chat panel embedded in the brief view. It presents a branded header ("Scout — Ask anything about this account"), a scrolling message thread, and a composer at the bottom. User messages appear right-aligned in the brand color; Scout answers appear left-aligned and render markdown, so citations and formatting from the grounded service display cleanly.

The panel is meeting-scoped. It loads existing history with TanStack Query (`getChat`) and sends new questions with a mutation (`postChat`), invalidating the history query on success so the new turn and Scout's reply appear. The thread auto-scrolls to the newest message, and while a request is in flight an animated typing indicator is shown. The composer is a growing textarea that sends on Enter (Shift+Enter for newline) and is disabled while a request is pending.

The panel is gated on brief readiness: when passed `disabled`, it shows a "Scout unlocks once the brief is ready" empty state and blocks input, matching the backend's requirement of a `ready` brief. When ready but empty, it shows starter prompts (e.g. "Who led their last round?", "Best opening line?") to guide the rep. Answers detected as ungrounded — via the "not in the sources / no supporting sources / not supported" phrasing — are styled distinctly in amber with an "Not in the sources" warning header, so the rep can instantly see when Scout declined rather than answered.

## Acceptance criteria
```gherkin
Scenario: Ask Scout and see the reply
  Given the brief is ready and the Scout panel is enabled
  When the rep types a question and presses Enter
  Then the question appears in the thread and a typing indicator shows
  And Scout's grounded answer renders as markdown when it returns
```

```gherkin
Scenario: History restored on load
  Given prior messages exist for the meeting
  When the brief view mounts the Scout panel
  Then the existing conversation is fetched and displayed in order
```

```gherkin
Scenario: Ungrounded answer is visually distinct
  Given Scout returns an answer stating it is not in the sources
  When the message renders in the thread
  Then it is shown in the amber "Not in the sources" style with a warning header
```

```gherkin
Scenario: Panel gated until the brief is ready
  Given the brief is not yet ready and the panel is passed disabled
  When the rep views the panel
  Then it shows "Scout unlocks once the brief is ready" and the input is disabled
```

## Technical notes (reference)
- Key files: `frontend/src/components/ChatPanel.tsx`
- Data via TanStack Query: `getChat(meetingId)` for history, `postChat(meetingId, question)` mutation invalidating `["chat", meetingId]`.
- Ungrounded detection is client-side regex on the answer text (`/not in the sources|no supporting sources|not supported/i`) to trigger amber styling.
- Auto-scroll on new messages / pending state; Enter-to-send with Shift+Enter newline; input disabled while `disabled` or a request is pending. Answers rendered via `MarkdownView`.

## Definition of Done
- [x] Scout-branded panel embedded in the brief view with header, thread, and composer
- [x] Loads per-meeting history and posts new questions via TanStack Query
- [x] User vs. assistant bubbles styled distinctly; assistant answers render markdown
- [x] Ungrounded answers shown in an amber "Not in the sources" style
- [x] Disabled/empty/pending states handled (unlock gate, starter prompts, typing indicator)
