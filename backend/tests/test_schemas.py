"""Persona section-set contract."""
from app.schemas import PERSONA_SECTIONS, SECTION_ORDER, sections_for


def test_all_personas_present():
    assert set(PERSONA_SECTIONS) == {"ae", "sdr", "se"}


def test_ae_is_nine_sections_in_order():
    ids = [sid for sid, _ in sections_for("ae")]
    assert ids == SECTION_ORDER
    assert len(ids) == 9


def test_sdr_sections():
    ids = [sid for sid, _ in sections_for("sdr")]
    assert ids == ["hook", "target_contact", "value_hypothesis", "outreach_opener", "qualifying_questions"]


def test_se_sections():
    ids = [sid for sid, _ in sections_for("se")]
    assert ids == ["tech_stack", "integration_landscape", "technical_fit", "demo_focus", "technical_objections", "open_questions"]


def test_unknown_persona_falls_back_to_ae():
    assert sections_for("bogus") == sections_for("ae")
