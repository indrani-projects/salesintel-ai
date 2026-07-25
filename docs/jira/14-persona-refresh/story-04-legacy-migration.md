# SI-14.4 — One-time legacy persona migration with brief regeneration

| Field | Value |
|---|---|
| Issue type | Story |
| Parent epic | SI-14 — Persona Refresh: the six personas from the persona doc (supersedes SI-4) |
| Status | Done |
| Priority | High |
| Story points | 5 |
| Component | Personas |
| Labels | backend, data |

## User story
As an existing user with meetings created under the old AE / SDR / SE personas, I want the app to keep working after the persona refresh, so that my meetings survive the switch and their briefs regenerate cleanly instead of breaking on an unknown persona value.

## Description
Replacing the persona set is not additive — it retires the `ae`, `sdr`, and `se` values that older Meeting and Brief rows still carry. This story adds a one-time, guarded migration, `db.py::_migrate_personas`, called from `init_db`, that reconciles that legacy data with the new six-persona contract without any manual step and without ever 500-ing on an unknown enum value.

The migration remaps old rows onto the new set — `ae` and `sdr` become `sales_rep`, and `se` becomes `enablement` — and drops stale brief rows whose section sets no longer match any current persona so they are regenerated cleanly against the new `PERSONA_SECTIONS`. Meetings affected by the remap are marked `pending` so the normal brief lifecycle regenerates them. Existing meetings are always preserved; only stale brief content is discarded. The migration is guarded so it is a no-op once no legacy persona values remain, making it safe to run on every startup. It ran live during the refresh: four existing meetings were remapped to `sales_rep` and their briefs regenerated to `ready`.

## Acceptance criteria
```gherkin
Scenario: Legacy persona values are remapped in place
  Given meeting and brief rows carrying legacy ae, sdr, or se personas
  When init_db runs the migration
  Then ae and sdr rows are remapped to sales_rep
  And se rows are remapped to enablement
  And the existing meetings are preserved
```
```gherkin
Scenario: Stale briefs are dropped and regenerated
  Given brief rows whose section sets no longer match any current persona
  When the migration runs
  Then those stale briefs are dropped
  And the affected meetings are marked pending so the lifecycle regenerates them
  And no request 500s on an unknown enum value
```
```gherkin
Scenario: The migration is guarded and idempotent (edge case)
  Given a database with no remaining legacy persona values
  When init_db runs again
  Then _migrate_personas is a no-op
  And running it repeatedly on startup is safe
```

## Technical notes (reference)
- Key file: `backend/app/db.py` — `_migrate_personas`, called from `init_db`; one-time, guarded, idempotent.
- Remap: `ae` → `sales_rep`, `sdr` → `sales_rep`, `se` → `enablement`.
- Stale briefs (old section sets) are dropped rather than migrated, so they regenerate against the new `PERSONA_SECTIONS`; affected meetings are marked `pending`.
- Existing meetings are never deleted; nothing 500s on the enum during or after migration.
- Verified live: four existing meetings remapped to `sales_rep`, briefs regenerated to `ready`.

## Definition of Done
- [x] `db.py::_migrate_personas` added and called from `init_db`.
- [x] Legacy `ae`/`sdr` remapped to `sales_rep`, `se` remapped to `enablement`, meetings preserved.
- [x] Stale briefs dropped and affected meetings marked `pending` so they regenerate.
- [x] Migration guarded so it is a no-op once no legacy values remain (safe on every startup).
- [x] No request 500s on an unknown enum value; live run remapped four meetings to `sales_rep` with briefs regenerated to `ready`.
