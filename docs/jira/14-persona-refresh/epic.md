# EPIC SI-14 — Persona Refresh: the six personas from the persona doc (supersedes SI-4)

| Field | Value |
|---|---|
| Issue type | Epic |
| Suggested key | SI-14 |
| Status | Done |
| Priority | High |
| Component | Personas |
| Labels | backend, frontend, ai, llm, api, data, ux |
| Story points (rollup) | 21 |

## Summary
One prospect, six reader lenses: the same prospect research is re-synthesized — not re-labelled — for a Sales Representative, a Sales Manager, a Sales Enablement lead, a Revenue Operations Manager, a VP of Sales, and a SalesIntel AI Admin, each getting its own ordered section set framed to that reader's goals.

## Description
SalesIntel AI already turns external prospect signal and internal Zoho product knowledge into a grounded, cited pre-sales briefing, and epic SI-4 first made the reader's *role* a first-class dimension of that brief with three sales-motion personas (AE / SDR / SE). This epic **supersedes SI-4**: it retires that ad-hoc three-persona set and replaces it with the six canonical personas defined in `docs/shared/Expected_Features_By_Persona.docx.pdf`. Each persona reframes the *same* prospect brief to the goals and expected features the doc lists for that reader, so switching persona changes what the document is *for*, not just its heading.

The six personas are: the **Sales Representative** (the full nine-section pre-meeting brief — this is the old Account Executive brief, kept intact and renamed to match the doc); the **Sales Manager** (a coaching lens — deal snapshot, coaching focus, deal risks, stakeholders, questions to ask the rep, next steps); **Sales Enablement** (an onboarding/best-practice lens — company snapshot, best-practice prep steps, talking points, objection handling, playbook alignment, readiness checklist); the **Revenue Operations Manager** (an adoption/ROI lens — account snapshot, CRM data health, process fit, automation opportunities, ROI hypothesis, adoption angle); the **VP of Sales** (an executive lens — executive summary, strategic fit, revenue opportunity, win probability, competitive landscape, executive recommendation); and the **SalesIntel AI Admin** (a data-provenance/quality lens — source inventory & credibility, data lineage, coverage gaps, data freshness, integration/field-mapping status, quality flags).

Five of the six personas are selling roles that pitch the same prospect from a different altitude. The **Admin persona is deliberately the one non-selling role**: it is a data-provenance and quality view, not a sales pitch, and it exists to let an operator audit the sources, lineage, freshness, and gaps behind every brief. This is an explicit design choice — not a bug or an oversight — and it leans on the source-credibility scoring introduced in SI-12. Persona remains chosen at meeting-create time (the "primary" persona) and switchable on the brief itself; the primary persona is generated eagerly and the others lazily on first view, exactly as the SI-4 lifecycle established. This epic shipped as **PR #13** on branch `feat/personas`, and includes a one-time, guarded migration that remaps legacy `ae`/`sdr`/`se` rows onto the new set so existing meetings survive the switch.

## Stories in this epic
| Key | Story | Points | Priority |
|---|---|---|---|
| SI-14.1 | Six-persona contract, section sets & default | 3 | High |
| SI-14.2 | Per-persona framing & section guidance for all new sections | 8 | High |
| SI-14.3 | Frontend: six-persona types, colours, selector grid, tabs & badges | 5 | High |
| SI-14.4 | One-time legacy persona migration with brief regeneration | 5 | High |

## Epic acceptance criteria
```gherkin
Scenario: The same prospect yields six role-specific briefs
  Given a meeting exists for "The Sleep Company"
  When the brief is viewed as each of the six personas in turn
  Then each persona shows its own ordered section set from the persona doc
  And the Sales Representative brief is the full nine-section pre-meeting brief
  And the Sales Manager brief leads with a deal snapshot and coaching focus
  And the VP of Sales brief leads with an executive summary and strategic fit
  And the Admin brief shows source inventory, data lineage, and quality flags rather than a sales pitch
```
```gherkin
Scenario: Six is the canonical set and sales_rep is the default
  Given the shared Persona enum
  When a brief is generated without an explicit persona
  Then it is generated as DEFAULT_PERSONA ("sales_rep")
  And exactly six personas are exposed: sales_rep, sales_manager, enablement, revops, vp_sales, admin
  And the old ae / sdr / se persona set is no longer present
```
```gherkin
Scenario: Existing meetings survive the persona switch
  Given meetings created before the refresh with legacy ae / sdr / se briefs
  When the app initializes after the refresh
  Then a one-time migration remaps those rows onto the new persona set
  And no request 500s on an unknown enum value
  And the affected meetings regenerate their briefs to a ready state
```

## Out of scope
- Custom or user-defined personas beyond the six in the persona doc.
- Cross-persona diffing or a combined "all personas" export.
- Per-persona chatbot (Scout) tuning — chat remains shared across personas.
- Vector retrieval or per-persona source selection (all personas share the single-call corpus).
- Turning the Admin persona into a selling brief — it is intentionally a data-provenance view.

## Dependencies
- Supersedes and replaces epic SI-4 (Multi-Persona Briefs, AE / SDR / SE); reuses its lazy-generation lifecycle and persona-scoped API.
- The Admin persona's credibility/quality view depends on the source-credibility scoring from SI-12.
- Shares the `schemas.py` / `frontend/src/api/types.ts` contract seam; the persona set is replaced in lockstep across both.

## Verification
- Backend `pytest` all green — `test_schemas`, `test_brief_engine`, `test_api`, and `test_email_service` updated for the six personas; every persona generates its declared section set.
- `npm run build` green.
- Playwright 6/6 — the persona toggle walks Sales Representative → Sales Manager → VP of Sales, and a screenshot confirms the six-persona selector renders as a responsive 3×2 grid.
- Migration ran live: four existing meetings remapped to `sales_rep` and their briefs regenerated to `ready`.
