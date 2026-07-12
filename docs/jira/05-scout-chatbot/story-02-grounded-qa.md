# SI-5.2 — Grounded Q&A service with graceful decline

| Field | Value |
|---|---|
| Issue type | Story |
| Parent epic | SI-5 — Scout Chatbot (Grounded Q&A) |
| Status | Done |
| Priority | High |
| Story points | 5 |
| Component | Scout |
| Labels | backend, ai, llm |

## User story
As a sales rep, I want Scout's answers to come only from the brief and its sources, with citations, and to be told plainly when something isn't in the sources, so that I can trust every answer and never act on a fabricated fact.

## Description
This is the intelligence behind Scout. Given a company slug, the validated brief, the prior conversation, and the rep's new question, the service assembles a grounded prompt and calls the single OpenAI-compatible LLM client to produce an answer.

The prompt is built from two evidence blocks. The first is the brief context — its headline and every section rendered with title, id, and markdown body. The second is the source-document context — the freshly loaded prospect and Zoho documents (via `load_company_sources`), each labelled with its `[S#]` marker, tag, title, and filename, and truncated to a per-document cap to keep the chat context lean relative to full brief generation. A system prompt instructs the model to answer *only* from the brief and sources, to cite `[S#]` markers for every claim, and — critically — to set `grounded=false` and say the answer isn't in the available sources rather than guessing. The last several turns of conversation history are included so follow-ups stay coherent.

The model is asked for strict JSON (`{"answer_md", "grounded"}`) via `response_format`, with a low reasoning effort to cap latency; if the endpoint rejects those parameters the call falls back to a plain completion. The response is parsed defensively: code fences are stripped, JSON is parsed when present and otherwise the raw text is treated as the answer, and an empty answer is converted into a graceful decline with `grounded=false`. Finally, citations are resolved by scanning the answer for `[S#]` markers and matching them against the brief's source list (falling back to the full source list when no markers are found), so the returned `ChatResponse` carries the exact sources backing the answer. A mock mode short-circuits the LLM for offline demos, deterministically declining "favourite colour"-style out-of-scope questions to showcase the decline path.

## Acceptance criteria
```gherkin
Scenario: Answer grounded in the sources with citations
  Given a brief and its source documents for a prospect
  When the rep asks a question the sources support
  Then the service returns grounded=true with an answer citing the relevant [S#] markers
  And the returned citations match the referenced markers from the brief's source list
```

```gherkin
Scenario: Graceful decline when unsupported
  Given a question that the brief and sources do not cover
  When the service generates an answer
  Then it returns grounded=false and states the answer isn't in the available sources
  And it does not fabricate prospect facts
```

```gherkin
Scenario: Malformed or empty model output
  Given the LLM returns non-JSON text, fenced output, or an empty string
  When the service parses the response
  Then fences are stripped and non-JSON text is used as the answer
  And an empty answer becomes a grounded=false graceful decline
```

## Technical notes (reference)
- Key files: `backend/app/services/chat_service.py`
- Sources loaded via `load_company_sources(company_slug)`; each doc truncated to `_MAX_DOC_CHARS` (8000) and only the last `_MAX_HISTORY` (10) turns are sent.
- Primary LLM call requests `response_format={"type": "json_object"}` with `reasoning_effort="low"`; a plain-call fallback covers endpoints that reject those params.
- Citations resolved by regex-matching `[S#]` markers in the answer against `brief.sources`, falling back to the full list.
- POC shortcut: all source text is stuffed into one call (no vector DB); `settings.mock_llm` provides a deterministic offline path including the decline case.

## Definition of Done
- [x] Answers are generated strictly from the brief plus loaded source documents
- [x] Every supported claim cites `[S#]` markers resolved back to the brief's sources
- [x] Unsupported questions return `grounded=false` with a graceful decline (no hallucination)
- [x] Response parsing is defensive: fence-stripping, JSON/raw handling, empty-answer fallback
- [x] JSON-mode call with a plain-call fallback; mock mode for offline demos
