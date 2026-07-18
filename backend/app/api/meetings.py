"""
Meetings API + per-persona brief-generation background tasks.

Each meeting has a *primary* persona (chosen at creation) plus AE/SDR/SE briefs
that are generated so the frontend "View as" toggle can switch between them. On
create, the primary persona is generated first, then the other two.
"""
from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Response, status
from sqlmodel import Session, select

from app import models
from app.db import engine, get_session
from app.schemas import CompanyRead, MeetingCreate, MeetingRead, Persona
from app.services import brief_engine, brief_render, sources

router = APIRouter(tags=["meetings"])

ALL_PERSONAS = ["ae", "sdr", "se"]


# --------------------------------------------------------------------------- #
# Background generation
# --------------------------------------------------------------------------- #
def _run_generation(meeting_id: int, persona: str) -> None:
    """Generate one persona's brief. Opens its OWN session. MUST catch all
    exceptions so a failure yields status="error" rather than crashing."""
    with Session(engine) as session:
        meeting = session.get(models.Meeting, meeting_id)
        brief = session.exec(
            select(models.Brief).where(
                models.Brief.meeting_id == meeting_id,
                models.Brief.persona == persona,
            )
        ).first()
        if meeting is None:
            return
        if brief is None:
            brief = models.Brief(meeting_id=meeting_id, persona=persona)
            session.add(brief)

        is_primary = persona == meeting.persona
        brief.status = "generating"
        if is_primary:
            meeting.brief_status = "generating"
        session.add(brief)
        session.add(meeting)
        session.commit()

        try:
            content = brief_engine.generate_brief(
                meeting.company_slug,
                meeting.subject,
                meeting.why,
                meeting.agenda,
                persona,
                company_name=meeting.prospect_company,
            )
            brief.content_json = content.model_dump_json()
            brief.html = brief_render.render_html(content)
            brief.status = "ready"
            brief.error = None
            brief.generated_at = datetime.utcnow()
            if is_primary:
                meeting.brief_status = "ready"
        except Exception as e:  # noqa: BLE001 — must never crash the server
            brief.status = "error"
            brief.error = str(e)[:1000]
            if is_primary:
                meeting.brief_status = "error"

        session.add(brief)
        session.add(meeting)
        session.commit()


def generate_one_task(meeting_id: int, persona: str) -> None:
    _run_generation(meeting_id, persona)


def build_meeting_with_briefs(
    session: Session,
    *,
    subject: str,
    prospect_company: str,
    start_time: datetime,
    why: str = "",
    agenda: str = "",
    persona: str = "ae",
    google_event_id: Optional[str] = None,
    google_html_link: Optional[str] = None,
) -> models.Meeting:
    """Create a Meeting and seed its three persona Brief rows. Does NOT schedule
    generation — the caller decides (BackgroundTasks for the API request, or a
    direct generate_one_task() call for the Google-sync background path). Reused by
    both create_meeting and the calendar importer so they stay in lockstep."""
    meeting = models.Meeting(
        subject=subject,
        prospect_company=prospect_company,
        company_slug=sources.resolve_company_slug(prospect_company),
        why=why,
        agenda=agenda,
        start_time=start_time,
        brief_status="generating",
        persona=persona,
        google_event_id=google_event_id,
        google_html_link=google_html_link,
    )
    session.add(meeting)
    session.commit()
    session.refresh(meeting)
    # Primary persona generates first; the other two are lazy (on first view).
    for p in ALL_PERSONAS:
        st = "generating" if p == persona else "pending"
        session.add(models.Brief(meeting_id=meeting.id, persona=p, status=st))
    meeting.brief_status = "generating"
    session.add(meeting)
    session.commit()
    session.refresh(meeting)
    return meeting


def _maybe_push_to_google(session: Session, meeting: models.Meeting) -> None:
    """If Google is connected, mirror the meeting to the user's calendar. Best-effort
    — never let a Google failure break meeting creation."""
    from app.services import google_service

    if meeting.google_event_id or not google_service.is_connected():
        return
    try:
        ev = google_service.insert_event(
            summary=meeting.subject,
            start=meeting.start_time,
            description=(meeting.why or ""),
        )
        meeting.google_event_id = ev.get("id")
        meeting.google_html_link = ev.get("html_link")
        session.add(meeting)
        session.commit()
        session.refresh(meeting)
    except Exception:  # noqa: BLE001 — creation must succeed regardless
        pass


# --------------------------------------------------------------------------- #
# Routes
# --------------------------------------------------------------------------- #
@router.post("/meetings", response_model=MeetingRead)
def create_meeting(
    body: MeetingCreate,
    background_tasks: BackgroundTasks,
    session: Session = Depends(get_session),
) -> models.Meeting:
    persona = body.persona.value if isinstance(body.persona, Persona) else str(body.persona)
    meeting = build_meeting_with_briefs(
        session,
        subject=body.subject,
        prospect_company=body.prospect_company,
        start_time=body.start_time,
        why=body.why,
        agenda=body.agenda,
        persona=persona,
    )
    _maybe_push_to_google(session, meeting)
    background_tasks.add_task(generate_one_task, meeting.id, persona)
    return meeting


@router.get("/meetings", response_model=List[MeetingRead])
def list_meetings(session: Session = Depends(get_session)) -> List[models.Meeting]:
    return list(
        session.exec(select(models.Meeting).order_by(models.Meeting.start_time)).all()
    )


@router.get("/meetings/{meeting_id}", response_model=MeetingRead)
def get_meeting(
    meeting_id: int, session: Session = Depends(get_session)
) -> models.Meeting:
    meeting = session.get(models.Meeting, meeting_id)
    if meeting is None:
        raise HTTPException(status_code=404, detail="Meeting not found")
    return meeting


@router.delete("/meetings/{meeting_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_meeting(
    meeting_id: int, session: Session = Depends(get_session)
) -> Response:
    meeting = session.get(models.Meeting, meeting_id)
    if meeting is None:
        raise HTTPException(status_code=404, detail="Meeting not found")

    for brief in session.exec(
        select(models.Brief).where(models.Brief.meeting_id == meeting_id)
    ).all():
        session.delete(brief)

    for msg in session.exec(
        select(models.ChatMessage).where(models.ChatMessage.meeting_id == meeting_id)
    ).all():
        session.delete(msg)

    session.delete(meeting)
    session.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/meetings/{meeting_id}/brief/regenerate", status_code=status.HTTP_202_ACCEPTED)
def regenerate_brief(
    meeting_id: int,
    background_tasks: BackgroundTasks,
    persona: Optional[Persona] = None,
    session: Session = Depends(get_session),
) -> dict:
    meeting = session.get(models.Meeting, meeting_id)
    if meeting is None:
        raise HTTPException(status_code=404, detail="Meeting not found")

    p = (persona.value if isinstance(persona, Persona) else persona) or meeting.persona

    brief = session.exec(
        select(models.Brief).where(
            models.Brief.meeting_id == meeting_id, models.Brief.persona == p
        )
    ).first()
    if brief is None:
        brief = models.Brief(meeting_id=meeting_id, persona=p)

    brief.status = "pending"
    brief.error = None
    brief.content_json = None
    brief.html = None
    brief.generated_at = None
    if p == meeting.persona:
        meeting.brief_status = "pending"
    session.add(brief)
    session.add(meeting)
    session.commit()

    background_tasks.add_task(generate_one_task, meeting_id, p)
    return {"status": "pending", "meeting_id": meeting_id, "persona": p}


@router.get("/companies", response_model=List[CompanyRead])
def get_companies() -> List[CompanyRead]:
    return sources.list_companies()
