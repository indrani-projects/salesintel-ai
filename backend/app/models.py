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
    persona: str = "sales_rep"         # the meeting's primary/selected persona
    # Google Calendar link (set when imported from / pushed to Google). Used to
    # dedupe calendar syncs and to deep-link to the event.
    google_event_id: Optional[str] = Field(default=None, index=True)
    google_html_link: Optional[str] = None
    # Automated-email guards: when set, that email has already gone out for this
    # meeting (idempotency for the on-ready send and the 1-hour pre-meeting send).
    ready_email_sent_at: Optional[datetime] = None
    reminder_sent_at: Optional[datetime] = None


class Brief(SQLModel, table=True):
    # One brief per (meeting, persona) — a meeting can have a brief per persona.
    __table_args__ = (UniqueConstraint("meeting_id", "persona", name="uq_brief_meeting_persona"),)

    id: Optional[int] = Field(default=None, primary_key=True)
    meeting_id: int = Field(foreign_key="meeting.id", index=True)
    persona: str = "sales_rep"
    status: str = "pending"
    content_json: Optional[str] = None  # serialized BriefContent
    html: Optional[str] = None
    error: Optional[str] = None
    generated_at: Optional[datetime] = None


class AppState(SQLModel, table=True):
    # Single-row app state (POC): the currently signed-in user's persona. Set on login
    # and used server-side (e.g. calendar sync) so imported meetings + generation use
    # the active persona rather than a hardcoded default.
    id: Optional[int] = Field(default=1, primary_key=True)
    active_persona: str = "sales_rep"


class ChatMessage(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    meeting_id: int = Field(foreign_key="meeting.id", index=True)
    role: str
    content: str
    created_at: datetime = Field(default_factory=datetime.utcnow)


class GoogleToken(SQLModel, table=True):
    # Single-row store of the connected Google account's OAuth credentials (POC:
    # one rep). The refresh_token keeps the connection alive across restarts.
    id: Optional[int] = Field(default=None, primary_key=True)
    google_email: Optional[str] = None
    access_token: Optional[str] = None
    refresh_token: Optional[str] = None
    token_uri: str = "https://oauth2.googleapis.com/token"
    scopes: str = ""                    # space-separated granted scopes
    token_expiry: Optional[datetime] = None
    updated_at: datetime = Field(default_factory=datetime.utcnow)
