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


def test_compose_ae_highlights_angle_and_stakeholders():
    composed = email_service.compose_brief_email(_brief("ae"))
    assert "Account Executive" in composed.subject
    assert "The Sleep Company" in composed.subject
    assert composed.attachment_filename.endswith("-ae-brief.html")
    # AE digest features the recommended angle + stakeholders sections.
    # (Titles are HTML-escaped, so match on apostrophe-free substrings.)
    assert "Recommended Angle" in composed.body_html
    assert "Key Stakeholders" in composed.body_html
    assert composed.attachment_bytes  # full brief HTML attached


def test_compose_persona_specific_sections():
    sdr = email_service.compose_brief_email(_brief("sdr"))
    assert "Ready-to-Send Opener" in sdr.body_html
    assert sdr.attachment_filename.endswith("-sdr-brief.html")

    se = email_service.compose_brief_email(_brief("se"))
    assert "Demo Focus" in se.body_html
    assert se.attachment_filename.endswith("-se-brief.html")


def test_send_is_demo_when_not_configured():
    composed = email_service.compose_brief_email(_brief("ae"))
    result = email_service.send_brief_email(composed, "rep@zoho.com")
    assert result.delivered is False
    assert result.mode == "demo"
    assert result.recipient == "rep@zoho.com"


def test_send_rejects_empty_recipient():
    composed = email_service.compose_brief_email(_brief("ae"))
    result = email_service.send_brief_email(composed, "   ")
    assert result.delivered is False
    assert result.mode == "error"
