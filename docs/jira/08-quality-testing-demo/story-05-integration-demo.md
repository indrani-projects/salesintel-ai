# SI-8.5 — End-to-end integration & demo dry-run

| Field | Value |
|---|---|
| Issue type | Story |
| Parent epic | SI-8 — Quality, Testing & Demo Readiness |
| Status | Done |
| Priority | High |
| Story points | 5 |
| Component | Quality |
| Labels | frontend, backend, qa |

## User story
As a presenter, I want the frontend and backend wired together with polling, CORS, seeded data, and polished states, plus a rehearsed narrative and README run steps, so that I can deliver the Zoho → Sleep Company demo start to finish without surprises.

## Description
This story turns a set of working parts into one continuous, presentable experience. It wires the React frontend to the FastAPI backend end to end: the axios client points at the backend, CORS is opened for the Vite origins, and the Dashboard and Brief pages use TanStack Query to poll `GET /meetings/{id}/brief` so a brief visibly flips `pending → generating → ready` on screen without a manual refresh. That polling is the on-stage proof that the async brief lifecycle is real.

It also hardens the UI's rough edges into demo polish: empty states (no meetings yet), loading states (the brief spinner / skeleton while generating), and error states (a brief that goes to `status=error` shows a clear message and a regenerate affordance rather than a blank page). The known-company dropdown is seeded so "The Sleep Company" is a one-click choice that resolves to `docs/sleep_company` — no free-text typing on stage, no slug mismatch.

Finally it makes the demo repeatable for anyone: the README carries exact run steps (start the backend on :8000, the frontend on :5173, the mock-mode env for a quota-free rehearsal), and the team runs a full end-to-end dry-run of the narrative — add a Sleep Company meeting → watch the brief generate → open it → toggle personas → download the PDF → chat with Scout → send the brief as email — confirming every hop works and timing the story. With mock modes on, this dry-run can be repeated as many times as needed at zero cost.

## Acceptance criteria
```gherkin
Scenario: The full demo narrative runs end to end
  Given the backend and frontend are running (mock modes on for rehearsal)
  When the presenter adds a Sleep Company meeting, opens the brief, toggles personas, downloads the PDF, chats with Scout, and sends the email
  Then every step succeeds and the brief status polls from pending to ready on screen
  And the seeded Sleep Company option resolves to docs/sleep_company
```

```gherkin
Scenario: FE and BE talk across origins with live polling
  Given the frontend on :5173 and the backend on :8000
  When a meeting is created
  Then CORS allows the request and the dashboard card polls the brief to ready without a manual refresh
```

```gherkin
Scenario: Edge case — a failed brief degrades gracefully
  Given a brief generation that ends in status error
  When the user opens the brief
  Then a clear error state with a regenerate action is shown instead of a blank or broken page
```

## Technical notes (reference)
- Key files (reference): `frontend/src/api/client.ts` (axios base URL), `backend/app/config.py` `cors_origins` / `cors_list`, Dashboard + `BriefView` polling via TanStack Query, the seeded company dropdown (Sleep Company → `sleep_company` via `sources.resolve_company_slug`), `README.md` run steps.
- Status polls `GET /meetings/{id}/brief` and watches `pending → generating → ready | error`, mirrored on both `Meeting.brief_status` and `Brief.status`.
- POC shortcut (intentional): base URL is hardcoded to `http://localhost:8000` and companies are seeded from the local `docs/` folder — a single-machine demo, no deploy or live scraping.

## Definition of Done
- [x] FE↔BE wired with axios client + CORS for the Vite origins
- [x] Dashboard/Brief poll brief status from pending → ready on screen
- [x] Empty, loading, and error states implemented and polished
- [x] Sleep Company seeded in the known-company dropdown → docs/sleep_company
- [x] README run steps documented (incl. mock-mode rehearsal)
- [x] Full end-to-end demo dry-run completed: meeting → brief → PDF → Scout → email
