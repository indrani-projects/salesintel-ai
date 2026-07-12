# SI-7.3 — Direction C design system (tokens, KPI strip, hero, cards, status pills)

| Field | Value |
|---|---|
| Issue type | Story |
| Parent epic | SI-7 — Application Experience & Visual Design (Direction C) |
| Status | Done |
| Priority | Medium |
| Story points | 8 |
| Component | Frontend/UX |
| Labels | frontend, design, ux |

## User story
As a demo presenter, I want one cohesive visual design system applied across every screen, so that SalesIntel AI looks like a premium, shipped SaaS product rather than a prototype, and every surface feels like part of the same app.

## Description
"Direction C" is the chosen visual direction for SalesIntel AI, and this story is where it becomes real across the whole application. It defines a token/theme system — a palette (indigo brand accent, ink neutrals, and semantic good/warn/bad colors), typography scale, corner radii, and elevation — expressed as Tailwind theme tokens and a small set of reusable component classes (`card`, `btn-primary`, `btn-secondary`, status pills, segmented control). Because the vocabulary is centralized, every page composes the same primitives instead of inventing one-off styles.

The system is applied consistently to all five surfaces: the **Calendar** (a themed FullCalendar), the **Dashboard** brief cards with their status pills, the **BriefView**, the **meeting-creation dialog**, and the **Scout panel**. BriefView is where the design does the most work: it opens with a **KPI strip** (a responsive 2/4-column grid of stat cards driven by the brief's `key_facts` — label, big number, optional note), followed by a **hero card** (persona eyebrow chip, company name, headline, and a "Ready · N sources" status pill), then the nine numbered **section cards**. Each section card carries a **confidence chip** (high/medium/low) and, for low-confidence sections, a "verify before use" flag — turning the intelligence layer's honesty into a visible, trustworthy design element.

Supporting patterns round out the system: numbered section badges, source citation lists, persona accent tints (indigo/emerald/amber for AE/SDR/SE), skeleton loaders for the fetching state, and empty/error states styled as first-class cards. The payoff is a demo where every click lands on something that looks intentional and finished.

## Acceptance criteria
```gherkin
Scenario: One token system spans every screen
  Given the user navigates across Calendar, Briefs, BriefView, the meeting dialog, and Scout
  When each surface renders
  Then all of them use the same Direction C tokens — brand accent, card style, radii, and typography
  And status colors (good/warn/bad) are semantically consistent everywhere
```

```gherkin
Scenario: The KPI strip renders from the brief's key facts
  Given a ready brief that includes key_facts
  When the BriefView renders
  Then a KPI strip shows up to four stat cards, each with a label, large value, and optional note
  And the hero card shows the persona chip, company, headline, and a "Ready · N sources" pill
```

```gherkin
Scenario: Confidence is communicated on every section
  Given a ready brief with sections of varying confidence
  When the section cards render
  Then each card shows a high/medium/low confidence chip
  And any low-confidence section additionally shows a "verify before use" flag
```

```gherkin
Scenario: Loading and empty states are designed, not blank
  Given a brief is still generating or a list is empty
  When the screen renders
  Then it shows styled skeleton cards while loading
  And a styled empty-state card (icon, heading, guidance, call-to-action) when there is nothing to show
```

## Technical notes (reference)
- Key files: `frontend/src/pages/BriefView.tsx` (`KpiStrip`, hero, `SectionCard`, `ConfidenceChip`, `VerifyFlag`), `frontend/src/pages/Dashboard.tsx`, `frontend/src/pages/Calendar.tsx`, `frontend/src/components/MeetingDialog.tsx`, `frontend/src/components/ChatPanel.tsx`, `frontend/src/components/BriefCard.tsx`, `frontend/src/components/PersonaBadge.tsx`; tokens/component classes in `frontend/tailwind.config.*` + global CSS.
- KPI strip is driven by `brief.content.key_facts` (`slice(0,4)`); older briefs may lack `key_facts`, so it renders nothing rather than erroring.
- Confidence chip styling maps through `CONFIDENCE_META` in `lib/format.ts`; persona accent tints live in `lib/persona.ts` (`PERSONA_ACCENTS`) as full literal Tailwind class strings so the JIT scanner keeps them.
- Semantic tokens (`ink-*`, `brand-*`, `good`/`warn`/`bad`, `nav`, `muted`/`faint`) are used app-wide; reusable classes `card`, `btn-primary`, `btn-secondary`, `seg`/`seg-btn`.

## Definition of Done
- [x] Direction C token/theme system defined (color, type, radii, elevation) and applied to Calendar, Dashboard, BriefView, meeting dialog, and Scout.
- [x] BriefView KPI strip (from `key_facts`), hero card, numbered section cards, confidence chips, and verify flags implemented.
- [x] Reusable component classes (`card`, buttons, status pills, segmented control) used consistently instead of one-off styles.
- [x] Loading skeletons and styled empty/error states in place across list and detail screens.
