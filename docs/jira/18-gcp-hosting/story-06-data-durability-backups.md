# SI-18.6 — Data durability & daily backups

| Field | Value |
|---|---|
| Issue type | Story |
| Parent epic | SI-18 — Free Cloud Hosting on GCP |
| Status | Done |
| Priority | Medium |
| Story points | 3 |
| Component | Deployment |
| Labels | deployment, backup, sqlite, reliability |

## User story
As the operator, I want the database to survive redeploys and to be **backed up daily**, so that the app's data is durable and recoverable on a single free-tier box.

## Description
Data durability rests on **placement plus backups**. The SQLite database lives on the VM's **persistent disk** at `/var/lib/salesintel/salesintel.db`, **outside the deploy dir**, so `deploy.sh` republishing code never clobbers it. A committed **`backup.sh`** runs from cron **daily** (`0 3 * * *`) and writes a **tarball** of the database **together with its `-wal` and `-shm` WAL sidecars** (capturing WAL sidecars matters so a backup taken mid-write is consistent) and the **prepared research cache** (`backend/.cache/`).

Even in the worst case the app is **regenerable**: because meetings come back from **Google calendar sync** and briefs are rebuilt by the **no-LLM prep** pipeline (Plane A web-to-doc + Plane B Zoho catalog), the durable state needed to reconstitute the app is small — the daily tarball plus the calendar is enough to bring it back.

## Acceptance criteria
```gherkin
Scenario: The database survives redeploys
  Given the DB lives at /var/lib/salesintel outside the deploy dir
  When deploy.sh republishes code and restarts services
  Then the database and its -wal/-shm sidecars are untouched
```

```gherkin
Scenario: A daily backup captures the DB and its WAL sidecars
  Given backup.sh runs from cron at 03:00 daily
  When it executes
  Then it writes a tarball of the database, its -wal and -shm sidecars, and the prepared research cache
```

```gherkin
Scenario: The app is regenerable after data loss
  Given only the daily tarball and the connected Google calendar remain
  When the app is restored
  Then meetings return via calendar sync
  And briefs are rebuilt by the no-LLM prep pipeline
```

## Technical notes (reference)
- Placement: DB at `/var/lib/salesintel/salesintel.db` (+ `-wal` / `-shm`) on the persistent disk, **outside** the deploy dir — redeploys never touch it.
- Backup: `deploy/backup.sh` via cron `0 3 * * *` — tarball of DB + WAL sidecars + `backend/.cache/` prepared research.
- Recoverability: meetings regenerate from Google calendar sync (SI-15); briefs rebuild from the no-LLM prep (SI-12/SI-13).

## Definition of Done
- [x] The database lives on the persistent disk outside the deploy dir so redeploys never clobber it.
- [x] `backup.sh` writes a daily tarball of the DB plus its `-wal`/`-shm` sidecars and the prepared research cache.
- [x] The backup is scheduled via cron (`0 3 * * *`).
- [x] The app is regenerable from calendar sync + the no-LLM prep pipeline in a worst-case restore.
