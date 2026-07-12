# SI-7.4 — Dashboard status cards + live polling

| Field | Value |
|---|---|
| Issue type | Story |
| Parent epic | SI-7 — Application Experience & Visual Design (Direction C) |
| Status | Done |
| Priority | High |
| Story points | 3 |
| Component | Frontend/UX |
| Labels | frontend, ux |

## User story
As a sales rep, I want the Briefs dashboard to show a card per meeting whose status updates on its own, so that I can watch a brief go from queued to ready without refreshing and open it the moment it's done.

## Description
The Briefs dashboard is the home base of the app: a responsive grid of cards, one per meeting, each showing the meeting and the live status of its brief. Because brief generation is asynchronous on the backend (a background job moving through pending → generating → ready | error), the dashboard's job is to reflect that state machine truthfully and in real time.

It does this with TanStack Query polling. The meetings query uses a smart `refetchInterval`: while any meeting on the board is still in an active state (pending/generating) it re-fetches every four seconds; once everything has settled to ready or error, polling stops entirely to avoid needless traffic. A header summary counts how many briefs are "generating…" with a spinner, and a manual Refresh button is available for impatience. Meetings are sorted newest-first so the just-created one appears at the top.

The screen also handles its non-happy paths as designed states rather than blank space: a skeleton-card grid while the first load is in flight, a friendly error card (with a retry) when the backend at localhost:8000 can't be reached, and a rich empty state prompting the user to create their first meeting. New meetings are created from here via the meeting dialog, closing the loop from dashboard to calendar to brief.

## Acceptance criteria
```gherkin
Scenario: A card flips status without a manual refresh
  Given a meeting whose brief is generating is on the dashboard
  When the backend finishes generating the brief
  Then within one poll cycle the card's status pill changes to "ready"
  And no manual refresh was required
```

```gherkin
Scenario: Polling stops when nothing is active
  Given every brief on the dashboard is ready or error
  When the dashboard is idle
  Then the meetings query stops its polling interval
  And it resumes 4s polling as soon as a new active brief appears
```

```gherkin
Scenario: The dashboard handles empty and error states
  Given the user has created no meetings
  When the dashboard loads
  Then a styled empty state invites them to create their first meeting
  And if the backend is unreachable a friendly error card with a "Try again" retry is shown instead
```

## Technical notes (reference)
- Key files: `frontend/src/pages/Dashboard.tsx`, `frontend/src/components/BriefCard.tsx`, `frontend/src/components/MeetingDialog.tsx`, `frontend/src/lib/format.ts` (`isActiveStatus`).
- Polling: `useQuery({ queryKey: ["meetings"], queryFn: listMeetings, refetchInterval })` where the interval returns `4000` when any `m.brief_status` is active, else `false`.
- Status values mirror the backend `BriefStatus` enum: `pending` / `generating` / `ready` / `error`; the header shows an animated "N generating…" count.
- Newest-first sort by `start_time`; skeleton grid on `isLoading`, error card on `isError`, empty state when `sorted.length === 0`.

## Definition of Done
- [x] Dashboard renders one status card per meeting in a responsive grid, sorted newest-first.
- [x] Cards reflect pending → generating → ready | error and update live via TanStack Query polling.
- [x] Polling runs only while a brief is active and stops once all settle.
- [x] Loading skeletons, unreachable-backend error card (with retry), and empty state all implemented.
