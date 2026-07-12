# SI-3.5 — Brief JSON → styled HTML render + key facts KPI strip

| Field | Value |
|---|---|
| Issue type | Story |
| Parent epic | SI-3 — AI Brief Generation Engine |
| Status | Done |
| Priority | High |
| Story points | 5 |
| Component | Brief Engine |
| Labels | backend, frontend |

## User story
As a sales rep, I want the brief presented as a clean, self-contained document with citations and headline metrics up top, so that I can scan it fast, trust the sources, and export it to PDF without anything breaking.

## Description
The synthesis step produces validated JSON, but a rep reads a document, not JSON. This story renders a `BriefContent` into a single, polished HTML string with all CSS inlined — no external stylesheets, fonts, or scripts — so the exact same markup drives the in-app brief view and the client-side PDF export cleanly. The document leads with the company name, a one-line headline, and a meta row (persona view, tagline, generation time), followed by the sections and a linked Sources list, with a print stylesheet that flattens the card chrome and avoids breaking sections across pages.

Because section bodies come back as markdown, the renderer includes a small dependency-free markdown converter that handles bold, italics, inline code, links, headings, and both bullet and numbered lists — with all input HTML-escaped first so source text can never inject markup. The `[S#]` citation markers the model emitted inline are turned into styled citation chips, visually tying each claim back to the Sources list at the bottom. Confidence is shown per section as a colored pill, and any low-confidence section gets a prominent "Verify before use" badge plus its flags as chips, so the rep can see at a glance which claims to trust and which to confirm.

The at-a-glance layer is the key-facts KPI strip: the handful of headline metrics the model surfaced (revenue/ARR, latest funding, retail/scale, growth rate, offline mix) rendered as compact label/value tiles at the top of the brief. This is what lets a rep absorb the shape of the account in two seconds before reading a word of prose, and it's a visible payoff of the grounded synthesis — every KPI traces back to a cited fact.

## Acceptance criteria
```gherkin
Scenario: Self-contained HTML with citation chips
  Given a validated BriefContent
  When it is rendered
  Then a single HTML string with all CSS inlined is returned
  And inline [S#] markers become citation chips linked to a Sources list
  And section markdown is converted to HTML with its input escaped first
```

```gherkin
Scenario: Confidence and verification are visible
  Given a section marked low confidence or flagged "verify before use"
  When the brief is rendered
  Then that section shows a colored confidence pill and a "Verify before use" badge
  And any extra flags render as chips
```

```gherkin
Scenario: Key facts render as a KPI strip
  Given the brief includes key facts
  When it is rendered
  Then the headline metrics appear as compact label/value tiles for at-a-glance scanning
  And a brief with no key facts still renders without error (edge case)
```

## Technical notes (reference)
- Key files: `backend/app/services/brief_render.py`, `backend/app/schemas.py` (`BriefContent`, `BriefSection`, `KeyFact`, `PERSONA_LABELS`, `PERSONA_TAGLINES`)
- `render_html` emits a full self-contained document (inline `_CSS`, print media query); `_md_to_html` + `_inline_md` are the dependency-free markdown converter (escape-first, then bold/italic/code/links/lists/headings, then `[S#]` → `.cite` chips).
- Low confidence detected via `Confidence.low` or a "verify before use" flag → "Verify before use" badge; `key_facts` drives the KPI strip.
- Server renders HTML only; PDF export is client-side (`frontend/src/lib/pdf.ts`, html2pdf.js) over this same markup — no server PDF deps.

## Definition of Done
- [x] `BriefContent` renders to a single self-contained HTML string (inline CSS, print styles)
- [x] Dependency-free markdown conversion with escape-first safety
- [x] `[S#]` citation chips linked to a Sources list
- [x] Per-section confidence pills and "Verify before use" badges/flags
- [x] Key-facts KPI strip driven by `key_facts`
