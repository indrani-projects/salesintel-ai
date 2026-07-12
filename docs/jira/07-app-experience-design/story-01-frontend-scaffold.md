# SI-7.1 — Frontend scaffold (Vite/React/TS/Tailwind, typed API client, TanStack Query)

| Field | Value |
|---|---|
| Issue type | Story |
| Parent epic | SI-7 — Application Experience & Visual Design (Direction C) |
| Status | Done |
| Priority | High |
| Story points | 3 |
| Component | Frontend/UX |
| Labels | frontend, infra |

## User story
As a frontend engineer, I want a modern, type-safe React application scaffold with a shared API client and server-state layer, so that every feature team can build screens against the backend contract without re-solving tooling, data-fetching, or type-safety.

## Description
This story stands up the foundation the entire web app is built on: a Vite + React 19 + TypeScript project styled with Tailwind CSS, wired with React Router for navigation and TanStack Query for server state. It is the "hello, the app runs and talks to the backend" milestone that unblocks all other frontend work.

At the center is a single, thin axios client (`api/client.ts`) that exposes one typed function per backend endpoint — listing companies and meetings, creating/getting/deleting a meeting, fetching and regenerating a brief, reading and posting chat, checking health, and the email preview/send calls. Every function is typed against `api/types.ts`, which hand-mirrors the backend's Pydantic schemas (persona enums, `MeetingRead`, `BriefRead`, `ChatResponse`, and the persona label maps). Because the types are mirrored rather than generated, keeping them in step with the backend schema is a deliberate, documented discipline of this POC.

The client's base URL defaults to `http://localhost:8000` — a deliberate POC shortcut — but reads `VITE_API_URL` when set, so a shared/tunnelled demo can point requests same-origin at `/api` through the Vite dev proxy. TanStack Query provides caching, loading/error states, and the polling primitive that later stories (dashboard, brief view) rely on. The result is a scaffold where any new screen is a few typed calls plus a `useQuery`.

## Acceptance criteria
```gherkin
Scenario: The dev server runs and serves the app
  Given a developer has installed dependencies with npm install
  When they run npm run dev
  Then the Vite dev server starts on port 5173
  And the React application renders in the browser with no type errors
```

```gherkin
Scenario: The typed client reaches the backend
  Given the backend is running on localhost:8000
  When the app calls listMeetings() from api/client.ts
  Then it issues a GET to /meetings and returns a typed MeetingRead array
```

```gherkin
Scenario: The API base URL is overridable for a shared demo
  Given VITE_API_URL is set to "/api"
  When the app makes any API call
  Then requests go same-origin to /api and are proxied to localhost:8000 by Vite
  And when VITE_API_URL is unset the client defaults to http://localhost:8000
```

## Technical notes (reference)
- Key files: `frontend/src/api/client.ts`, `frontend/src/api/types.ts`, `frontend/vite.config.ts`, `frontend/package.json`.
- Stack pinned in `package.json`: React 19, Vite 8, TypeScript ~6, Tailwind 3.4, `@tanstack/react-query` 5, `react-router-dom` 7, axios 1, FullCalendar 6, `lucide-react` icons.
- `api/types.ts` is hand-mirrored from backend `schemas.py` (not codegen) — field names must stay identical across both and the LLM JSON shape.
- POC shortcut: base URL hardcoded to `http://localhost:8000` unless `VITE_API_URL` is set; `vite.config.ts` proxies `/api` → `localhost:8000` and sets `allowedHosts: true` for tunnelled demos.

## Definition of Done
- [x] Vite/React/TS/Tailwind project builds (`npm run build` = `tsc -b && vite build`) and lints (`npm run lint`).
- [x] `api/client.ts` exposes one typed function per backend endpoint, all typed via `api/types.ts`.
- [x] TanStack Query is installed and available for data fetching/polling across the app.
- [x] `VITE_API_URL` override + Vite `/api` proxy verified for shared-demo mode.
