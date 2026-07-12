# EPIC SI-3 — AI Brief Generation Engine

| Field | Value |
|---|---|
| Issue type | Epic |
| Suggested key | SI-3 |
| Status | Done |
| Priority | Highest |
| Component | Brief Engine |
| Labels | backend, ai, llm, data, api |
| Story points (rollup) | 25 |

## Summary
Ingest local prospect and Zoho source documents, synthesize a grounded, cited, why/agenda-tailored 9-section pre-sales brief in one LLM call, render it to self-contained HTML, and serve it through the Briefs API.

## Description
This epic is the intelligence core of SalesIntel AI — the reason the product exists. Everything else in the app (calendar, dashboard, chat) is scaffolding around the moment when a sales rep opens a brief and sees an actual pre-sales angle rather than a summary. The demo scenario is Zoho selling to "The Sleep Company": the engine crosses external prospect signal (`docs/<company>/` PDFs) with internal Zoho product knowledge (`docs/zoho/`) and infers where the two connect. Sections 5 (Pain Hypotheses → Zoho products), 8 (Risks & Watch-outs) and 9 (Analyst's Recommended Angle) are where that inference lives; the other six sections are grounded factual scaffolding that makes the inference trustworthy.

The engine is a linear service chain. `sources.py` discovers which company folder a free-text prospect name maps to and collects that company's documents plus the always-appended shared Zoho knowledge. `ingestion.py` extracts clean text from each document (PDF via PyMuPDF, plus Markdown/text/HTML) and caches the result so re-runs are fast. `brief_engine.py` stuffs all extracted source text into a single prompt, asks an OpenAI-compatible LLM for strict JSON, and parses it defensively so a malformed model response can never break the brief. `brief_render.py` turns the validated JSON into a styled, self-contained HTML document with a key-facts KPI strip and `[S#]` citation chips. `briefs.py` exposes status, content, and HTML to the frontend and supports lazy generation and regeneration.

Two deliberate POC shortcuts are load-bearing and intentional, with the scale path noted. First, there is NO vector database — ALL source text is concatenated into one LLM call rather than retrieved by embedding similarity; RAG is the documented scale path once the corpus outgrows the context window. Second, the sources come from a local `docs/` folder instead of live web scraping; the source layer is written behind a provider seam so a live-fetch implementation can drop in without touching the synthesis code.

Every factual claim in a brief carries an inline `[S#]` citation back to the source that supports it, and any claim the model judges stale, thin, or inferred is set to low confidence and flagged "verify before use". The rep's meeting `why` and `agenda` are injected into the prompt so emphasis shifts per meeting — an agenda of "scaling support" pulls Zoho Desk to the foreground of the pain and angle sections. That per-meeting shift is the demo's proof that the synthesis is real and not a static template.

## Stories in this epic
| Key | Story | Points | Priority |
|---|---|---|---|
| SI-3.1 | Source discovery (LocalFolderProvider + Zoho shared knowledge) | 3 | High |
| SI-3.2 | Document ingestion (PyMuPDF extraction + cache) | 3 | High |
| SI-3.3 | Swappable OpenAI-compatible LLM client | 3 | High |
| SI-3.4 | 9-section grounded, cited, why/agenda-tailored synthesis | 8 | Highest |
| SI-3.5 | Brief JSON → styled HTML render + key facts KPI strip | 5 | High |
| SI-3.6 | Briefs API (status, fetch content/HTML, regenerate) | 3 | High |

## Epic acceptance criteria
```gherkin
Scenario: A grounded, cited brief is generated for a known prospect
  Given a meeting for "The Sleep Company" with a why and an agenda
  When the brief-generation engine runs end to end
  Then a 9-section brief is produced in the fixed section order
  And every factual claim carries an inline [S#] citation
  And the brief crosses prospect signal with Zoho product knowledge in the pain and angle sections
```

```gherkin
Scenario: The rep's agenda shifts the brief's emphasis
  Given two meetings for the same prospect with different agendas
  When each brief is generated
  Then the pain-hypothesis and recommended-angle sections emphasize the Zoho products relevant to each agenda
  And the briefs are visibly different, proving the synthesis is dynamic
```

```gherkin
Scenario: The engine degrades gracefully on a bad model response
  Given the LLM returns malformed or partial JSON
  When the engine parses the response
  Then all nine sections are still guaranteed in order
  And any missing section becomes a low-confidence "verify before use" placeholder
  And the brief is never left in a broken state
```

## Out of scope
- Vector database / embedding-based retrieval (RAG is the documented scale path)
- Live web scraping of prospect signal (local `docs/` folder is the POC source)
- Server-side PDF generation (PDF export is client-side over the rendered HTML)
- The grounded Q&A chatbot over a brief (separate epic)

## Dependencies
- Shared contracts in `backend/app/schemas.py` and `backend/app/contracts.py` (section order/titles, `SourceDoc`, service signatures)
- Meeting lifecycle and background-task scheduling (Meetings epic) that invokes the engine
