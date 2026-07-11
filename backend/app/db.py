"""
Database engine + session management (SQLite via SQLModel).
"""
from __future__ import annotations

from sqlmodel import Session, SQLModel, create_engine

from app.config import settings

engine = create_engine(
    settings.database_url,
    connect_args={"check_same_thread": False},
)


def init_db() -> None:
    """Create all tables. Import models first so metadata is populated."""
    import app.models  # noqa: F401  (registers tables on SQLModel.metadata)

    SQLModel.metadata.create_all(engine)


def get_session():
    """FastAPI dependency yielding a database Session."""
    with Session(engine) as session:
        yield session
