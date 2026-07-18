"""Google integration API — OAuth connect + Calendar sync (one account, POC).

Endpoints:
  GET    /auth/google/login                     -> redirect to Google consent
  GET    /auth/google/callback                  -> exchange code, redirect to Settings
  GET    /integrations/google/status            -> GoogleStatus
  POST   /integrations/google/calendar/sync     -> import prospect events -> briefs
  DELETE /integrations/google/disconnect        -> forget the linked account
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional, Tuple

from fastapi import APIRouter, HTTPException, Query, Response, status
from fastapi.responses import RedirectResponse
from sqlmodel import Session, select

from app import models
from app.api import meetings as meetings_api
from app.config import settings
from app.db import engine
from app.schemas import CalendarSyncResult, GoogleStatus
from app.services import google_service, sources

router = APIRouter(tags=["google"])


@router.get("/auth/google/login")
def google_login():
    if not settings.google_configured:
        raise HTTPException(
            status_code=400,
            detail="Google OAuth is not configured — set GOOGLE_CLIENT_ID / "
            "GOOGLE_CLIENT_SECRET in backend/.env (see docs/RUNBOOK.md).",
        )
    return RedirectResponse(google_service.authorization_url())


@router.get("/auth/google/callback")
def google_callback(code: Optional[str] = Query(None), error: Optional[str] = Query(None)):
    dest = settings.frontend_url.rstrip("/") + "/settings"
    if error or not code:
        print(f"[google] callback returned error param: {error!r}", flush=True)
        return RedirectResponse(f"{dest}?google=error")
    try:
        google_service.exchange_code(code)
    except Exception as exc:  # noqa: BLE001
        import traceback
        traceback.print_exc()
        print(f"[google] exchange_code failed: {type(exc).__name__}: {exc}", flush=True)
        return RedirectResponse(f"{dest}?google=error")
    return RedirectResponse(f"{dest}?google=connected")


@router.get("/integrations/google/status", response_model=GoogleStatus)
def google_status() -> GoogleStatus:
    return GoogleStatus(**google_service.status())


@router.delete("/integrations/google/disconnect", status_code=status.HTTP_204_NO_CONTENT)
def google_disconnect() -> Response:
    google_service.disconnect()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


def _match_prospect(event: dict) -> Tuple[Optional[str], Optional[str]]:
    """Return (slug, display_name) if a known prospect appears in the event.

    Matches on the *normalized* company name (lowercased, leading "the" dropped,
    non-alphanumerics -> underscores) so titles like "Discovery call with Sleep
    Company" still resolve to "The Sleep Company" (slug sleep_company)."""
    hay = sources._normalize(
        " ".join(
            [event.get("summary", ""), event.get("description", "")]
            + list(event.get("attendees", []))
        )
    )
    for c in sources.list_companies():
        key = sources._normalize(c.name)  # "The Sleep Company" -> "sleep_company"
        if key and key in hay:
            return c.slug, c.name
    return None, None


def _parse_start(s: Optional[str]) -> datetime:
    if not s:
        return datetime.utcnow()
    try:
        if len(s) == 10:  # all-day event: "YYYY-MM-DD"
            return datetime.fromisoformat(s + "T09:00:00")
        dt = datetime.fromisoformat(s.replace("Z", "+00:00"))
        if dt.tzinfo is not None:
            dt = dt.astimezone(timezone.utc).replace(tzinfo=None)
        return dt
    except Exception:
        return datetime.utcnow()


@router.post("/integrations/google/calendar/sync", response_model=CalendarSyncResult)
def calendar_sync() -> CalendarSyncResult:
    """Import upcoming Google Calendar events that match a known prospect into
    meetings (+ briefs). Deduped by google_event_id; non-prospect events are skipped."""
    if not google_service.is_connected():
        raise HTTPException(status_code=400, detail="Google is not connected.")

    events = google_service.list_events()
    scanned = len(events)
    imported = skipped = 0

    with Session(engine) as session:
        for e in events:
            slug, name = _match_prospect(e)
            if not slug:
                continue  # not a known prospect — leave it in Google, don't import
            exists = session.exec(
                select(models.Meeting).where(models.Meeting.google_event_id == e["id"])
            ).first()
            if exists:
                skipped += 1
                continue
            meeting = meetings_api.build_meeting_with_briefs(
                session,
                subject=e.get("summary", "") or f"Meeting with {name}",
                prospect_company=name,
                why="Imported from Google Calendar",
                agenda=e.get("description", "") or "",
                start_time=_parse_start(e.get("start")),
                persona="ae",
                google_event_id=e["id"],
                google_html_link=e.get("html_link"),
            )
            # Background poller has no BackgroundTasks — generate_one_task opens its
            # own session and runs synchronously here.
            meetings_api.generate_one_task(meeting.id, "ae")
            imported += 1

    return CalendarSyncResult(
        imported=imported,
        briefed=imported,
        skipped_existing=skipped,
        scanned=scanned,
        message=f"Scanned {scanned} event(s); imported {imported} prospect meeting(s), "
        f"{skipped} already present.",
    )
