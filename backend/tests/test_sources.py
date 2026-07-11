"""Company discovery + source loading against the real docs/ folder."""
from app.services import sources


def test_resolve_company_slug_variants():
    assert sources.resolve_company_slug("The Sleep Company") == "sleep_company"
    assert sources.resolve_company_slug("sleep_company") == "sleep_company"
    assert sources.resolve_company_slug("SLEEP company") == "sleep_company"


def test_resolve_unknown_returns_none():
    assert sources.resolve_company_slug("Definitely Not A Prospect") is None


def test_zoho_is_not_a_prospect_company():
    # zoho is our internal knowledge, never a prospect target.
    assert sources.resolve_company_slug("zoho") is None
    names = {c.slug for c in sources.list_companies()}
    assert "zoho" not in names


def test_list_companies_includes_sleep_company():
    companies = {c.slug: c for c in sources.list_companies()}
    assert "sleep_company" in companies
    assert companies["sleep_company"].name == "The Sleep Company"
    assert companies["sleep_company"].doc_count >= 1


def test_load_company_sources_has_prospect_and_zoho():
    docs = sources.load_company_sources("sleep_company")
    assert len(docs) >= 2
    tags = {t for d in docs for t in d.tags}
    assert "prospect" in tags and "zoho" in tags
    # markers are sequential and text is non-empty
    assert docs[0].marker == "S1"
    assert all(d.text.strip() for d in docs)
