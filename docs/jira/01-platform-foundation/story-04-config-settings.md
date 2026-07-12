# SI-1.4 — Configuration & swappable LLM provider settings

| Field | Value |
|---|---|
| Issue type | Story |
| Parent epic | SI-1 — Platform Foundation & Data Contract |
| Status | Done |
| Priority | High |
| Story points | 3 |
| Component | Platform |
| Labels | backend, infra |

## User story
As an operator setting up the demo, I want all runtime configuration to come from a single `.env`-driven settings object with a swappable LLM provider, so that I can point the app at Gemini, a local Ollama, or any OpenAI-compatible endpoint without touching code — and run the server even before I have a key.

## Description
This story centralizes every runtime setting into one typed configuration object built on `pydantic-settings`. Values are read from `backend/.env` (with `.env.example` documenting each one) and map case-insensitively from upper-snake environment variable names. Because the whole app imports this single `settings` object, there is exactly one place to look for how the system is configured and no scattered constants.

The headline capability is a **swappable LLM provider**. The app talks to any OpenAI-compatible endpoint, chosen entirely through three settings: `LLM_BASE_URL`, `LLM_MODEL`, and `LLM_API_KEY`. The default is Google's Gemini free tier, but pointing `LLM_BASE_URL` at a local Ollama instance runs the whole thing offline — no code change required. This is the demo's proof that the intelligence layer is not welded to one vendor. Other settings cover the database URL, the `DOCS_ROOT` path to the local source-document folder, and the `CORS_ORIGINS` list consumed by the app shell. A path helper resolves `DOCS_ROOT` to an absolute location whether it is given as absolute or relative.

A deliberate design point: the server must run even with **no LLM key**. The settings object exposes a derived `llm_configured` flag (true only when a real, non-placeholder key is present). When it is false, the server still starts and stays healthy — briefs simply fail gracefully to `status = error` instead of crashing anything. This keeps the app demoable and debuggable at every stage of setup. The configuration also carries mock toggles (for deterministic test/E2E runs) and the SMTP/email settings for the "Send as email" feature, all defaulting to safe, offline behavior.

## Acceptance criteria

**Scenario: Configuration loads from the environment file**
```gherkin
Given a backend/.env populated from .env.example
When the application starts
Then all settings load from that file with correct types and defaults
```

**Scenario: The LLM provider is swappable without code changes**
```gherkin
Given LLM_BASE_URL, LLM_MODEL, and LLM_API_KEY in the environment
When the operator points LLM_BASE_URL at a local Ollama instead of the default Gemini
Then the app uses the new endpoint with no source changes
```

**Scenario: The server runs without an LLM key**
```gherkin
Given no LLM_API_KEY (or a placeholder value) is set
When the server starts
Then llm_configured is false and the server runs normally
And brief generation degrades to status = error rather than crashing
```

**Scenario: Docs root resolves regardless of form**
```gherkin
Given DOCS_ROOT set to a relative path
When a service needs the documents folder
Then the configured path resolves to an absolute location on disk
```

## Technical notes (reference)
- Key files: `backend/app/config.py`, `backend/.env.example`
- Built on `pydantic-settings`; env vars are upper-snake and map case-insensitively to fields.
- LLM settings: `LLM_BASE_URL` / `LLM_MODEL` / `LLM_API_KEY` (default Gemini flash; OpenAI-compatible, Ollama-friendly).
- App settings: `DATABASE_URL`, `DOCS_ROOT` (with an absolute-path resolver), `CORS_ORIGINS` (exposed as a parsed list).
- Derived flags: `llm_configured` guards on a real, non-placeholder key; `mock_llm` / `mock_email` force deterministic offline behavior for tests and E2E.
- Also holds the SMTP/email settings for the "Send as email" feature, defaulting to offline demo-send.

## Definition of Done
- [x] Single `Settings` object built on `pydantic-settings`, imported app-wide.
- [x] LLM base URL, model, and key are configurable; default is Gemini, swappable to any OpenAI-compatible endpoint.
- [x] `DOCS_ROOT` and `CORS_ORIGINS` settings present, with helpers for absolute path and parsed origin list.
- [x] `llm_configured` flag lets the server run keyless with briefs degrading to error.
- [x] `.env.example` documents every setting.
