# SI-8.3 — Frontend E2E suite (Playwright + screenshots)

| Field | Value |
|---|---|
| Issue type | Story |
| Parent epic | SI-8 — Quality, Testing & Demo Readiness |
| Status | Done |
| Priority | High |
| Story points | 5 |
| Component | Quality |
| Labels | frontend, testing, qa |

## User story
As a developer preparing for a live demo, I want Playwright specs that click through the real UI against fresh mock servers and capture screenshots, so that I can prove the whole front-to-back flow works and have visual evidence of every demo screen.

## Description
Backend tests prove the API, but the demo is judged on the UI: the calendar, the create-meeting dialog, the dashboard status cards, the 9-section brief with its KPI strip, the persona toggle, the Scout chat panel, and the send-as-email dialog. This story adds four Playwright specs that drive the actual React app end to end, so a green run means the demo path genuinely works in a browser — not just at the API boundary.

The Playwright config boots a **fresh** backend in `MOCK_LLM`/`MOCK_EMAIL` mode on port 8000 (its own throwaway SQLite DB) and the Vite dev server on 5173, with `reuseExistingServer: false` so the backend under test is always the mock one. Runs are serial (`workers: 1`, `fullyParallel: false`) with `screenshot: "on"`, so each step leaves an artifact.

The four specs are: (1) **app shell** — the workspace nav and the "New meeting" button render; (2) **create meeting via dialog** — fill subject/company/why/agenda in the dialog, submit, then confirm the new Sleep Company AE card on the dashboard; (3) **brief view** — open a seeded meeting, assert the AE brief heading, the "Account Executive · Pre-Call Brief" label, the KPI strip (ARR / ₹700 Cr), an AE-only section (Pain Hypotheses), and the "Ready · N source" badge, then toggle to SDR (Ready-to-Send Opener) and SE (Demo Focus) and confirm the distinct section sets, then ask Scout a grounded question and confirm the mock grounded answer appears; (4) **send-as-email** — open the email dialog from the brief toolbar, confirm the recipient is prefilled and the persona digest + `-ae-brief.html` attachment + "Demo mode" preview render, confirm send, and confirm "Demo send complete". A `seedMeeting()` helper posts a meeting straight to the mock API to set up specs that start on the brief page. Screenshots 01–09 are written to `e2e/screenshots/`.

## Acceptance criteria
```gherkin
Scenario: The demo path is green in a real browser against mock servers
  Given the Playwright config boots fresh MOCK_LLM/MOCK_EMAIL backend and Vite servers
  When the four specs run
  Then the app shell, create-meeting dialog, brief render, persona toggle, Scout, and email demo-send all pass
  And screenshots 01 through 09 are captured to e2e/screenshots
```

```gherkin
Scenario: Persona toggle swaps the section set live in the UI
  Given a seeded AE brief is open
  When the user toggles to the SDR then the SE persona
  Then the SDR "Ready-to-Send Opener" and the SE "Demo Focus" headings appear
  And the AE-only "Pain Hypotheses" section is no longer the active set
```

```gherkin
Scenario: Edge case — the mock backend is always the one under test
  Given a developer left a real backend running on port 8000
  When the E2E suite starts
  Then reuseExistingServer is false so the suite boots its own mock backend
  And the specs never hit a live LLM or mail server
```

## Technical notes (reference)
- Key files: `frontend/e2e/app.spec.ts` (4 specs + `seedMeeting` helper + screenshot paths), `frontend/playwright.config.ts` (dual web-servers: mock uvicorn on :8000 with `MOCK_LLM`/`MOCK_EMAIL`/isolated `e2e_salesintel.db`, and `npm run dev` on :5173).
- Scout "Send" button matched with `exact: true` to disambiguate from the toolbar's "Send as email"; brief/persona assertions use role+name selectors and generous timeouts for the async status flip.
- POC shortcut (intentional): the backend web-server command hardcodes the checked-in venv path (`.venv\Scripts\python.exe`) and a Windows-style DB URL — matches the documented single-machine demo setup.

## Definition of Done
- [x] Playwright config boots fresh mock backend + Vite servers with `reuseExistingServer: false`
- [x] Spec 1: app shell + nav renders
- [x] Spec 2: create meeting via dialog → lands on dashboard card
- [x] Spec 3: brief render → persona toggle (AE/SDR/SE) → Scout grounded answer
- [x] Spec 4: email compose → demo-send success
- [x] Screenshots captured for every step; all 4 specs pass
