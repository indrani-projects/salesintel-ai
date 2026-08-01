#!/usr/bin/env bash
# Daily backup of the SQLite DB (+ WAL sidecars) and the prepared research cache.
# Installed as a root cron job by the runbook. Keeps the last 7 tarballs.
#   0 3 * * *  /opt/salesintel/deploy/backup.sh
set -euo pipefail

DB_DIR=/var/lib/salesintel
CACHE_DIR=/opt/salesintel/backend/.cache
OUT_DIR=/var/backups/salesintel
STAMP="$(date +%Y%m%d-%H%M%S)"

mkdir -p "$OUT_DIR"
# Checkpoint WAL into the main DB so the snapshot is self-consistent (best-effort).
sqlite3 "$DB_DIR/salesintel.db" 'PRAGMA wal_checkpoint(TRUNCATE);' 2>/dev/null || true

tar -czf "$OUT_DIR/salesintel-$STAMP.tar.gz" \
	-C / \
	"var/lib/salesintel" \
	"opt/salesintel/backend/.cache" 2>/dev/null || \
	tar -czf "$OUT_DIR/salesintel-$STAMP.tar.gz" -C / "var/lib/salesintel"

# Retention: keep the 7 newest.
ls -1t "$OUT_DIR"/salesintel-*.tar.gz | tail -n +8 | xargs -r rm -f
echo "backup -> $OUT_DIR/salesintel-$STAMP.tar.gz"
