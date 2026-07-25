"""Google integration API — OAuth connect + Calendar sync (one account, POC).

Endpoints:
  GET    /auth/google/login                     -> redirect to Google consent
  GET    /auth/google/callback                  -> exchange code, redirect to Settings
  GET    /integrations/google/status            -> GoogleStatus
  POST   /integrations/google/calendar/sync     -> import prospect events -> briefs
  DELETE /integrations/google/disconnect        -> forget the linked account
"""
from __future__ import annotations

import re
import time
from datetime import datetime, timedelta, timezone
from typing import Optional, Tuple

from fastapi import APIRouter, BackgroundTasks, HTTPException, Query, Response, status
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


# Display names for the enrichment companies (docs/shared research guide). These
# have NO docs/ folder — the web-first intel path builds their briefs by name.
_HINT_DISPLAY = {
    "freshworks": "Freshworks",
    "braze": "Braze",
    "sproutsocial": "Sprout Social",
    "amplitude": "Amplitude",
    "zuora": "Zuora",
}

# Words that mark a calendar event as a sales/prospect meeting (vs. a personal
# event). Used only for the generic "any company" fallback so we don't import
# "Lunch with Mom".
_MEETING_WORDS = re.compile(
    r"\b(call|meeting|sync|demo|intro\w*|discovery|pitch|deal|prospect|"
    r"brief\w*|kick[- ]?off|qbr|poc|review|catch[- ]?up|check[- ]?in|"
    r"onboard\w*|account|sales)\b",
    re.IGNORECASE,
)
# "... with <Company>" — capture the company that a meeting is *with*.
_WITH_RE = re.compile(r"\bwith\s+(.+)$", re.IGNORECASE)
# Trailing noise to trim off an extracted company name.
_TRAILING = re.compile(
    r"\s*\b(team|folks|group|call|meeting|sync|demo|about|re|regarding)\b.*$",
    re.IGNORECASE,
)


def _extract_company_from_title(summary: str) -> Optional[str]:
    """Best-effort generic company name from a sales-meeting-style title, e.g.
    'Discovery call with Acme Corp' -> 'Acme Corp'. Returns None if the title
    doesn't read like a prospect meeting (keeps personal events out)."""
    if not summary or not _MEETING_WORDS.search(summary):
        return None
    m = _WITH_RE.search(summary)
    if not m:
        return None
    cand = _TRAILING.sub("", m.group(1)).strip(" -–—:,")
    return cand or None


def _match_prospect(event: dict) -> Tuple[Optional[str], Optional[str]]:
    """Return (slug, display_name) if a prospect appears in the event.

    Three tiers, most-confident first:
      1. A company with a local docs/ folder (returns its slug).
      2. One of the enrichment companies from docs/shared (no slug -> web-first).
      3. Generic: any company named in a sales-meeting-style title (no slug).

    Matching uses the *normalized* name (lowercased, leading "the" dropped,
    non-alphanumerics -> underscores) so 'Discovery call with Sleep Company'
    still resolves to 'The Sleep Company'."""
    summary = event.get("summary", "") or ""
    hay = sources._normalize(
        " ".join(
            [summary, event.get("description", "")]
            + list(event.get("attendees", []))
        )
    )

    # 1) Known company with docs (highest confidence).
    for c in sources.list_companies():
        key = sources._normalize(c.name)  # "The Sleep Company" -> "sleep_company"
        if key and key in hay:
            return c.slug, c.name

    # 2) Enrichment company from the research guide (web-first, no docs folder).
    for name_key, display in _HINT_DISPLAY.items():
        if sources._normalize(display) in hay:
            return None, display

    # 3) Generic: extract any company from a sales-meeting-style title. The
    #    web-first intel path builds the brief by name (a company_hints entry, if
    #    one matches the extracted name, enriches it — but isn't required).
    name = _extract_company_from_title(summary)
    if name:
        return None, name

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


# Deletion reconciliation is bounded to the same window list_events() scans, so an
# imported meeting that's simply out of range is never mistaken for a deleted one.
_SYNC_DAYS_BACK = 1
_SYNC_DAYS_AHEAD = 30


