"""Brief synthesis in MOCK_LLM mode + HTML render (six personas)."""
from app.schemas import Persona, sections_for
from app.services.brief_engine import generate_brief
from app.services.brief_render import render_html


def test_sales_rep_brief_has_nine_sections_and_key_facts():
    b = generate_brief("sleep_company", "Discovery", "why", "agenda", "sales_rep")
    assert b.persona.value == "sales_rep"
    assert [s.id for s in b.sections] == [sid for sid, _ in sections_for("sales_rep")]
    assert len(b.sections) == 9
    assert b.key_facts and b.key_facts[0].label
    assert b.company == "The Sleep Company"


def test_every_persona_section_set():
    for p in Persona:
        b = generate_brief("sleep_company", "s", "w", "a", p.value)
        assert b.persona.value == p.value
        assert [s.id for s in b.sections] == [sid for sid, _ in sections_for(p.value)]


def test_render_html_contains_company_and_persona_label():
    b = generate_brief("sleep_company", "s", "w", "a", "vp_sales")
    html = render_html(b)
    assert "<html" in html.lower()
    assert "The Sleep Company" in html
    assert "VP of Sales" in html
