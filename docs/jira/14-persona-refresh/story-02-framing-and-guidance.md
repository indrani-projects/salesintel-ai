# SI-14.2 — Per-persona framing & section guidance for all new sections

| Field | Value |
|---|---|
| Issue type | Story |
| Parent epic | SI-14 — Persona Refresh: the six personas from the persona doc (supersedes SI-4) |
| Status | Done |
| Priority | High |
| Story points | 8 |
| Component | Personas |
| Labels | backend, ai, llm |

## User story
As a sales reader, I want the brief for my persona to actually read like it was written for my job — coaching if I'm a manager, ROI if I'm in RevOps, provenance if I'm the Admin — so that switching persona changes the synthesis, not just the section headings.

## Description
This story rewrites the generation layer so all six personas produce genuinely persona-shaped synthesis. `brief_engine.py`'s `_PERSONA_FRAMING` is rewritten for every one of the six personas: each entry tells the LLM who is reading, what they are trying to accomplish, and how to angle the same prospect corpus toward that reader's goals — a coaching angle for the Sales Manager, an onboarding/best-practice angle for Enablement, an adoption/ROI angle for RevOps, an executive angle for the VP of Sales, and a data-provenance/quality angle for the Admin. The Admin framing is explicitly a non-selling audit voice: it inventories and grades sources rather than pitching Zoho.

Because the six personas introduce many new section ids that never existed under SI-4, `_SECTION_GUIDANCE` is extended to give per-section instructions for every new section — deal snapshot, coaching focus, ROI hypothesis, competitive landscape, source inventory & credibility, data lineage, quality flags, and the rest — so each section is grounded and cited rather than generic. Where a persona is not explicitly supplied, generation defaults to `DEFAULT_PERSONA`.

The per-persona fan-out is kept in sync with the contract by deriving `meetings.ALL_PERSONAS` from the enum itself (`[p.value for p in Persona]`) rather than a hand-maintained list, so adding or renaming a persona in `schemas.py` automatically flows into which briefs get generated. The lazy lifecycle from SI-4 is unchanged: the primary persona chosen at meeting-create is generated eagerly, and the other personas are generated on first view.

## Acceptance criteria
```gherkin
Scenario: Every persona has framing that shifts the synthesis
  Given a prospect corpus for "The Sleep Company"
  When the brief is generated for each of the six personas
  Then the Sales Manager brief is framed as coaching for the rep
  And the RevOps brief is framed around adoption and ROI
  And the VP of Sales brief is framed as an executive decision aid
  And the Admin brief is framed as a data-provenance audit, not a sales pitch
```
```gherkin
Scenario: Every new section id has grounding guidance
  Given _SECTION_GUIDANCE
  When any section from any of the six personas is synthesized
  Then that section id has its own guidance entry
  And the section is produced grounded and cited rather than as a generic placeholder
```
```gherkin
Scenario: The fan-out list stays in sync with the enum
  Given meetings.ALL_PERSONAS
  When the Persona enum changes
  Then ALL_PERSONAS is derived as [p.value for p in Persona] and reflects the change automatically
  And generation without an explicit persona uses DEFAULT_PERSONA
```

## Technical notes (reference)
- Key files: `backend/app/services/brief_engine.py` (`_PERSONA_FRAMING` rewritten for all six personas, `_SECTION_GUIDANCE` extended for every new section id, defaults use `DEFAULT_PERSONA`) and `backend/app/api/meetings.py` (`ALL_PERSONAS = [p.value for p in Persona]`).
- The single-call synthesis pipeline is unchanged — all source text is still stuffed into one LLM call; only the framing and per-section guidance are persona-aware.
- Lazy generation is unchanged: primary persona eager on meeting-create, others on first view.
- The Admin framing deliberately does not sell — it grades and traces sources, using the SI-12 credibility scoring.

## Definition of Done
- [x] `_PERSONA_FRAMING` rewritten with a distinct framing for all six personas, including the non-selling Admin audit voice.
- [x] `_SECTION_GUIDANCE` given a guidance entry for every new section id across the six personas.
- [x] Generation defaults to `DEFAULT_PERSONA` when a persona is not supplied.
- [x] `meetings.ALL_PERSONAS` derived from the `Persona` enum so the fan-out stays in sync.
- [x] Lazy per-persona lifecycle preserved (primary eager, others on first view).
