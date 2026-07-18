# SI-11.2 — Filtered-intel cache (temporary, no LLM)

| Field | Value |
|---|---|
| Issue type | Story |
| Parent epic | SI-11 — Web-First Prospect Intel (generic, on-demand) + filtered cache |
| Status | Done |
| Priority | Medium |
| Story points | 3 |
| Component | Intelligence |
| Labels | backend, data, performance |

## User story
As the system, I want to cache the filtered web intel for a company on disk with a short TTL, so that repeated briefs, Scout turns, and persona toggles for the same prospect reuse it without re-fetching or spending extra API calls.

## Description
This story adds a temporary on-disk cache for the filtered web intel produced in SI-11.1, modeled on the existing PyMuPDF ingestion cache. Each company's filtered text is stored at `.cache/webintel/<sha256(name)>.json` as `{fetched_at, docs}` — the fetch timestamp plus the filtered documents.

Reads honor a **24h TTL** (`WEB_TTL_HOURS`) and a character budget (`web_max_chars`), both configurable. When a cache entry exists and is within the TTL, it is served directly: no web request and no API call. This is the "temporary memory" the chatbot reads from — a rep who opens a brief, toggles persona three times, and asks Scout five questions triggers exactly one fetch, then reuses the cache for everything that follows.

Writes are **best-effort**: a failure to write the cache never breaks the fetch or the brief. A `force` flag bypasses the cache to re-pull fresh intel on demand. Nothing here persists beyond the TTL window — the cache is explicitly temporary, not a datastore.

## Acceptance criteria
```gherkin
Scenario: Fresh fetch populates the cache
  Given no cached intel exists for a company
  When web intel is fetched
  Then the filtered docs are written to .cache/webintel/<sha256(name)>.json with fetched_at
```

```gherkin
Scenario: Within-TTL reuse avoids re-fetching
  Given a company's cache entry is younger than WEB_TTL_HOURS
  When another brief, Scout turn, or persona toggle runs for the same company
  Then the cached filtered text is returned
  And no web request or API call is made
```

```gherkin
Scenario: Expired cache triggers a re-fetch
  Given a company's cache entry is older than WEB_TTL_HOURS
  When web intel is requested
  Then a fresh fetch runs and the cache is rewritten
```

```gherkin
Scenario: Force re-pull bypasses the cache
  Given a valid cache entry exists
  When intel is requested with force
  Then the cache is bypassed and fresh intel is fetched
```

```gherkin
Scenario: Cache-write failure is non-fatal
  Given the cache file cannot be written
  When web intel is fetched
  Then the fetch still returns its results
  And no error is surfaced to the caller
```

## Technical notes (reference)
- Cache path: `.cache/webintel/<sha256(company_name)>.json`, payload `{fetched_at, docs}`.
- Config: `WEB_TTL_HOURS` (default 24h TTL), `web_max_chars` (character budget for stored/served text).
- Modeled on the existing ingestion cache; writes are best-effort (wrapped, never raise).
- `force` flag bypasses read to re-pull; TTL expiry triggers automatic re-fetch.
- Deliberately temporary — nothing persists past the TTL; this is the chatbot's short-lived working memory.

## Definition of Done
- [x] Filtered intel cached at `.cache/webintel/<sha256(name)>.json` as `{fetched_at, docs}`.
- [x] 24h TTL via `WEB_TTL_HOURS`; served text bounded by `web_max_chars`.
- [x] Within-TTL requests reuse the cache with zero re-fetch / zero extra API calls.
- [x] `force` re-pull and TTL-expiry re-fetch both supported.
- [x] Cache writes are best-effort and never break the fetch or brief.