def import_calendar_events() -> Tuple[int, int, int, int, int]:
    """Reconcile Google Calendar prospect events into meetings. New events are
    imported (primary brief queued 'pending'); events already imported are UPDATED
    in place if the rep edited them in Google (subject/time always; company change
    also requeues the brief so it rebuilds for the new prospect); unchanged events
    are skipped; and a meeting whose Google event was DELETED (no longer returned,
    within the sync window) is removed here too. Brief generation is NOT done here —
    it is handed to meetings_api.generate_pending_briefs so sync stays fast.

    Returns (scanned, imported, updated, skipped, deleted). Callers (the sync endpoint
    and the startup pass) trigger generate_pending_briefs after this returns."""
    events = google_service.list_events(_SYNC_DAYS_BACK, _SYNC_DAYS_AHEAD)
    scanned = len(events)
    live_ids = {e.get("id") for e in events if e.get("id")}
    imported = updated = skipped = deleted = 0

    with Session(engine) as session:
        for e in events:
            slug, name = _match_prospect(e)
            if not name:
                continue  # not a prospect — leave it in Google, don't import
            new_subject = e.get("summary", "") or f"Meeting with {name}"
            new_start = _parse_start(e.get("start"))
            existing = session.exec(
                select(models.Meeting).where(models.Meeting.google_event_id == e["id"])
            ).first()

            if existing is None:
                meetings_api.build_meeting_with_briefs(
                    session,
                    subject=new_subject,
                    prospect_company=name,
                    why="Imported from Google Calendar",
                    agenda=e.get("description", "") or "",
                    start_time=new_start,
                    # The signed-in user's persona — not a hardcoded default — so imported
                    # meetings generate only that persona's brief.
                    persona=meetings_api.get_active_persona(session),
                    primary_status="pending",  # queued for the background worker
                    google_event_id=e["id"],
                    google_html_link=e.get("html_link"),
                )
                imported += 1
                continue

            # Already imported — apply any edit the rep made in Google.
            company_changed = sources._normalize(existing.prospect_company) != sources._normalize(name)
            subject_changed = (existing.subject or "") != new_subject
            time_changed = existing.start_time != new_start
            if not (company_changed or subject_changed or time_changed):
                skipped += 1
                continue

            existing.subject = new_subject
            existing.start_time = new_start
            existing.agenda = e.get("description", "") or existing.agenda
            if e.get("html_link"):
                existing.google_html_link = e.get("html_link")
            if company_changed:
                existing.prospect_company = name
                existing.company_slug = slug or sources.resolve_company_slug(name)
                # Rebuild the brief for the new prospect.
                meetings_api.requeue_meeting_briefs(session, existing)
            session.add(existing)
            session.commit()
            updated += 1

        # Deletion reconciliation: a meeting linked to a Google event, whose start_time
        # is inside the sync window but whose event no longer appears, was deleted in
        # Google → remove it here too. `list_events` raises on failure (it never returns
        # a partial/empty list on error), so reaching this point means `live_ids` is
        # authoritative and it's safe to delete what's missing.
        now = datetime.utcnow()
        window_start = now - timedelta(days=_SYNC_DAYS_BACK)
        window_end = now + timedelta(days=_SYNC_DAYS_AHEAD)
        linked = session.exec(
            select(models.Meeting).where(
                models.Meeting.google_event_id != None,  # noqa: E711 (SQL IS NOT NULL)
                models.Meeting.start_time >= window_start,
                models.Meeting.start_time <= window_end,
            )
        ).all()
        for meeting in linked:
            if meeting.google_event_id not in live_ids:
                meetings_api.delete_meeting_cascade(session, meeting)
                deleted += 1
        if deleted:
            session.commit()

    return scanned, imported, updated, skipped, deleted


def _is_auth_error(exc: Exception) -> bool:
    """True when the failure is a dead/expired OAuth token (needs a reconnect)."""
    msg = str(exc).lower()
    return "invalid_grant" in msg or "expired" in msg or "revoked" in msg


def sync_calendar_once() -> Optional[Tuple[int, int, int, int, int]]:
    """One import pass + background-safe brief generation. Fail-soft: returns None on
    any error (e.g. an expired token) instead of raising, so the recurring scheduler
    never dies. Used by both the startup pass and the recurring loop."""
    try:
        if not google_service.is_connected():
            return None
        result = import_calendar_events()
        imported, updated, deleted = result[1], result[2], result[4]
        if imported or updated:
            meetings_api.generate_pending_briefs()
        if imported or updated or deleted:
            print(f"[calendar-sync] imported {imported}, updated {updated}, "
                  f"deleted {deleted}", flush=True)
        return result
    except Exception as exc:  # noqa: BLE001 — a bad token must not kill the loop
        hint = " (token expired/revoked — reconnect Google)" if _is_auth_error(exc) else ""
        print(f"[calendar-sync] pass failed: {exc}{hint}", flush=True)
        return None


def calendar_sync_loop() -> None:
    """Long-lived daemon: re-sync the calendar every `calendar_sync_seconds`."""
    interval = max(5, settings.calendar_sync_seconds)
    while True:
        sync_calendar_once()
        time.sleep(interval)


@router.post("/integrations/google/calendar/sync", response_model=CalendarSyncResult)
def calendar_sync(background_tasks: BackgroundTasks) -> CalendarSyncResult:
    """Import upcoming prospect events into meetings (fast), then kick off brief
    generation in the background (earliest meeting first). Non-prospect events are
    skipped; existing ones are deduped by google_event_id."""
    if not google_service.is_connected():
        raise HTTPException(status_code=400, detail="Google is not connected.")

    try:
        scanned, imported, updated, skipped, deleted = import_calendar_events()
    except Exception as exc:  # noqa: BLE001 — surface a clear error, never a raw 500
        if _is_auth_error(exc):
            raise HTTPException(
                status_code=400,
                detail="Google connection expired or was revoked — open Settings, "
                "Disconnect, then Connect Google again.",
            )
        raise HTTPException(status_code=502, detail=f"Calendar sync failed: {exc}")

    if imported or updated:
        background_tasks.add_task(meetings_api.generate_pending_briefs)

    changed = imported + updated
    deleted_note = f" Removed {deleted} deleted from Google." if deleted else ""
    return CalendarSyncResult(
        imported=imported,
        briefed=changed,
        skipped_existing=skipped,
        scanned=scanned,
        deleted=deleted,
        message=(
            f"Scanned {scanned} event(s); imported {imported} prospect meeting(s), "
            f"updated {updated} changed, {skipped} unchanged." + deleted_note + " "
            + (
                "Briefs are generating in the background."
                if changed
                else "Nothing to (re)brief."
            )
        ),
    )
