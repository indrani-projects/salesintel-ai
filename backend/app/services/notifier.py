"""Automated brief emails — two triggers, both reusing the manual "Send as email"
path (compose_brief_email + send_brief_email):

  1. on-ready  — email a meeting's primary brief the moment it flips to `ready`
                 (called from meetings._run_generation).
  2. reminder  — email it again `reminder_lead_minutes` before start_time
                 (a background poll loop started at app startup).

Recipient is `settings.default_recipient` (the rep emails the brief to themselves);
blank ⇒ auto-send is skipped. Idempotency is per-meeting via two guard columns
(Meeting.ready_email_sent_at / reminder_sent_at). Everything here is fail-soft — an
email problem never propagates to brief generation or kills the poll loop.

These functions do NOT check settings.auto_email_enabled themselves — the callers
(the generation hook and the startup thread) gate on it, so tests can drive the
functions directly with the master switch off.
"""
from __future__ import annotations

import time
from datetime import datetime, timedelta
from typing import Optional

from sqlmodel import Session, select

from app import models
from app.config import settings
from app.db import engine
from app.schemas import BriefContent
from app.services import email_service


def _transport() -> str:
    """How a send would deliver right now: gmail | smtp | demo."""
    from app.services import google_service

    if settings.mock_email:
        return "demo"
    if google_service.is_connected():
        return "gmail"
    if settings.email_configured:
        return "smtp"
    return "demo"


def automation_status() -> dict:
    """Read-only settings snapshot for the Settings page / API."""
    return {
        "enabled": settings.auto_email_enabled,
        "lead_minutes": settings.reminder_lead_minutes,
        "recipient": (settings.default_recipient or "").strip(),
        "transport": _transport(),
    }


def _load_ready_primary(session: Session, meeting: models.Meeting) -> Optional[BriefContent]:
    """The meeting's primary-persona brief content if it's ready, else None."""
    brief = session.exec(
        select(models.Brief).where(
            models.Brief.meeting_id == meeting.id,
            models.Brief.persona == meeting.persona,
        )
    ).first()
    if brief is None or brief.status != "ready" or not brief.content_json:
        return None
    try:
        return BriefContent.model_validate_json(brief.content_json)
    except Exception:  # noqa: BLE001 — a corrupt brief must not break auto-email
        return None


def _send(content: BriefContent, recipient: str, subject_override: Optional[str] = None):
    """Compose + send the brief email, optionally with a custom subject."""
    composed = email_service.compose_brief_email(content)
    if subject_override:
        composed.subject = subject_override
    return email_service.send_brief_email(composed, recipient)


def send_ready_email(meeting_id: int) -> None:
    """Email a meeting's brief once, when it becomes ready. No-op unless the brief is
    ready, the meeting is still upcoming, and it hasn't already been sent. If the
    meeting is already inside the reminder window, this send also satisfies the
    reminder (stamps reminder_sent_at) so the scheduler won't re-send minutes later."""
    recipient = (settings.default_recipient or "").strip()
    if not recipient:
        print("[auto-email] DEFAULT_RECIPIENT is blank — skipping ready email", flush=True)
        return

    now = datetime.utcnow()
    try:
        with Session(engine) as session:
            meeting = session.get(models.Meeting, meeting_id)
            if meeting is None or meeting.ready_email_sent_at is not None:
                return
            if meeting.start_time is None or meeting.start_time <= now:
                return  # only email upcoming meetings
            content = _load_ready_primary(session, meeting)
            if content is None:
                return

            result = _send(content, recipient)
            if result.mode != "error":
                meeting.ready_email_sent_at = now
                lead = timedelta(minutes=settings.reminder_lead_minutes)
                if meeting.reminder_sent_at is None and meeting.start_time <= now + lead:
                    meeting.reminder_sent_at = now  # doubles as the reminder
                session.add(meeting)
                session.commit()
            print(
                f"[auto-email] ready email for meeting {meeting_id} "
                f"({meeting.prospect_company}): {result.mode}",
                flush=True,
            )
    except Exception as exc:  # noqa: BLE001 — never disturb brief generation
        print(f"[auto-email] send_ready_email({meeting_id}) failed: {exc}", flush=True)


def send_due_reminders() -> int:
    """Send the 1-hour reminder for every upcoming ready meeting now inside the lead
    window that hasn't been reminded yet. Returns how many were sent. Per-meeting
    fail-soft so one bad send never blocks the rest."""
    recipient = (settings.default_recipient or "").strip()
    if not recipient:
        return 0

    now = datetime.utcnow()
    window_end = now + timedelta(minutes=settings.reminder_lead_minutes)
    sent = 0
    with Session(engine) as session:
        due = session.exec(
            select(models.Meeting)
            .where(
                models.Meeting.brief_status == "ready",
                models.Meeting.reminder_sent_at == None,  # noqa: E711 (SQL IS NULL)
                models.Meeting.start_time > now,
                models.Meeting.start_time <= window_end,
            )
            .order_by(models.Meeting.start_time)
        ).all()

        for meeting in due:
            try:
                content = _load_ready_primary(session, meeting)
                if content is None:
                    continue
                company = content.company or meeting.prospect_company or "your prospect"
                subject = (
                    f"[SalesIntel] Reminder — {company} meeting in "
                    f"~{settings.reminder_lead_minutes} min"
                )
                result = _send(content, recipient, subject_override=subject)
                if result.mode != "error":
                    meeting.reminder_sent_at = now
                    session.add(meeting)
                    session.commit()
                    sent += 1
                print(
                    f"[auto-email] reminder for meeting {meeting.id} "
                    f"({meeting.prospect_company}): {result.mode}",
                    flush=True,
                )
            except Exception as exc:  # noqa: BLE001
                print(f"[auto-email] reminder failed for meeting {meeting.id}: {exc}", flush=True)
    return sent


def reminder_loop() -> None:
    """Long-lived daemon: wake every reminder_poll_seconds and send any due reminders.
    Fully fail-soft — a transient error just retries on the next tick."""
    poll = max(5, settings.reminder_poll_seconds)
    print(
        f"[auto-email] reminder scheduler started "
        f"(lead={settings.reminder_lead_minutes}m, poll={poll}s)",
        flush=True,
    )
    while True:
        try:
            send_due_reminders()
        except Exception as exc:  # noqa: BLE001 — the loop must never die
            print(f"[auto-email] reminder loop error: {exc}", flush=True)
        time.sleep(poll)
