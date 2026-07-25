"""Google integration API (MOCK_GOOGLE: deterministic, no network)."""

NEW_MEETING = {
    "subject": "Discovery call with The Sleep Company",
    "prospect_company": "The Sleep Company",
    "why": "Scale retail + B2B",
    "agenda": "Omnichannel data + support",
    "start_time": "2026-07-20T10:30:00",
    "persona": "sales_rep",
}


def _sync(client):
    r = client.post("/integrations/google/calendar/sync")
    assert r.status_code == 200, r.text
    return r.json()


def test_google_status_connected_in_mock(client):
    r = client.get("/integrations/google/status")
    assert r.status_code == 200
    j = r.json()
    assert j["configured"] is True
    assert j["connected"] is True
    assert j["email"] == "mock@calendar.test"
    assert "https://www.googleapis.com/auth/calendar.events" in j["scopes"]


def test_calendar_sync_imports_prospect_and_dedupes(client):
    first = _sync(client)
    # two canned events (Sleep Company + Team standup); only the prospect imports
    assert first["scanned"] == 2
    assert first["imported"] == 1
    assert first["skipped_existing"] == 0

    meetings = client.get("/meetings").json()
    imported = [m for m in meetings if m.get("google_event_id") == "mock-evt-sleep"]
    assert len(imported) == 1
    m = imported[0]
    assert m["company_slug"] == "sleep_company"
    assert "Sleep Company" in m["subject"]
    assert m["google_html_link"]

    # its brief was generated synchronously during sync
    brief = client.get(f"/meetings/{m['id']}/brief").json()
    assert brief["status"] == "ready"

    # re-syncing the same events is idempotent (deduped by google_event_id)
    second = _sync(client)
    assert second["imported"] == 0
    assert second["skipped_existing"] == 1


def test_create_meeting_pushes_to_google_when_connected(client):
    r = client.post("/meetings", json=NEW_MEETING)
    assert r.status_code == 200, r.text
    m = r.json()
    # mock Google is "connected", so the meeting mirrors to the calendar
    assert m["google_event_id"] == "mock-created-event"
    assert m["google_html_link"]


def test_disconnect_is_204(client):
    # mock mode has no stored token, but the endpoint should still succeed
    r = client.delete("/integrations/google/disconnect")
    assert r.status_code == 204


def test_prospect_matching_is_lenient_on_the_prefix():
    # Real Google titles often drop the leading "The" — must still resolve.
    from app.api.google import _match_prospect

    slug, name = _match_prospect({"summary": "Discovery call with Sleep Company"})
    assert slug == "sleep_company"
    assert name == "The Sleep Company"

    # A non-prospect event resolves to nothing.
    none_slug, _ = _match_prospect({"summary": "Team standup", "attendees": []})
    assert none_slug is None


def test_web_only_enrichment_company_imports_without_docs_folder():
    # Freshworks has no docs/ folder — it is a web-first (enrichment) company.
    # Its calendar event must still be recognized as a prospect, regardless of
    # the title phrasing, with slug=None so the web-first intel path builds it.
    from app.api.google import _match_prospect

    for summary in (
        "Freshworks",
        "Discovery call with Freshworks",
        "Meeting with Freshworks team",
        "Braze QBR",
    ):
        slug, name = _match_prospect({"summary": summary})
        assert slug is None, summary
        assert name in ("Freshworks", "Braze"), summary


def test_generic_unknown_company_imports_from_meeting_title():
    # A company with neither a docs folder nor an enrichment hint still imports
    # when the title reads like a sales meeting.
    from app.api.google import _match_prospect

    slug, name = _match_prospect({"summary": "Sales sync with Acme Robotics"})
    assert slug is None
    assert name == "Acme Robotics"


def test_editing_an_event_in_google_updates_the_meeting_on_resync(client, monkeypatch):
    # First sync imports the canned Sleep Company event.
    _sync(client)
    meetings = client.get("/meetings").json()
    m = next(x for x in meetings if x.get("google_event_id") == "mock-evt-sleep")
    assert m["prospect_company"] == "The Sleep Company"

    # The rep edits that same event in Google — different company (Braze), new time.
    from app.services import google_service

    edited = [
        {
            "id": "mock-evt-sleep",
            "summary": "Discovery call with Braze",
            "start": "2026-08-05T09:00:00+00:00",
            "html_link": "https://calendar.google.com/mock/braze",
            "description": "Rescheduled",
            "attendees": [],
        }
    ]
    monkeypatch.setattr(google_service, "list_events", lambda *a, **k: edited)

    res = _sync(client)
    assert res["imported"] == 0        # not a new event
    assert "updated 1" in res["message"]

    # The meeting reflects the edit and its brief was rebuilt for the new company.
    updated = client.get(f"/meetings/{m['id']}").json()
    assert updated["prospect_company"] == "Braze"
    assert updated["company_slug"] is None          # Braze is web-first (no docs folder)
    assert "Braze" in updated["subject"]
    brief = client.get(f"/meetings/{m['id']}/brief").json()
    assert brief["status"] == "ready"


def test_personal_events_are_not_imported():
    # The generic path must not import personal calendar events.
    from app.api.google import _match_prospect

    for summary in ("Lunch with Mom", "Dentist", "Gym", "Pick up kids"):
        slug, name = _match_prospect({"summary": summary})
        assert (slug, name) == (None, None), summary
