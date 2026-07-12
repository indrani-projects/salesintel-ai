# SI-6.1 — Brief viewer (9 sections, citations, confidence chips, KPI strip)

| Field | Value |
|---|---|
| Issue type | Story |
| Parent epic | SI-6 — Brief Delivery: Web View & Email |
| Status | Done |
| Priority | High |
| Story points | 5 |
| Component | Delivery |
| Labels | frontend, ux |

## User story
As a sales rep, I want to read the finished brief on screen as nine clearly structured, cited sections, so that I can trust the intelligence and jump straight to the parts that matter for my role.

## Description
The brief viewer is the primary way a rep consumes a generated brief. It renders the complete 9-section pre-sales briefing for a meeting from the server-produced HTML/JSON, laid out for fast scanning rather than as a wall of text. The nine sections appear in their canonical order, each with a title and body, so the rep always sees the same familiar structure regardless of the prospect.

Above the sections, a **KPI strip** surfaces the brief's `key_facts` — the handful of at-a-glance numbers and attributes (e.g. headcount, funding, key metrics) that frame the account. Within each section, source references render as inline **`[S#]` citations** tied back to the grounding documents, so the rep can see exactly where a claim came from. Each section also carries a **confidence chip**; low-confidence sections are flagged with a "verify before use" indicator so the rep never mistakes a soft inference for a hard fact.

The viewer includes a **persona toggle** (AE / SDR / SE) that re-fetches the brief tailored to the selected role, and it hosts the **Scout** Q&A panel alongside the content so the rep can ask grounded follow-up questions without leaving the page. The viewer also anchors the download and "Send as email" actions delivered by the sibling stories in this epic.

## Acceptance criteria
```gherkin
Scenario: All nine sections render with citations
  Given a meeting whose brief status is "ready"
  When the rep opens the brief view
  Then the nine sections render in canonical order with their titles and bodies
  And inline [S#] citations appear where the brief references a source
```

```gherkin
Scenario: KPI strip reflects key facts
  Given a ready brief that carries key_facts
  When the brief view loads
  Then a KPI strip displays those key facts above the sections
```

```gherkin
Scenario: Low-confidence sections are flagged
  Given a ready brief where at least one section has low confidence
  When the rep views that section
  Then a "verify before use" confidence chip is shown on it
```

```gherkin
Scenario: Older brief without key facts (edge case)
  Given a ready brief generated before key_facts existed
  When the brief view loads
  Then the viewer renders the sections normally
  And the KPI strip degrades gracefully with no key facts shown
```

## Technical notes (reference)
- Key files: `frontend/src/pages/BriefView.tsx`, `frontend/src/lib/persona.ts`, `frontend/src/api/types.ts`.
- `ConfidenceChip` renders the "verify before use" label when `section.confidence === "low"`; `KpiStrip` reads `brief.content.key_facts ?? []` so older briefs without the field degrade gracefully.
- Persona toggle sets `activePersona`; the viewed persona defaults to the meeting's primary persona and drives a persona-scoped brief fetch. The Scout panel and the `EmailDialog` (SI-6.5) mount from this page using the same `viewPersona`.

## Definition of Done
- [x] Nine sections render in order from the server-rendered brief content.
- [x] Inline `[S#]` citations display within section bodies.
- [x] KPI strip renders `key_facts` and tolerates their absence.
- [x] Per-section confidence chips show "verify before use" for low-confidence sections.
- [x] Persona toggle re-fetches the brief for the selected role; Scout panel is present.
