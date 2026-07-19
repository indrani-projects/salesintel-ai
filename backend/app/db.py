"""
Database engine + session management (SQLite via SQLModel).
"""
from __future__ import annotations

from sqlalchemy import text
from sqlmodel import Session, SQLModel, create_engine

from app.config import settings

engine = create_engine(
    settings.database_url,
    connect_args={"check_same_thread": False},
)

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


def init_db() -> None:
    """Create all tables, then apply lightweight column migrations."""
    import app.models  # noqa: F401  (registers tables on SQLModel.metadata)

    SQLModel.metadata.create_all(engine)
    _ensure_columns()


def get_session():
    """FastAPI dependency yielding a database Session."""
    with Session(engine) as session:
        yield session
