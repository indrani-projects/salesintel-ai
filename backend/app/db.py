"""
Database engine + session management (SQLite via SQLModel).
"""
from __future__ import annotations

from sqlalchemy import event, text
from sqlmodel import Session, SQLModel, create_engine

from app.config import settings

engine = create_engine(
    settings.database_url,
    connect_args={"check_same_thread": False},
)


# SQLite pragmas, applied on every new connection. WAL (write-ahead logging) lets
# the request path READ while the background daemons (30s calendar sync + the
# pre-meeting reminder loop) WRITE, so overlapping access no longer trips
# "database is locked"; synchronous=NORMAL is the safe, fast pairing for WAL.
# journal_mode=WAL persists in the file header; re-issuing it per connection is a
# harmless no-op (and a no-op on :memory: DBs). Guarded to sqlite so pointing
# database_url at another engine later stays clean.
if engine.dialect.name == "sqlite":

    @event.listens_for(engine, "connect")
    def _sqlite_pragmas(dbapi_conn, _record) -> None:  # noqa: ANN001
        cur = dbapi_conn.cursor()
        cur.execute("PRAGMA journal_mode=WAL")
        cur.execute("PRAGMA synchronous=NORMAL")
        cur.close()

# Columns added to existing tables after first release. create_all() only CREATEs
# new tables/columns on fresh DBs — it never ALTERs an existing table — so we add
# these idempotently for DBs created before the column existed.
_ADDED_COLUMNS = {
    "meeting": {
        "google_event_id": "VARCHAR",
        "google_html_link": "VARCHAR",
        "ready_email_sent_at": "DATETIME",
        "reminder_sent_at": "DATETIME",
    },
}


def _ensure_columns() -> None:
    with engine.begin() as conn:
        for table, cols in _ADDED_COLUMNS.items():
            existing = {row[1] for row in conn.execute(text(f'PRAGMA table_info("{table}")'))}
            for name, decl in cols.items():
                if name not in existing:
                    conn.execute(text(f'ALTER TABLE "{table}" ADD COLUMN {name} {decl}'))


# Old persona codes -> their closest new persona. Meetings keep their row (persona
# remapped); their briefs used the old section sets and are dropped to regenerate.
_LEGACY_PERSONA_MAP = {"ae": "sales_rep", "sdr": "sales_rep", "se": "enablement"}


def _migrate_personas() -> None:
    """One-time remap of legacy persona values (ae/sdr/se) to the six-persona set.
    Guarded so it's a no-op once no legacy values remain. Stale briefs are deleted so
    they regenerate under the new section sets; affected meetings are marked pending."""
    from app.schemas import PERSONA_LABELS  # local import avoids any import cycle

    valid_csv = ", ".join(f"'{k}'" for k in PERSONA_LABELS)
    with engine.begin() as conn:
        legacy = conn.execute(text(
            "SELECT 1 FROM meeting WHERE persona NOT IN (" + valid_csv + ") "
            "UNION ALL SELECT 1 FROM brief WHERE persona NOT IN (" + valid_csv + ") LIMIT 1"
        )).first()
        if not legacy:
            return
        for old, new in _LEGACY_PERSONA_MAP.items():
            conn.execute(text("UPDATE meeting SET persona = :n WHERE persona = :o"),
                         {"n": new, "o": old})
        # Any remaining unknown persona -> default.
        conn.execute(text("UPDATE meeting SET persona = 'sales_rep' "
                          "WHERE persona NOT IN (" + valid_csv + ")"))
        # Drop stale briefs (old section sets) so they regenerate; then mark any
        # meeting left without a ready brief as pending for (re)generation.
        conn.execute(text("DELETE FROM brief WHERE persona NOT IN (" + valid_csv + ")"))
        conn.execute(text(
            "UPDATE meeting SET brief_status = 'pending' "
            "WHERE id NOT IN (SELECT meeting_id FROM brief WHERE status = 'ready')"
        ))


def init_db() -> None:
    """Create all tables, then apply lightweight column + data migrations."""
    import app.models  # noqa: F401  (registers tables on SQLModel.metadata)

    SQLModel.metadata.create_all(engine)
    _ensure_columns()
    _migrate_personas()


def get_session():
    """FastAPI dependency yielding a database Session."""
    with Session(engine) as session:
        yield session
