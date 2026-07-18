# SI-10.4 — Settings page & Calendar sync UI

| Field | Value |
|---|---|
| Issue type | Story |
| Parent epic | SI-10 — Google Workspace Integration |
| Status | Done |
| Priority | Medium |
| Story points | 2 |
| Component | Integrations |
| Labels | frontend, ux, google |

## User story
As a sales rep, I want a Settings page where I can connect, check, sync, and disconnect Google, so that I can manage the integration and trigger a calendar sync without touching the API directly.

## Description
This story is the UI for the whole epic. A new `/settings` route renders `Settings.tsx`, which shows the live Google connection status (connected email + scopes) and the three primary actions: **Connect Google** (kicks off the OAuth login redirect), **Sync calendar now** (calls the sync endpoint and reports the `CalendarSyncResult`), and **Disconnect**. The page also handles the post-consent redirect: when it loads with `?google=connected` (or `?google=error`) it reads the flag, shows the corresponding notice, and refreshes status.

The previously **disabled Settings nav item** in `Layout.tsx` is enabled so the page is reachable. For convenience, a **"Sync Google"** button is also added to the Calendar page so the rep can pull calendar events from where they already work. The API client and types are extended with the Google status / sync methods and the `GoogleStatus` / `CalendarSyncResult` shapes mirrored from `schemas.py`.

## Acceptance criteria
```gherkin
Scenario: Settings page shows live connection status
  Given the rep opens /settings
  When the page loads
  Then it fetches Google status and shows whether an account is connected
  And when connected it shows the connected email and granted scopes
```

```gherkin
Scenario: Connect, sync, and disconnect actions
  Given the rep is on the Settings page
  When they click Connect Google
  Then they are sent through the Google OAuth login flow
  And a connected account exposes "Sync calendar now" and "Disconnect" actions
```

```gherkin
Scenario: Post-consent redirect is handled
  Given the OAuth callback redirects back to /settings?google=connected
  When the Settings page loads
  Then it shows a "connected" notice and refreshes status
  And a ?google=error redirect shows an error notice instead
```

```gherkin
Scenario: Sync from the Calendar page
  Given the Settings nav item is enabled and a Sync Google button is on the Calendar page
  When the rep clicks Sync Google on the Calendar page
  Then the calendar sync runs and the imported meetings appear
```

## Technical notes (reference)
- Key files: `frontend/src/pages/Settings.tsx`, `frontend/src/components/Layout.tsx`, `frontend/src/pages/Calendar.tsx`, `frontend/src/api/client.ts`, `frontend/src/api/types.ts`.
- `Settings.tsx`: Connect / Sync calendar now / Disconnect, live status, handles the `?google=connected|error` redirect.
- `Layout.tsx`: enables the previously-disabled Settings nav item.
- `Calendar.tsx`: adds a "Sync Google" button.
- `client.ts` / `types.ts`: Google status + sync methods and the `GoogleStatus` / `CalendarSyncResult` types mirrored from `schemas.py`.

## Definition of Done
- [x] `/settings` route + `Settings.tsx` with Connect / Sync calendar now / Disconnect and live status.
- [x] Handles the `?google=connected|error` post-consent redirect with the right notice.
- [x] Previously-disabled Settings nav item enabled in `Layout.tsx`.
- [x] "Sync Google" button added to the Calendar page.
- [x] `client.ts` / `types.ts` extended with Google status + sync methods and DTOs mirrored from `schemas.py`.
