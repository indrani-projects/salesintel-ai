"""
Meetings API + per-persona brief-generation background tasks.

Each meeting has a *primary* persona (chosen at creation) plus AE/SDR/SE briefs
that are generated so the frontend "View as" toggle can switch between them. On
create, the primary persona is generated first, then the other two.
"""
from __future__ import annotations

import threading
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Response, status
from sqlmodel import Session, select

from app import models
from app.config import settings
from app.db import engine, get_session
from app.schemas import CompanyRead, MeetingCreate, MeetingRead, Persona
from app.services import brief_engine, brief_render, sources

router = APIRouter(tags=["meetings"])

# Fan-out set — one brief per persona. Derived from the enum so it stays in sync.
ALL_PERSONAS = [p.value for p in Persona]


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
        became_ready = is_primary and brief.status == "ready"

    # Auto-email the brief the moment the PRIMARY persona is ready (outside the
    # session, so the row is durable). Gated by the master switch; fail-soft inside.
    if became_ready and settings.auto_email_enabled:
        from app.services import notifier

        notifier.send_ready_email(meeting_id)


def generate_one_task(meeting_id: int, persona: str) -> None:
    _run_generation(meeting_id, persona)


# --------------------------------------------------------------------------- #
# Background brief-generation worker (date-ordered queue)
# --------------------------------------------------------------------------- #
# Calendar sync and startup only *import* meetings (primary brief left "pending").
# This worker drains that queue in start_time-ascending order, one meeting at a
# time. It is serialized by a lock so overlapping triggers (a sync click while the
# startup pass is running) never double-generate; a rerun flag makes a trigger that
# arrives mid-pass get honored instead of dropped.
_gen_lock = threading.Lock()
_gen_rerun = threading.Event()


def _next_pending_meeting() -> Optional[tuple[int, str]]:
    """The earliest meeting whose primary brief is still queued, as (id, persona)."""
    with Session(engine) as session:
        meeting = session.exec(
            select(models.Meeting)
            .where(models.Meeting.brief_status == "pending")
            .order_by(models.Meeting.start_time)
        ).first()
        if meeting is None:
            return None
        return meeting.id, meeting.persona


def generate_pending_briefs() -> None:
    """Generate the primary brief for every meeting queued as 'pending', earliest
    meeting first. Safe to call from anywhere (BackgroundTasks, a startup thread);
    only one pass runs at a time and it always drains everything left pending."""
    _gen_rerun.set()
    if not _gen_lock.acquire(blocking=False):
        return  # a pass is already running; it will honor the rerun flag
    try:
        while _gen_rerun.is_set():
            _gen_rerun.clear()
            while True:
                nxt = _next_pending_meeting()
                if nxt is None:
                    break
                meeting_id, persona = nxt
                # generate_one_task flips the row to generating -> ready|error, so
                # the next query won't re-select it (no infinite loop on failure).
                generate_one_task(meeting_id, persona)
    finally:
        _gen_lock.release()


def generate_persona_briefs(persona: str) -> int:
    """Ensure the given persona's brief exists + is ready for EVERY meeting. Used when
    a user logs in with a selected persona so that persona's briefs are generated
    automatically. Skips meetings whose persona brief is already ready; each generation
    is exception-safe. Returns how many were (re)generated."""
    with Session(engine) as session:
        meeting_ids = [m.id for m in session.exec(select(models.Meeting)).all()]

    generated = 0
    for mid in meeting_ids:
        with Session(engine) as s:
            existing = s.exec(
                select(models.Brief).where(
                    models.Brief.meeting_id == mid,
                    models.Brief.persona == persona,
                )
            ).first()
            if existing is not None and existing.status == "ready":
                continue
        _run_generation(mid, persona)  # own session, fail-soft
        generated += 1
    return generated


