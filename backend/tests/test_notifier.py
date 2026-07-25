"""Automated brief emails (notifier) — MOCK env, no network, no quota.

Auto-email is OFF in tests (AUTO_EMAIL_ENABLED=0), so nothing fires on its own;
these call the notifier functions directly. DEFAULT_RECIPIENT is set in conftest.
Times are relative to datetime.utcnow() so the assertions never depend on the
wall clock (start_time is stored naive-UTC).
"""
from datetime import datetime, timedelta

from sqlmodel import Session

from app import models
from app.db import engine
from app.services import notifier

_BASE = {
    "subject": "Discovery call with The Sleep Company",
    "prospect_company": "The Sleep Company",
    "why": "Scale retail",
    "agenda": "Omnichannel",
    "persona": "sales_rep",
}


def _make_ready_meeting(client, start_time: datetime) -> int:
    """Create a meeting whose primary brief is ready (MOCK_LLM generates it
    synchronously via BackgroundTasks), pin its start_time, and clear the guards."""
    body = dict(_BASE, start_time=start_time.isoformat())
    r = client.post("/meetings", json=body)
    assert r.status_code == 200, r.text
    mid = r.json()["id"]
    assert client.get(f"/meetings/{mid}/brief").json()["status"] == "ready"
    with Session(engine) as s:
        m = s.get(models.Meeting, mid)
        m.start_time = start_time
        m.ready_email_sent_at = None
        m.reminder_sent_at = None
        m.day_before_sent_at = None
        s.add(m)
        s.commit()
    return mid


def _meeting(mid: int) -> models.Meeting:
    with Session(engine) as s:
        return s.get(models.Meeting, mid)


def test_send_ready_email_stamps_and_is_idempotent(client):
    mid = _make_ready_meeting(client, datetime.utcnow() + timedelta(days=2))
    notifier.send_ready_email(mid)
    first = _meeting(mid).ready_email_sent_at
    assert first is not None
    # Second call is a no-op — the guard is already set.
    notifier.send_ready_email(mid)
    assert _meeting(mid).ready_email_sent_at == first


def test_send_ready_email_skips_past_meeting(client):
    mid = _make_ready_meeting(client, datetime.utcnow() - timedelta(hours=1))
    notifier.send_ready_email(mid)
    assert _meeting(mid).ready_email_sent_at is None


def test_ready_within_window_also_stamps_reminder(client):
    # Meeting is <60 min away → the ready-send doubles as the reminder.
    mid = _make_ready_meeting(client, datetime.utcnow() + timedelta(minutes=30))
    notifier.send_ready_email(mid)
    m = _meeting(mid)
    assert m.ready_email_sent_at is not None
    assert m.reminder_sent_at is not None


def test_send_ready_email_noops_without_recipient(client, monkeypatch):
    from app.config import settings

    monkeypatch.setattr(settings, "default_recipient", "")
    mid = _make_ready_meeting(client, datetime.utcnow() + timedelta(days=2))
    notifier.send_ready_email(mid)
    assert _meeting(mid).ready_email_sent_at is None


def test_send_due_reminders_sends_within_window(client):
    mid = _make_ready_meeting(client, datetime.utcnow() + timedelta(minutes=45))
    sent = notifier.send_due_reminders()
    assert sent >= 1
    assert _meeting(mid).reminder_sent_at is not None


def test_send_due_reminders_skips_outside_window_and_already_sent(client):
    far = _make_ready_meeting(client, datetime.utcnow() + timedelta(days=2))
    done = _make_ready_meeting(client, datetime.utcnow() + timedelta(minutes=20))
    with Session(engine) as s:
        m = s.get(models.Meeting, done)
        m.reminder_sent_at = datetime.utcnow() - timedelta(minutes=5)
        s.add(m)
        s.commit()
    already = _meeting(done).reminder_sent_at

    notifier.send_due_reminders()

    assert _meeting(far).reminder_sent_at is None          # outside the 1h window
    assert _meeting(done).reminder_sent_at == already      # not re-sent


def test_gmail_transport_when_connected(client, monkeypatch):
    from app.config import settings

    # mock_email off + mock_google on → the Gmail send path (mode "gmail").
    monkeypatch.setattr(settings, "mock_email", False)
    assert notifier._transport() == "gmail"
    mid = _make_ready_meeting(client, datetime.utcnow() + timedelta(days=1))
    notifier.send_ready_email(mid)
    assert _meeting(mid).ready_email_sent_at is not None


def test_automation_endpoint_shape(client):
    j = client.get("/integrations/email/automation").json()
    assert set(j) == {
        "enabled", "lead_minutes", "recipient", "transport",
        "day_before_enabled", "day_before_minutes", "personalized",
    }
    assert j["enabled"] is False           # AUTO_EMAIL_ENABLED=0 in tests
    assert j["lead_minutes"] == 60
    assert j["recipient"] == "rep@salesintel.test"
    assert j["transport"] in {"gmail", "smtp", "demo"}
    assert j["day_before_minutes"] == 1440
    assert j["personalized"] is False      # no PERSONA_EMAILS in tests


def test_day_before_sends_within_window_and_is_idempotent(client):
    # ~12h out → inside the 24h day-before window.
    mid = _make_ready_meeting(client, datetime.utcnow() + timedelta(hours=12))
    sent = notifier.send_due_day_before()
    assert sent >= 1
    first = _meeting(mid).day_before_sent_at
    assert first is not None
    # Second pass is a no-op — the guard is set.
    notifier.send_due_day_before()
    assert _meeting(mid).day_before_sent_at == first


def test_day_before_skips_outside_window(client):
    mid = _make_ready_meeting(client, datetime.utcnow() + timedelta(days=3))  # >24h
    notifier.send_due_day_before()
    assert _meeting(mid).day_before_sent_at is None


def test_ready_within_day_before_window_also_stamps_day_before(client):
    # A meeting created <24h out: the on-ready send doubles as the day-before send.
    mid = _make_ready_meeting(client, datetime.utcnow() + timedelta(hours=6))
    notifier.send_ready_email(mid)
    assert _meeting(mid).day_before_sent_at is not None


def test_persona_email_routing_falls_back_to_default(monkeypatch):
    from app.config import settings

    monkeypatch.setattr(settings, "persona_emails", {"sales_rep": "rohan@acme.com"})
    assert settings.recipient_for_persona("sales_rep") == "rohan@acme.com"
    # A persona without its own entry uses DEFAULT_RECIPIENT.
    assert settings.recipient_for_persona("vp_sales") == settings.default_recipient


def test_day_before_routes_to_persona_email(client, monkeypatch):
    from app.config import settings
    from app.services import email_service

    monkeypatch.setattr(settings, "persona_emails", {"sales_rep": "rohan@acme.com"})
    captured: list[str] = []
    orig = email_service.send_brief_email

    def _spy(composed, recipient):
        captured.append(recipient)
        return orig(composed, recipient)

    monkeypatch.setattr(email_service, "send_brief_email", _spy)
    _make_ready_meeting(client, datetime.utcnow() + timedelta(hours=12))
    notifier.send_due_day_before()
    # The sales_rep meeting routed to its persona address (other due meetings, if any,
    # go to the default — we only assert our persona routing landed).
    assert "rohan@acme.com" in captured
