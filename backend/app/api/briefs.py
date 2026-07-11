"""
Brief retrieval API (per persona).
"""
from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlmodel import Session, select

from app import models
from app.api.meetings import generate_one_task
from app.db import get_session
from app.schemas import BriefContent, BriefRead, Persona

router = APIRouter(tags=["briefs"])


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
