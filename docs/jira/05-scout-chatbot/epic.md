# EPIC SI-5 — Scout Chatbot (Grounded Q&A)

| Field | Value |
|---|---|
| Issue type | Epic |
| Suggested key | SI-5 |
| Status | Done |
| Priority | Medium |
| Component | Scout |
| Labels | backend, frontend, ai, llm, api, ux |
| Story points (rollup) | 10 |

## Summary
Scout is an embedded chatbot that answers a sales rep's follow-up questions grounded strictly in the generated brief and its source documents, cites those sources, and gracefully declines when the answer is not present.

## Description
Once a pre-sales brief is generated, a rep almost always has a follow-up question that the nine sections do not directly answer — "Who led their last funding round?", "What's the best opening line for this call?", "Do they already use a competing helpdesk?". Scout is the conversational layer that closes this gap. It is a per-meeting chat assistant, branded "Scout" in the UI, that sits alongside the brief and answers questions in natural language.

The defining constraint of Scout is that it is *grounded*. Every answer is drawn only from two places: the content of the brief itself and the freshly-loaded prospect and Zoho source documents for that account. Scout cites its evidence using inline `[S#]` markers that map back to the same source list shown on the brief. When a question cannot be supported by the available material, Scout does not guess — it sets a "not grounded" flag and tells the rep the answer isn't in the sources. This anti-hallucination behavior is the trust foundation of the whole POC: a rep can rely on what Scout says because it never invents facts about the prospect.

Conversation is stateful per meeting. Every user question and Scout answer is persisted as a `ChatMessage` row in SQLite, keyed to the meeting, so the thread survives page reloads and provides prior turns as context for follow-up questions. The backend is split into a thin API router that handles persistence and history, and a service layer that performs the grounded LLM synthesis and decline logic.

As a deliberate POC shortcut, Scout stuffs all relevant source text into a single LLM call rather than using a vector database for retrieval, and reads documents from a local `docs/` folder rather than a live datastore. This keeps the synthesis-quality story front and center without retrieval-infrastructure overhead.

## Stories in this epic
| Key | Story | Points | Priority |
|---|---|---|---|
| SI-5.1 | Chat API (post question + per-meeting history) | 2 | Medium |
| SI-5.2 | Grounded Q&A service with graceful decline | 5 | High |
| SI-5.3 | Scout chat panel UI | 3 | Medium |

## Epic acceptance criteria
```gherkin
Scenario: Rep asks a question answerable from the sources
  Given a meeting with a brief in status "ready"
  When the rep asks Scout "Who led their last funding round?"
  Then Scout returns a grounded answer citing the relevant [S#] sources
  And both the question and the answer are saved to the meeting's chat history
```

```gherkin
Scenario: Rep asks something not in the sources
  Given a meeting with a ready brief
  When the rep asks Scout a question the brief and sources do not cover
  Then Scout declines gracefully and states the answer is not in the available sources
  And the answer is flagged as not grounded rather than fabricating a response
```

```gherkin
Scenario: Chat history persists per meeting
  Given a rep has exchanged several messages with Scout for a meeting
  When the rep reloads the brief view
  Then the full prior conversation for that meeting is restored in order
```

## Out of scope
- Vector-database retrieval / semantic chunking (POC stuffs all source text into one call)
- Live web scraping or external data lookups beyond the local `docs/` folder
- Cross-meeting or account-wide memory (history is strictly per meeting)
- Streaming token-by-token responses

## Dependencies
- SI (Brief Generation epic) — Scout requires a `ready` brief with content and a source list to ground on
- SI (Source Ingestion epic) — `load_company_sources` supplies the source documents Scout reads
