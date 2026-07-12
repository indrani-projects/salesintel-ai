# SI-1.2 — Shared API contract & 9-section brief schema

| Field | Value |
|---|---|
| Issue type | Story |
| Parent epic | SI-1 — Platform Foundation & Data Contract |
| Status | Done |
| Priority | Highest |
| Story points | 5 |
| Component | Platform |
| Labels | backend, api, data |

## User story
As an engineer building any part of SalesIntel AI, I want one authoritative definition of every API shape and the 9 brief sections, so that the backend, the AI engine, and the frontend can be built in parallel and still fit together perfectly.

## Description
This story delivers the backbone of the entire codebase: the shared data contract. Because the product was built by multiple agents working at the same time with strictly separated file ownership, the "seam" between them had to be defined once, up front, and then frozen. Two files carry that contract and are treated as **read-only / append-only** — you may add to them, but you never rename or retype an existing field without a coordinated update everywhere it is mirrored.

`schemas.py` holds every API request and response body as a Pydantic model: the Company listing, Meeting create/read, the full Brief content (headline, at-a-glance key facts, the list of sections, and the citable sources), the Brief read wrapper (status plus content plus rendered HTML or an error), and the Chat request/response. It also defines the enums that keep the system honest — `BriefStatus` (pending / generating / ready / error), `Confidence` (high / medium / low), and `Persona` (AE / SDR / SE). Crucially, it defines `SECTION_ORDER` and `SECTION_TITLES`: the canonical identifiers and display titles of the nine sections that make up the flagship AE brief — Company Snapshot, Financial & Funding Health, Trigger Events / Recent News, GTM & Operating Model, Pain Hypotheses mapped to Zoho, Tech Stack Signals, Key Stakeholders, Risks & Watch-outs, and the Analyst's Recommended Angle.

`contracts.py` complements it with the exact service function signatures that the API layer imports and the service layer implements (brief generation, question answering, source loading, HTML rendering, and so on), plus the internal `SourceDoc` dataclass used to pass ingested source text around. Together these two files let each agent code against a stable interface without reading each other's implementation.

The single most important rule this story establishes: **every field name in `schemas.py` is mirrored by hand in `frontend/src/api/types.ts` and in the JSON shape the LLM is instructed to emit.** These three are not generated from one another — they are kept in sync deliberately. Change a field name in one place and it must change in all three, or the brief silently breaks. This intentional POC convention (hand-mirroring instead of code generation) keeps the toolchain simple while making the sync discipline explicit.

## Acceptance criteria

**Scenario: Every API shape has a single source of truth**
```gherkin
Given the shared schemas module
When the backend, AI engine, or frontend needs the shape of a meeting, brief, or chat message
Then it references the same Pydantic definition and no shape is redefined elsewhere
```

**Scenario: The nine sections are canonical and ordered**
```gherkin
Given SECTION_ORDER and SECTION_TITLES in the contract
When a brief is generated and rendered
Then all nine sections appear in the defined order with the defined titles
```

**Scenario: The three mirrors stay in sync**
```gherkin
Given a field defined in schemas.py
When the same data is typed in the frontend and requested from the LLM as JSON
Then the field name is identical in all three places
And a mismatch would be treated as a defect, not an accepted variation
```

**Scenario: Statuses and confidence are constrained to known values**
```gherkin
Given the BriefStatus and Confidence enums
When a brief moves through its lifecycle or a section is scored
Then only the enumerated values (pending/generating/ready/error and high/medium/low) are valid
```

## Technical notes (reference)
- Key files: `backend/app/schemas.py`, `backend/app/contracts.py`
- Read-only / append-only backbone: the seam between parallel build agents; add fields, never silently rename.
- Mirrors to keep in sync: `schemas.py` ↔ `frontend/src/api/types.ts` ↔ the LLM JSON output shape (hand-mirrored by intent, not generated).
- `SourceDoc` (in `contracts.py`) is the internal dataclass carrying ingested source text between services; `BriefSource` (in `schemas.py`) is the citable, marker-referenced source returned to clients.
- The schema is persona-aware: `PERSONA_SECTIONS` defines section sets for AE (the nine), SDR, and SE briefs.

## Definition of Done
- [x] All API request/response DTOs defined as Pydantic models in `schemas.py`.
- [x] `SECTION_ORDER` and `SECTION_TITLES` define the nine sections and their titles.
- [x] `BriefStatus`, `Confidence`, and `Persona` enums defined and used across the app.
- [x] Service function signatures and the `SourceDoc` dataclass defined in `contracts.py`.
- [x] Frontend `types.ts` and the LLM JSON shape mirror the schema field-for-field.
- [x] Both files documented as read-only / append-only backbone.
