# SI-2.4 — Calendar UI (FullCalendar)

| Field | Value |
|---|---|
| Issue type | Story |
| Parent epic | SI-2 — Calendar & Meeting Management |
| Status | Done |
| Priority | High |
| Story points | 3 |
| Component | Meetings |
| Labels | frontend, ux |

## User story
As a sales rep, I want to see my meetings on a familiar calendar and add a new one by clicking a day, so that scheduling a prospect (and triggering its briefing) fits into how I already work.

## Description
The calendar is the product's front door. Rather than inventing a new surface, SalesIntel AI meets the rep where they already live — a month calendar. This story renders that calendar using FullCalendar, populates it with the rep's meetings fetched from `GET /meetings`, and makes each day clickable to start creating a meeting there.

When the rep clicks a day, the add-meeting dialog opens pre-seeded with that date, so the "time" field starts from the day they picked. Existing meetings appear as calendar events, giving the rep an at-a-glance view of their prospect pipeline. Because meetings are fetched with TanStack Query, the calendar stays in sync as meetings are created or deleted, and newly added meetings appear without a manual refresh.

The calendar is intentionally the launch point for the whole flow: adding a meeting here is what persists it and auto-kicks off brief generation (SI-2.3). From the rep's perspective, one click on a day and a short form is all it takes for a fully researched briefing to start assembling itself in the background.

## Acceptance criteria
```gherkin
Scenario: Calendar shows existing meetings
  Given the rep has meetings on their calendar
  When the Calendar page loads
  Then each meeting is rendered as an event on its start date
```

```gherkin
Scenario: Clicking a day opens the add-meeting dialog
  Given the rep is viewing the calendar
  When they click on a day
  Then the add-meeting dialog opens
  And it is pre-seeded with the clicked date
```

```gherkin
Scenario: A newly added meeting appears without a manual refresh
  Given the rep saves a new meeting from the dialog
  When the calendar's meeting query invalidates
  Then the new meeting appears as an event on the calendar automatically
```

## Technical notes (reference)
- Key files: `frontend/src/pages/Calendar.tsx` (FullCalendar render, `dateClick` handler, meetings query), `frontend/src/components/MeetingDialog.tsx` (opened from the calendar)
- Meetings are fetched via TanStack Query against `GET /meetings`; creating/deleting a meeting invalidates the query so the grid re-renders.
- The clicked date is passed into the dialog to seed the start time.

## Definition of Done
- [x] FullCalendar renders in the Calendar page
- [x] Existing meetings render as events fetched from `GET /meetings`
- [x] Clicking a day opens the add-meeting dialog seeded with that date
- [x] The calendar reflects created/deleted meetings without a manual refresh
