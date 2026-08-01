# SI-18.2 — SQLite WAL mode for concurrent daemon writes

| Field | Value |
|---|---|
| Issue type | Story |
| Parent epic | SI-18 — Free Cloud Hosting on GCP |
| Status | Done |
| Priority | High |
| Story points | 3 |
| Component | Deployment |
| Labels | deployment, backend, sqlite, reliability |

## User story
As the operator running the app on a single always-on box, I want SQLite to allow **concurrent reads and writes**, so that the background daemons can write while the request path reads without ever hitting "database is locked".

## Description
On the live VM two background daemons (the 30-second calendar sync and the 1-hour-before reminder email) run inside the same process as the request path and continually **write** to the database while the API **reads**. Default SQLite journaling serializes writers against readers and surfaces "database is locked" under this load. To fix it, `backend/app/db.py` enables **Write-Ahead Logging**: on **every** sqlite connection it sets **`PRAGMA journal_mode=WAL`** and **`PRAGMA synchronous=NORMAL`**, guarded to the **sqlite dialect** so non-sqlite backends are untouched.

This is a **runtime-only** change — **no schema change and no migration**. WAL lets readers and a writer proceed concurrently, which removes the lock contention on the free-tier single box. The database file lives at `/var/lib/salesintel/salesintel.db` and produces `-wal` and `-shm` sidecars that WAL uses for the log and shared-memory index (both captured by backups — see SI-18.6).

## Acceptance criteria
```gherkin
Scenario: WAL is enabled on every sqlite connection
  Given the app opens a sqlite connection
  When db.py runs its connection setup
  Then PRAGMA journal_mode=WAL and PRAGMA synchronous=NORMAL are applied
  And the pragmas are guarded to the sqlite dialect only
```

```gherkin
Scenario: Daemons write while the request path reads
  Given the calendar-sync and reminder daemons are writing
  When an API request reads from the database at the same time
  Then both proceed concurrently
  And no "database is locked" error is raised
```

```gherkin
Scenario: No schema change or migration
  Given WAL is a runtime pragma change
  When the change is deployed
  Then no database schema change or migration is required
```

```gherkin
Scenario: WAL mode is verifiable on the VM
  Given the live database at /var/lib/salesintel/salesintel.db
  When PRAGMA journal_mode is queried
  Then it returns wal
```

## Technical notes (reference)
- Key file: `backend/app/db.py` — sets `PRAGMA journal_mode=WAL` + `PRAGMA synchronous=NORMAL` on each sqlite connection, guarded to the sqlite dialect.
- Effect: concurrent daemon writes + request-path reads without "database is locked"; runtime-only, no migration.
- DB location: `/var/lib/salesintel/salesintel.db` (+ `-wal` / `-shm` sidecars), outside the deploy dir.
- Verify: `sqlite3 /var/lib/salesintel/salesintel.db 'PRAGMA journal_mode;'` → `wal`.

## Definition of Done
- [x] `db.py` sets `journal_mode=WAL` and `synchronous=NORMAL` on every sqlite connection.
- [x] The pragmas are guarded to the sqlite dialect so other backends are unaffected.
- [x] No schema change or migration is introduced.
- [x] Concurrent daemon writes and request-path reads no longer produce "database is locked".
- [x] `PRAGMA journal_mode` returns `wal` on the live database.
