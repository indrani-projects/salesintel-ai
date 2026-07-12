# SI-7.2 — App shell, dark sidebar layout & navigation

| Field | Value |
|---|---|
| Issue type | Story |
| Parent epic | SI-7 — Application Experience & Visual Design (Direction C) |
| Status | Done |
| Priority | Medium |
| Story points | 3 |
| Component | Frontend/UX |
| Labels | frontend, ux |

## User story
As a sales rep using SalesIntel AI, I want a persistent app shell with a clear sidebar and navigation, so that I always know where I am, can move between the calendar and my briefs in one click, and can see at a glance whether the system is online.

## Description
This story delivers the persistent chrome that wraps every page: a dark left sidebar containing the branded SalesIntel AI logo (a radar-glyph mark), the primary navigation, and a footer that shows the signed-in rep plus live system status. The main content region renders the active route via React Router's `Outlet`, so navigating between screens swaps only the page body — the shell stays put and there is no full-page reload.

Navigation lists Calendar and Briefs as active destinations, with Accounts and Settings shown as visibly disabled "coming soon" items to communicate product scope without dead links. The active route is highlighted with the brand accent. The layout is responsive: on wide viewports it is a fixed-width sidebar beside the content grid; below the breakpoint the sidebar collapses into a compact top bar with a horizontal nav so the app remains usable on smaller screens.

The sidebar footer doubles as a lightweight system monitor. It polls the backend `/health` endpoint on an interval and renders a status line — "Backend connected / offline" and "LLM on / off" — alongside the demo rep's identity (Rohan M., Account Executive). This gives the demo a truthful, always-visible signal of whether the backend and LLM key are wired up, which is invaluable when presenting live.

## Acceptance criteria
```gherkin
Scenario: The shell persists across navigation
  Given the user is on the Briefs dashboard
  When they click Calendar in the sidebar
  Then the Calendar page renders in the content area
  And the sidebar, logo, and navigation remain in place without a full page reload
  And the Calendar nav item is shown as active
```

```gherkin
Scenario: System status is visible in the sidebar footer
  Given the backend is reachable and an LLM key is configured
  When the shell polls the health endpoint
  Then the footer shows "Backend connected" and "LLM on"
  And when the backend is unreachable it shows "Backend offline"
```

```gherkin
Scenario: The shell adapts to small screens
  Given the viewport is narrower than the desktop breakpoint
  When the app renders
  Then the sidebar collapses into a compact top bar with horizontal navigation
  And disabled "coming soon" items are hidden from the mobile nav
```

## Technical notes (reference)
- Key files: `frontend/src/components/Layout.tsx`, plus the React Router route tree (`App.tsx`/router entry) that renders `<Layout>` with an `<Outlet>`.
- Nav items defined as a typed `NavItem[]`; `Accounts` and `Settings` carry `disabled: true` and render as non-link "coming soon" rows.
- Footer status uses TanStack Query against `getHealth()` (`/health`) with `refetchInterval: 15000`, `retry: false`; `online` and `llm_configured` drive the dots.
- Responsive: CSS grid `[236px_1fr]` at the `min-[960px]` breakpoint; below it a `bg-nav` top bar renders the compact logo + horizontal nav.

## Definition of Done
- [x] Persistent dark-sidebar `Layout` renders logo, primary nav, and status footer around a routed `<Outlet>`.
- [x] Calendar and Briefs navigate client-side with active-state highlighting; Accounts/Settings shown as disabled.
- [x] Health-polling footer reflects backend + LLM status live.
- [x] Responsive collapse to a mobile top bar verified.
