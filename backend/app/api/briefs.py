"""
Brief retrieval API (per persona).
"""
from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlmodel import Session, select

from app import models
from app.api.meetings import generate_one_task
from app.config import settings
from app.db import get_session
from app.schemas import (
    BriefContent,
    BriefRead,
    EmailPreview,
    EmailSendRequest,
    EmailSendResult,
    Persona,
)
from app.services import email_service

router = APIRouter(tags=["briefs"])


def _ready_brief_content(
    session: Session, meeting_id: int, persona: Optional[Persona]
) -> BriefContent:
    """Load a READY brief's content for (meeting, persona), or raise HTTP errors."""
    meeting = session.get(models.Meeting, meeting_id)
    if meeting is None:
        raise HTTPException(status_code=404, detail="Meeting not found")
    p = (persona.value if isinstance(persona, Persona) else persona) or meeting.persona
    brief = session.exec(
        select(models.Brief).where(
            models.Brief.meeting_id == meeting_id, models.Brief.persona == p
        )
    ).first()
    if brief is None or brief.status != "ready" or not brief.content_json:
        raise HTTPException(
            status_code=409, detail="Brief is not ready yet for this persona."
        )
    return BriefContent.model_validate_json(brief.content_json)


@router.get("/meetings/{meeting_id}/brief", response_model=BriefRead)
def get_brief(
    meeting_id: int,
    background_tasks: BackgroundTasks,
    persona: Optional[Persona] = None,
    session: Session = Depends(get_session),
) -> BriefRead:
    meeting = session.get(models.Meeting, meeting_id)
    if meeting is None:
        raise HTTPException(status_code=404, detail="Meeting not found")

    p = (persona.value if isinstance(persona, Persona) else persona) or meeting.persona

    brief = session.exec(
        select(models.Brief).where(
            models.Brief.meeting_id == meeting_id, models.Brief.persona == p
        )
    ).first()

    # No row yet, or a not-yet-started ("pending") persona → generate it lazily on
    # first view. Flip to "generating" so repeated polls don't re-schedule.
    if brief is None or brief.status == "pending":
        if brief is None:
            brief = models.Brief(meeting_id=meeting_id, persona=p)
        brief.status = "generating"
        session.add(brief)
        session.commit()
        background_tasks.add_task(generate_one_task, meeting_id, p)
        return BriefRead(meeting_id=meeting_id, persona=p, status="generating")

    result = BriefRead(meeting_id=meeting_id, persona=p, status=brief.status)
    if brief.status == "ready" and brief.content_json:
        result.content = BriefContent.model_validate_json(brief.content_json)
        result.html = brief.html
    elif brief.status == "error":
        result.error = brief.error
    return result


@router.get("/meetings/{meeting_id}/brief/email/preview", response_model=EmailPreview)
def preview_brief_email(
    meeting_id: int,
    persona: Optional[Persona] = None,
    session: Session = Depends(get_session),
) -> EmailPreview:
    """Compose the persona-tailored email for review — does NOT send anything."""
    content = _ready_brief_content(session, meeting_id, persona)
    composed = email_service.compose_brief_email(content)
    return EmailPreview(
        subject=composed.subject,
        body_html=composed.body_html,
        attachment_filename=composed.attachment_filename,
        recipient_default=settings.default_recipient,
        email_configured=settings.email_configured and not settings.mock_email,
    )


@router.post("/meetings/{meeting_id}/brief/email/send", response_model=EmailSendResult)
def send_brief_email(
    meeting_id: int,
    payload: EmailSendRequest,
    persona: Optional[Persona] = None,
    session: Session = Depends(get_session),
) -> EmailSendResult:
    """Compose + send the email (real when SMTP configured, else demo-send)."""
    content = _ready_brief_content(session, meeting_id, persona)
    composed = email_service.compose_brief_email(content)
    return email_service.send_brief_email(composed, payload.recipient)