def requeue_meeting_briefs(session: Session, meeting: models.Meeting) -> None:
    """Reset a meeting's briefs to queued and clear their content — used when a
    calendar edit changed the prospect company, so generate_pending_briefs rebuilds
    the primary brief for the new company (the other personas stay lazy)."""
    for b in session.exec(
        select(models.Brief).where(models.Brief.meeting_id == meeting.id)
    ).all():
        b.status = "pending"
        b.content_json = None
        b.html = None
        b.error = None
        b.generated_at = None
        session.add(b)
    meeting.brief_status = "pending"
    session.add(meeting)


def reset_stale_generating() -> int:
    """On startup, any brief left 'generating' by a killed process has no worker
    behind it — requeue it as 'pending' so the date-ordered worker picks it up.
    Returns how many meetings were requeued. Must run only at startup (never while
    a live generation is in flight)."""
    n = 0
    with Session(engine) as session:
        stale = session.exec(
            select(models.Meeting).where(models.Meeting.brief_status == "generating")
        ).all()
        for meeting in stale:
            meeting.brief_status = "pending"
            session.add(meeting)
            primary = session.exec(
                select(models.Brief).where(
                    models.Brief.meeting_id == meeting.id,
                    models.Brief.persona == meeting.persona,
                )
            ).first()
            if primary is not None:
                primary.status = "pending"
                session.add(primary)
            n += 1
        session.commit()
    return n


def build_meeting_with_briefs(
    session: Session,
    *,
    subject: str,
    prospect_company: str,
    start_time: datetime,
    why: str = "",
    agenda: str = "",
    persona: str = "sales_rep",
    primary_status: str = "generating",
    google_event_id: Optional[str] = None,
    google_html_link: Optional[str] = None,
) -> models.Meeting:
    """Create a Meeting and seed its three persona Brief rows. Does NOT run
    generation — the caller decides how: create_meeting schedules the primary brief
    immediately (primary_status="generating" + a BackgroundTask), while the calendar
    importer only queues it (primary_status="pending") for the date-ordered
    generate_pending_briefs worker to pick up. Reused by both so they stay in
    lockstep."""
    meeting = models.Meeting(
        subject=subject,
        prospect_company=prospect_company,
        company_slug=sources.resolve_company_slug(prospect_company),
        why=why,
        agenda=agenda,
        start_time=start_time,
        brief_status=primary_status,
        persona=persona,
        google_event_id=google_event_id,
        google_html_link=google_html_link,
    )
    session.add(meeting)
    session.commit()
    session.refresh(meeting)
    # Primary persona uses primary_status; the other two are lazy (on first view).
    for p in ALL_PERSONAS:
        st = primary_status if p == persona else "pending"
        session.add(models.Brief(meeting_id=meeting.id, persona=p, status=st))
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


def delete_meeting_cascade(session: Session, meeting: models.Meeting) -> None:
    """Delete a meeting and its briefs + chat messages. Does NOT commit — the caller
    commits (so callers can delete several in one transaction)."""
    mid = meeting.id
    for brief in session.exec(
        select(models.Brief).where(models.Brief.meeting_id == mid)
    ).all():
        session.delete(brief)
    for msg in session.exec(
        select(models.ChatMessage).where(models.ChatMessage.meeting_id == mid)
    ).all():
        session.delete(msg)
    session.delete(meeting)


@router.delete("/meetings/{meeting_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_meeting(
    meeting_id: int, session: Session = Depends(get_session)
) -> Response:
    meeting = session.get(models.Meeting, meeting_id)
    if meeting is None:
        raise HTTPException(status_code=404, detail="Meeting not found")

    delete_meeting_cascade(session, meeting)
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


@router.post("/briefs/generate", status_code=status.HTTP_202_ACCEPTED)
def generate_briefs_for_persona(
    persona: Persona, background_tasks: BackgroundTasks
) -> dict:
    """Queue generation of the given persona's brief across ALL meetings (background,
    earliest first). Called on login so the selected persona's briefs are generated
    automatically. Idempotent — meetings already ready for that persona are skipped."""
    background_tasks.add_task(generate_persona_briefs, persona.value)
    return {"queued": True, "persona": persona.value}
