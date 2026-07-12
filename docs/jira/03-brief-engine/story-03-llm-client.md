# SI-3.3 — Swappable OpenAI-compatible LLM client

| Field | Value |
|---|---|
| Issue type | Story |
| Parent epic | SI-3 — AI Brief Generation Engine |
| Status | Done |
| Priority | High |
| Story points | 3 |
| Component | Brief Engine |
| Labels | backend, llm |

## User story
As an operator running the demo, I want to point the app at any OpenAI-compatible model provider by editing config, so that I can use a free hosted model for the demo or a fully offline local model without changing any code.

## Description
Every LLM call in the engine — brief synthesis and grounded chat alike — goes through one small client module. It constructs a single OpenAI-compatible client from configuration and exposes it, along with the configured model name, to the rest of the backend. Because the OpenAI Chat Completions shape is a de-facto standard, this one client works against a wide range of providers unchanged.

The point of centralizing it is swappability. The base URL, model name, and API key all come from `.env`, so switching providers is a config change, not a code change. The default is a free hosted tier (Gemini via its OpenAI-compatible endpoint) which keeps the demo zero-cost, and pointing the base URL at a local Ollama server runs the whole product offline. Nothing downstream knows or cares which provider is behind the client.

The module is also the single place where "no key configured" is handled sanely. Without a valid key the client can't make calls, but the server must still start and serve — briefs simply end up in an error state rather than the process failing. Keeping construction in one module means that behavior, plus any future retry/timeout tuning, has exactly one home instead of being scattered across the services that make calls.

## Acceptance criteria
```gherkin
Scenario: Provider is chosen by configuration
  Given LLM_BASE_URL, LLM_MODEL, and LLM_API_KEY are set in .env
  When the engine needs to call the model
  Then it uses the single OpenAI-compatible client built from those settings
  And no code change is needed to switch providers
```

```gherkin
Scenario: Offline operation via a local model
  Given LLM_BASE_URL points at a local Ollama server
  When a brief is generated
  Then the call is served by the local model with no external network dependency
```

```gherkin
Scenario: Missing key does not take down the server
  Given no valid LLM_API_KEY is configured
  When the app starts
  Then the server still runs and serves requests
  And brief generation fails into an error state rather than crashing the process
```

## Technical notes (reference)
- Key files: `backend/app/services/llm_client.py`, `backend/app/config.py` (`LLM_BASE_URL` / `LLM_MODEL` / `LLM_API_KEY`)
- Exposes `get_client()` and `get_model()`, consumed by `brief_engine.py` and `chat_service.py`.
- Default provider is Gemini's free tier via its OpenAI-compatible endpoint; repoint the base URL for Ollama/offline.
- POC framing: single client + `.env` swap instead of a provider-abstraction layer; sufficient because every target speaks the OpenAI Chat Completions shape.

## Definition of Done
- [x] Single OpenAI-compatible client constructed from `.env` settings
- [x] Base URL / model / key all configurable without code changes
- [x] Default Gemini free tier documented; Ollama offline path documented
- [x] Missing-key case leaves the server running (briefs go to error state)
