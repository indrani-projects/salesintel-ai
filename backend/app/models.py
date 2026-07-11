"""
SQLModel database tables for SalesIntel_AI.

These are the persistence-layer models (distinct from the API DTOs in
schemas.py). Statuses are stored as plain strings mirroring
schemas.BriefStatus values ("pending" | "generating" | "ready" | "error").
"""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import UniqueConstraint
from sqlmodel import Field, SQLModel


class Meeting(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    subject: str
    prospect_company: str
    company_slug: Optional[str] = None
    why: str = ""
    agenda: str = ""
    start_time: datetime
    created_at: datetime = Field(default_factory=datetime.utcnow)
    brief_status: str = "pending"      # mirrors the PRIMARY persona's brief status
    persona: str = "ae"                # the meeting's primary/selected persona


class Brief(SQLModel, table=True):
    # One brief per (meeting, persona) — a meeting can have AE / SDR / SE briefs.
    __table_args__ = (UniqueConstraint("meeting_id", "persona", name="uq_brief_meeting_persona"),)

    id: Optional[int] = Field(default=None, primary_key=True)
    meeting_id: int = Field(foreign_key="meeting.id", index=True)
    persona: str = "ae"
    status: str = "pending"
    content_json: Optional[str] = None  # serialized BriefContent
    html: Optional[str] = None
    error: Optional[str] = None
    generated_at: Optional[datetime] = None


class ChatMessage(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    meeting_id: int = Field(foreign_key="meeting.id", index=True)
    role: str
    content: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
