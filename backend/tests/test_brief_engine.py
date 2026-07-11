"""Brief synthesis in MOCK_LLM mode + HTML render."""
from app.schemas import sections_for
from app.services.brief_engine import generate_brief
from app.services.brief_render import render_html


def test_ae_brief_has_nine_sections_and_key_facts():
    b = generate_brief("sleep_company", "Discovery", "why", "agenda", "ae")
    assert b.persona.value == "ae"
    assert [s.id for s in b.sections] == [sid for sid, _ in sections_for("ae")]
    assert len(b.sections) == 9
    assert b.key_facts and b.key_facts[0].label
    assert b.company == "The Sleep Company"


def test_sdr_and_se_section_sets():
    sdr = generate_brief("sleep_company", "s", "w", "a", "sdr")
    se = generate_brief("sleep_company", "s", "w", "a", "se")
    assert [s.id for s in sdr.sections] == [sid for sid, _ in sections_for("sdr")]
    assert [s.id for s in se.sections] == [sid for sid, _ in sections_for("se")]


def test_render_html_contains_company_and_persona():
    b = generate_brief("sleep_company", "s", "w", "a", "se")
    html = render_html(b)
    assert "<html" in html.lower()
    assert "The Sleep Company" in html
    assert "Solutions Engineer" in html
