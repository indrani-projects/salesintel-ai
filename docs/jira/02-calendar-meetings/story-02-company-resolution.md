# SI-2.2 — Company resolution & seeded prospect dropdown

| Field | Value |
|---|---|
| Issue type | Story |
| Parent epic | SI-2 — Calendar & Meeting Management |
| Status | Done |
| Priority | Medium |
| Story points | 3 |
| Component | Meetings |
| Labels | backend, data, frontend |

## User story
As a sales rep, I want to name my prospect naturally (or pick it from a short list) and still get the right company's briefing, so that I never have to know or type an internal folder name.

## Description
A meeting's prospect is free text — a rep types "The Sleep Company", not a database key. This story is the resolution layer that turns that human-friendly name into the knowledge folder the brief engine reads from. When a meeting is created, the backend calls `resolve_company_slug`, which normalizes the input (lower-cases it, strips a leading "the", collapses punctuation and whitespace, and joins words with underscores) and matches it against the folders under `docs/`. "The Sleep Company" resolves to the `sleep_company` slug. Matching is forgiving: it tries an exact slug match first, then a normalized match against both the folder name and its known display name.

The `zoho/` folder is special-cased throughout. It is never treated as a prospect company — it is excluded from the company list and from resolution — because it represents the internal Zoho product knowledge that is appended as shared context to every brief, regardless of which prospect the meeting is about. This is the mechanism behind the product's core promise: external prospect signal crossed with internal Zoho knowledge.

Display names come from `COMPANY_NAMES`, a small slug-to-name override map (e.g. `sleep_company` to "The Sleep Company"); slugs without an override are prettified generically. On the frontend, the add-meeting dialog offers a seeded dropdown of known prospects — populated from `GET /companies` — so the demo flow is one click, while still allowing free-text entry for anything not in the list. Company knowledge lives in a local `docs/` folder (a deliberate POC shortcut in place of live scraping): adding a new prospect is as simple as dropping a folder of documents under `docs/<slug>/`, with no code change.

## Acceptance criteria
```gherkin
Scenario: Free-text company name resolves to a docs slug
  Given a docs/sleep_company folder exists
  When a meeting is created with prospect company "The Sleep Company"
  Then resolve_company_slug returns "sleep_company"
  And the meeting stores that slug for brief generation
```

```gherkin
Scenario: Zoho is shared knowledge, never a prospect
  Given a docs/zoho folder exists
  When the company list is built and resolution runs
  Then zoho never appears as a selectable prospect
  And zoho documents are still appended to every brief as shared knowledge
```

```gherkin
Scenario: Seeded dropdown offers known prospects
  Given the add-meeting dialog is open
  When the company field is focused
  Then a dropdown of known prospects (from GET /companies) is shown
  And the rep may also type a free-text company name
```

```gherkin
Scenario: An unknown company resolves to nothing
  Given no matching docs folder exists for "Acme Robotics"
  When resolve_company_slug is called with "Acme Robotics"
  Then it returns None
  And the meeting is still created (its brief will surface an error/empty-source state)
```

## Technical notes (reference)
- Key files: `backend/app/services/sources.py` (`resolve_company_slug`, `_normalize`, `COMPANY_NAMES`, `list_companies`, `_is_company_folder`), `frontend/src/components/MeetingDialog.tsx` (seeded dropdown), `backend/app/api/meetings.py` (`GET /companies`)
- `_normalize` strips a leading "the ", maps non-alphanumerics to spaces, then joins words with underscores. Matching order: exact slug, then normalized folder name, then normalized display name.
- `_is_company_folder` excludes hidden/underscore-prefixed folders and `zoho`.
- POC shortcut: prospects are added by dropping `docs/<slug>/` folders — data, not code.

## Definition of Done
- [x] `resolve_company_slug("The Sleep Company")` returns `sleep_company`
- [x] Resolution is case-insensitive and tolerant of a leading "the" and punctuation
- [x] `zoho` is excluded from the prospect list and from resolution, but always shared
- [x] `COMPANY_NAMES` provides display-name overrides; other slugs prettified
- [x] The add-meeting dialog shows a seeded prospect dropdown while allowing free text
