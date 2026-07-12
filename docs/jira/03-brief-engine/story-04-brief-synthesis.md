# SI-3.4 — 9-section grounded, cited, why/agenda-tailored synthesis

| Field | Value |
|---|---|
| Issue type | Story |
| Parent epic | SI-3 — AI Brief Generation Engine |
| Status | Done |
| Priority | Highest |
| Story points | 8 |
| Component | Brief Engine |
| Labels | backend, ai, llm |

## User story
As a sales rep, I want a 9-section brief that crosses the prospect's real situation with what Zoho actually sells — cited, confidence-flagged, and slanted toward my meeting's purpose — so that I walk in with a pre-sales angle instead of a summary I could have written myself.

## Description
This is the flagship story of the epic: the synthesis step where source text becomes intelligence. It takes the resolved prospect, the meeting's subject/why/agenda, and the full set of loaded source documents (prospect signal plus shared Zoho knowledge), builds a single prompt containing ALL of that source text, and asks the LLM to return a strict-JSON briefing. There is deliberately no vector database and no retrieval — everything is stuffed into one call. That is a documented POC shortcut; RAG is the scale path once the corpus outgrows the context window. For the demo's document volume, one call gives the model total recall over every source and lets it draw connections across the whole corpus at once, which is exactly what the pain and angle sections need.

The brief is nine fixed sections in a fixed order: (1) Company Snapshot, (2) Financial & Funding Health, (3) Trigger Events / Recent News, (4) GTM & Operating Model, (5) Pain Hypotheses → Mapped to Zoho, (6) Tech Stack Signals, (7) Key Stakeholders, (8) Risks & Watch-outs, (9) Analyst's Recommended Angle. Sections 5, 8, and 9 are the intelligence — they require inference across both knowledge sources. The prompt gives each section pointed guidance: the pain section must map a concrete prospect signal (growth, retail expansion, D2C/omnichannel, hiring, funding pressure) to a specific Zoho product framed as "prospect signal → likely pain → Zoho product that solves it", and the recommended angle is explicitly the analyst's own synthesized take on how to open and steer the meeting, grounded but allowed to connect dots.

Grounding is non-negotiable. The prompt supplies a source inventory of `[S#]` markers and requires an inline `[S#]` citation on every factual claim, using only the provided sources rather than inventing facts. Anything stale, thin, or inferred must be set to low confidence and flagged. The reader's meeting `why` and `agenda` are injected into the prompt so the brief's emphasis shifts per meeting — an agenda of "scaling support" pulls Zoho Desk to the foreground of the pain and angle sections. That per-meeting shift is the demo's proof that the synthesis is real and not a static template. (The engine is persona-aware — AE, SDR, SE each get a tailored section set and framing — with the 9-section AE brief as the primary case.)

Model calls are hardened for the real world. The request asks for JSON mode (`response_format`) with `reasoning_effort="low"` — which caps the default "thinking" of Gemini flash models and cuts generation from minutes to well under a minute with no meaningful quality loss on this grounded task — and falls back gracefully: if the endpoint rejects `reasoning_effort` it retries with JSON mode only, and if it rejects `response_format` too it drops to a plain call. Parsing is equally defensive: code fences are stripped, only sections whose ids belong to the persona are accepted, confidence values and flags are coerced into valid shapes, and the full section set is guaranteed in order — any section the model omits or returns empty becomes a low-confidence "verify before use" placeholder. Sources fall back to the loaded inventory if the model doesn't declare its own, key facts are captured and capped, and a parse/validation failure triggers one automatic retry before the engine raises. The result is that a flaky model can never produce a broken or incomplete brief.

## Acceptance criteria
```gherkin
Scenario: A grounded, cited 9-section brief in fixed order
  Given a resolved prospect with prospect and Zoho source documents
  When synthesis runs
  Then the brief contains exactly the nine sections in the fixed order
  And every factual claim carries an inline [S#] citation to a provided source
  And the pain and angle sections map prospect signal to specific Zoho products
```

```gherkin
Scenario: Agenda shifts the brief's emphasis
  Given a meeting whose agenda is "scaling support"
  When the why and agenda are injected into the synthesis prompt
  Then the pain-hypothesis and recommended-angle sections give Zoho Desk visible weight
  And a different agenda produces a visibly different emphasis for the same prospect
```

```gherkin
Scenario: Model rejects the tuning parameters
  Given the LLM endpoint rejects reasoning_effort
  When the engine calls the model
  Then it retries with JSON mode only, and then a plain call if needed
  And a valid brief is still produced
```

```gherkin
Scenario: Malformed or partial model output is repaired (edge case)
  Given the model returns fenced text, an unknown section id, or omits a section
  When the response is parsed
  Then fences are stripped and only valid persona section ids are accepted
  And confidence and flags are coerced into valid values
  And every missing or empty section becomes a low-confidence "verify before use" placeholder
  And a parse failure triggers one automatic retry before the engine gives up
```

## Technical notes (reference)
- Key files: `backend/app/services/brief_engine.py`, `backend/app/schemas.py` (`SECTION_ORDER`, `SECTION_TITLES`, `sections_for`, `BriefContent`, `BriefSection`, `KeyFact`, `Confidence`)
- One-call design: `_build_source_corpus` concatenates all source text; `_user_prompt` embeds the inventory, corpus, the required JSON shape, and the why/agenda. NO vector DB — RAG is the documented scale path.
- `_call_llm` tries JSON mode + `reasoning_effort="low"`, falls back to JSON-mode-only, then a plain call. `_REASONING_EFFORT="low"` caps Gemini flash thinking (~458s → ~35-60s).
- `_parse_brief` strips fences, accepts only valid persona section ids, coerces confidence/flags, guarantees the full ordered section set (missing/empty → `_placeholder_section` at low confidence with "verify before use"), falls back to the loaded source inventory, and caps `key_facts` to 5. `generate_brief` retries once on any parse/validation error.
- Persona-aware (AE/SDR/SE) via `sections_for`; the 9-section AE brief is the primary demo case. A `MOCK_LLM` mode returns a deterministic brief for tests/Playwright.

## Definition of Done
- [x] All source text sent in one LLM call; strict JSON requested
- [x] Nine fixed sections in fixed order, guaranteed present even on partial output
- [x] Inline `[S#]` citation required on every factual claim; unsupported claims flagged low-confidence
- [x] why/agenda injected so emphasis shifts per meeting (demo proof of real synthesis)
- [x] `reasoning_effort=low` with graceful fallback to plain call; defensive parse with one retry
- [x] Missing sections become low-confidence "verify before use" placeholders
