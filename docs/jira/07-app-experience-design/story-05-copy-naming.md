# SI-7.5 — Copy & naming pass (full-form persona labels, "Scout")

| Field | Value |
|---|---|
| Issue type | Story |
| Parent epic | SI-7 — Application Experience & Visual Design (Direction C) |
| Status | Done |
| Priority | Low |
| Story points | 2 |
| Component | Frontend/UX |
| Labels | frontend, ux |

## User story
As a demo presenter, I want polished, human-readable copy across the app, so that personas read as real job titles and the assistant has a memorable name, making the product feel finished rather than developer-facing.

## Description
This is the final polish pass that makes the product read like a shipped tool. Two changes run throughout the UI. First, personas are always shown with their full-form labels — Account Executive, Sales Development Rep, and Solutions Engineer — instead of the internal codes (`ae` / `sdr` / `se`). The labels are centralized in a single `PERSONA_LABELS` map so the meeting dialog, the "View as" segmented control on the brief, the persona badge on cards, the brief hero chip, the generating-state copy, the email dialog, and the sidebar rep identity all draw from one source of truth.

Second, the grounded per-account assistant is named **"Scout"** everywhere it appears: the panel header, the locked-state message ("Scout unlocks once the brief is ready"), the empty prompt ("Ask Scout a question"), and the input placeholders ("Ask Scout…"). Naming the assistant gives the chatbot a personality and makes it easy to refer to during the demo.

Although small in points, this pass touches many files and matters disproportionately for perceived quality — raw enum codes or a generic "chatbot" label are exactly the tells that make a demo feel unfinished. Centralizing the copy also keeps it consistent and easy to change.

## Acceptance criteria
```gherkin
Scenario: Personas are shown as full-form labels
  Given the user views any persona selector, badge, or brief header
  When a persona is displayed
  Then it reads "Account Executive", "Sales Development Rep", or "Solutions Engineer"
  And the internal codes ae/sdr/se are never surfaced to the user
```

```gherkin
Scenario: The assistant is named Scout throughout
  Given the user opens the assistant panel on a brief
  When the panel renders in any state
  Then it is titled "Scout"
  And its locked message, empty prompt, and input placeholder all refer to "Scout"
```

```gherkin
Scenario: Labels come from one source of truth
  Given the persona label map is the single definition of display names
  When any screen needs a persona label
  Then it reads from PERSONA_LABELS rather than hardcoding the string
```

## Technical notes (reference)
- Key files: `frontend/src/api/types.ts` (`PERSONA_LABELS`: `ae → "Account Executive"`, `sdr → "Sales Development Rep"`, `se → "Solutions Engineer"`), `frontend/src/lib/persona.ts` (re-exports labels + `PERSONAS`), `frontend/src/components/ChatPanel.tsx` (Scout naming), `frontend/src/pages/BriefView.tsx`, `frontend/src/components/MeetingDialog.tsx`, `frontend/src/components/PersonaBadge.tsx`, `frontend/src/components/EmailDialog.tsx`, `frontend/src/components/Layout.tsx`.
- Single source of truth: all persona display strings resolve through `PERSONA_LABELS`; no raw `ae`/`sdr`/`se` codes are rendered.
- "Scout" appears in the panel header, locked-state text, empty prompt, and input placeholders in `ChatPanel.tsx`.

## Definition of Done
- [x] All persona references render full-form labels sourced from `PERSONA_LABELS`.
- [x] The chatbot is named "Scout" across its header, states, and placeholders.
- [x] No internal persona codes are visible in the UI.
