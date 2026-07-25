# SI-11.4 — Generic any-company pipeline + free-text UI + hints

| Field | Value |
|---|---|
| Issue type | Story |
| Parent epic | SI-11 — Web-First Prospect Intel (generic, on-demand) + filtered cache |
| Status | Done |
| Priority | High |
| Story points | 5 |
| Component | Intelligence |
| Labels | backend, frontend, ux, ai |

## User story
As a sales rep, I want to type any prospect company name when I add a meeting and still get a grounded brief, so that I am not limited to the handful of companies that happen to have a local docs folder.

## Description
This story makes the pipeline **truly generic**: any company name works, not just the five research-guide targets or companies with a `docs/<slug>/` folder. `resolve_company_slug` returning `None` is no longer an error — it simply means there is no local folder, and the web-first seam (SI-11.3) supplies the intel by name.

On the frontend, the meeting dialog's company field became a **free-text input with suggestions** (`frontend/src/components/MeetingDialog.tsx`): a rep can pick a known company or type an entirely new one. The suggestions are a convenience, not a constraint.

An optional `backend/app/services/company_hints.py` enriches the research guide's five targets with a ticker and a Zoho pitch angle:

| Company | Ticker | Angle |
|---|---|---|
| Freshworks | FRSH | Zoho pitch angle |
| Braze | BRZE | Zoho pitch angle |
| Sprout Social | SPT | Zoho pitch angle |
| Amplitude | AMPL | Zoho pitch angle |
| Zuora | ZUO | Zoho pitch angle |

Hints are strictly optional enrichment — the **generic path works without any hint**, so a company that is not in the table still produces a complete brief from web intel alone. A `mock_web` mode keeps the whole flow deterministic for tests and E2E, where the dialog E2E now creates a web-only "Freshworks" meeting.

## Acceptance criteria
```gherkin
Scenario: Any company name is accepted
  Given a company name that maps to no docs/<slug>/ folder
  When a meeting is created
  Then resolve_company_slug returning None is handled gracefully
  And the brief is generated from web intel by name
```

```gherkin
Scenario: Free-text company entry with suggestions
  Given the rep opens the meeting dialog
  When they type a company name
  Then the field accepts free text and offers suggestions
  And a brand-new company name can be submitted
```

```gherkin
Scenario: Hints enrich the five targets without gating others
  Given a company present in company_hints (e.g. Freshworks / FRSH)
  When the brief is generated
  Then the ticker and Zoho pitch angle enrich the pipeline
  And a company absent from the table still produces a complete brief via the generic path
```

```gherkin
Scenario: Deterministic mock for tests and E2E
  Given MOCK_WEB is enabled
  When the dialog E2E creates a "Freshworks" web-only meeting
  Then the flow runs deterministically with no live network calls
```

## Technical notes (reference)
- Key files: `frontend/src/components/MeetingDialog.tsx` (free-text company input + suggestions), `backend/app/services/company_hints.py` (optional), `sources.resolve_company_slug` (None is valid).
- Hints: Freshworks/FRSH, Braze/BRZE, Sprout Social/SPT, Amplitude/AMPL, Zuora/ZUO — ticker + Zoho pitch angle; generic path requires no hint.
- `mock_web` keeps the end-to-end flow deterministic; the dialog E2E creates a web-only "Freshworks" meeting.

## Definition of Done
- [x] Any company name works; `resolve_company_slug` returning `None` is handled, not an error.
- [x] Meeting dialog company field is a free-text input with suggestions.
- [x] Optional `company_hints.py` enriches the five targets (ticker + Zoho angle); generic path works without a hint.
- [x] `mock_web` provides deterministic behavior; dialog E2E creates a "Freshworks" web-only meeting.
- [x] Verified within the suite: pytest 40/40, npm build clean, Playwright 5/5 under `MOCK_WEB`.
