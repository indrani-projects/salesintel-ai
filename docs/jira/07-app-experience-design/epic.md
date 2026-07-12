# EPIC SI-7 — Application Experience & Visual Design (Direction C)

| Field | Value |
|---|---|
| Issue type | Epic |
| Suggested key | SI-7 |
| Status | Done |
| Priority | Medium |
| Component | Frontend/UX |
| Labels | frontend, ux, design |
| Story points (rollup) | 19 |

## Summary
Build the polished single-page web application shell — scaffold, dark-sidebar layout, "Direction C" design system, live-polling dashboard, and copy/naming pass — that every SalesIntel AI feature lives inside and that makes the demo look premium.

## Description
SalesIntel AI auto-generates a grounded, cited 9-section pre-sales briefing about a prospect. The end-to-end flow is Calendar → Dashboard → Brief → Scout chatbot, demonstrated with the scenario of Zoho selling to "The Sleep Company". This epic owns the **application experience** — the visual container and interaction fabric that the calendar, brief engine, and chatbot all render into. Without it there is no product to show; with it the POC reads as a real, shippable SaaS tool rather than a script with a UI bolted on.

The frontend is a React 19 + Vite + TypeScript + Tailwind single-page app using React Router for navigation, TanStack Query for server state and polling, and FullCalendar for scheduling. A thin, fully-typed axios client (`api/client.ts`) talks to the FastAPI backend, and `api/types.ts` hand-mirrors the backend Pydantic schemas so the whole UI is type-safe against the contract. Three routed pages — Calendar, Dashboard (Briefs), and BriefView — sit inside a persistent app shell with a dark sidebar, brand logo, primary navigation, and a live backend/LLM status footer.

The visual identity is "Direction C": a token/theme system (color, typography, cards, radii, status colors) expressed as Tailwind theme tokens and reusable component classes (`card`, `btn-primary`, `btn-secondary`, status pills, segmented controls). Direction C is applied consistently across every surface — the calendar, the dashboard cards, the brief view's KPI strip / hero / confidence chips, the meeting-creation dialog, and the Scout panel — so the app looks like one designed system. The dashboard cards poll the backend and animate their status pills through pending → generating → ready | error as briefs are produced.

A final copy and naming pass makes the product read as finished: personas are shown with their full-form labels everywhere (Account Executive / Sales Development Rep / Solutions Engineer) instead of raw codes, and the grounded per-account assistant is named "Scout" across the panel, empty states, and input placeholders.

## Stories in this epic
| Key | Story | Points | Priority |
|---|---|---|---|
| SI-7.1 | Frontend scaffold (Vite/React/TS/Tailwind, typed API client, TanStack Query) | 3 | High |
| SI-7.2 | App shell, dark sidebar layout & navigation | 3 | Medium |
| SI-7.3 | Direction C design system (tokens, KPI strip, hero, cards, status pills) | 8 | Medium |
| SI-7.4 | Dashboard status cards + live polling | 3 | High |
| SI-7.5 | Copy & naming pass (full-form persona labels, "Scout") | 2 | Low |

## Epic acceptance criteria
```gherkin
Scenario: The application boots into a polished, navigable shell
  Given the backend is running on localhost:8000
  When a user opens the frontend dev server in a browser
  Then a dark-sidebar app shell renders with the SalesIntel AI logo and Calendar/Briefs navigation
  And routing between Calendar, Briefs, and BriefView works without a full page reload
  And every screen is styled with the Direction C token system
```

```gherkin
Scenario: The dashboard reflects brief generation live
  Given a meeting has just been created and its brief is generating
  When the user is viewing the Briefs dashboard
  Then the meeting's status pill shows "generating"
  And without any manual refresh the pill flips to "ready" once the backend finishes
```

```gherkin
Scenario: Product copy reads as finished
  Given the user is anywhere in the application
  When a persona is displayed
  Then it appears as a full-form label such as "Account Executive"
  And the grounded per-account assistant is labelled "Scout"
```

## Out of scope
- The FullCalendar page's meeting-creation behaviour and calendar wiring (owned by the Calendar/Meetings epic).
- Brief content generation, sectioning, and citations (owned by the Brief Engine epic).
- Scout's grounded question-answering logic and backend chat endpoints (owned by the Chatbot epic).
- Server-side PDF rendering and the email-send feature (separate epics).
- Deploying behind a real domain / auth — the POC hardcodes the API base URL to localhost:8000.

## Dependencies
- Backend API + shared schemas epic (provides `/meetings`, `/companies`, `/health` and the Pydantic DTOs that `api/types.ts` mirrors).
