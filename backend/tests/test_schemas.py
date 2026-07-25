"""Persona section-set contract (six personas from the persona doc)."""
from app.schemas import DEFAULT_PERSONA, PERSONA_LABELS, PERSONA_SECTIONS, SECTION_ORDER, sections_for

_EXPECTED = {"sales_rep", "sales_manager", "enablement", "revops", "vp_sales", "admin"}


def test_all_personas_present():
    assert set(PERSONA_SECTIONS) == _EXPECTED
    assert set(PERSONA_LABELS) == _EXPECTED
    assert DEFAULT_PERSONA == "sales_rep"


def test_sales_rep_is_nine_sections_in_order():
    ids = [sid for sid, _ in sections_for("sales_rep")]
    assert ids == SECTION_ORDER
    assert len(ids) == 9


def test_sales_manager_sections():
    ids = [sid for sid, _ in sections_for("sales_manager")]
    assert ids == [
        "deal_snapshot", "coaching_focus", "deal_risks",
        "key_stakeholders", "rep_questions", "next_steps",
    ]


def test_admin_is_provenance_view():
    ids = [sid for sid, _ in sections_for("admin")]
    assert ids == [
        "source_inventory", "data_lineage", "coverage_gaps",
        "data_freshness", "integration_status", "quality_flags",
    ]


def test_each_persona_has_sections():
    for p in _EXPECTED:
        assert len(sections_for(p)) >= 6 if p != "sales_rep" else True
        assert all(sid and title for sid, title in sections_for(p))


def test_unknown_persona_falls_back_to_default():
    assert sections_for("bogus") == sections_for("sales_rep")
