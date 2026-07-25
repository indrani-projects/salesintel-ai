"""Unit tests for the email composer/sender (demo-send, no real SMTP)."""
from app.schemas import (
    PERSONA_SECTIONS,
    BriefContent,
    BriefSection,
    BriefSource,
    KeyFact,
    Persona,
)
from app.services import email_service


def _brief(persona: str) -> BriefContent:
    sections = [
        BriefSection(id=sid, title=title, content_md=f"Body for {sid} [S1]")
        for sid, title in PERSONA_SECTIONS[persona]
    ]
    return BriefContent(
        company="The Sleep Company",
        company_slug="sleep_company",
        persona=Persona(persona),
        headline="Fast-scaling D2C sleep brand.",
        key_facts=[KeyFact(label="ARR", value="₹700 Cr")],
        sections=sections,
        sources=[BriefSource(marker="S1", title="Funding news")],
    )


def test_compose_sales_rep_highlights_angle_and_stakeholders():
    composed = email_service.compose_brief_email(_brief("sales_rep"))
    assert "Sales Representative" in composed.subject
    assert "The Sleep Company" in composed.subject
    assert composed.attachment_filename.endswith("-sales_rep-brief.html")
    # Sales Rep digest features the recommended angle + stakeholders sections.
    # (Titles are HTML-escaped, so match on apostrophe-free substrings.)
    assert "Recommended Angle" in composed.body_html
    assert "Key Stakeholders" in composed.body_html
    assert composed.attachment_bytes  # full brief HTML attached


def test_compose_persona_specific_sections():
    mgr = email_service.compose_brief_email(_brief("sales_manager"))
    assert "Coaching Focus" in mgr.body_html
    assert mgr.attachment_filename.endswith("-sales_manager-brief.html")

    vp = email_service.compose_brief_email(_brief("vp_sales"))
    assert "Executive Recommendation" in vp.body_html
    assert vp.attachment_filename.endswith("-vp_sales-brief.html")


def test_send_is_demo_when_not_configured():
    composed = email_service.compose_brief_email(_brief("sales_rep"))
    result = email_service.send_brief_email(composed, "rep@zoho.com")
    assert result.delivered is False
    assert result.mode == "demo"
    assert result.recipient == "rep@zoho.com"


def test_send_rejects_empty_recipient():
    composed = email_service.compose_brief_email(_brief("sales_rep"))
    result = email_service.send_brief_email(composed, "   ")
    assert result.delivered is False
    assert result.mode == "error"


def test_send_prefers_gmail_when_google_connected(monkeypatch):
    # With a connected Google account (mock) and email delivery enabled, the send
    # should route through Gmail (mode="gmail"), not SMTP/demo.
    from app.config import settings as s

    monkeypatch.setattr(s, "mock_email", False)   # allow real delivery path
    monkeypatch.setattr(s, "mock_google", True)   # "connected" + Gmail is a no-op
    composed = email_service.compose_brief_email(_brief("sales_manager"))
    result = email_service.send_brief_email(composed, "rep@zoho.com")
    assert result.mode == "gmail"
    assert result.recipient == "rep@zoho.com"
