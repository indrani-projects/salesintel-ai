"""Web-first prospect intel (MOCK_WEB: deterministic, no network)."""
from app.services import company_hints, sources, web_sources


def _tags(docs):
    return [d.tags[0] for d in docs if d.tags]


def test_mock_web_returns_docs():
    docs = web_sources.fetch_intel("Freshworks")
    assert docs
    assert any("Freshworks" in d.text for d in docs)


def test_load_company_intel_is_web_first_plus_zoho():
    # An unknown company with NO docs folder still gets web intel + shared zoho docs.
    s = sources.load_company_intel("Freshworks", None)
    assert "web" in _tags(s)          # web sources present
    assert "zoho" in _tags(s)         # zoho product knowledge always appended
    # markers are unique + sequential across web + zoho
    markers = [d.marker for d in s]
    assert markers == [f"S{i}" for i in range(1, len(s) + 1)]


def test_load_company_intel_falls_back_to_docs(monkeypatch):
    # When the web returns nothing, use the local docs/<slug>/ folder.
    monkeypatch.setattr(web_sources, "fetch_intel", lambda name, force=False: [])
    s = sources.load_company_intel("The Sleep Company", "sleep_company")
    assert "prospect" in _tags(s)     # local prospect docs used
    assert any(d.filename for d in s if d.tags and d.tags[0] == "prospect")
    assert "zoho" in _tags(s)


def test_company_hints_lenient_lookup():
    assert company_hints.hint_for("Freshworks")["ticker"] == "FRSH"
    assert company_hints.hint_for("Sprout Social Inc.")["ticker"] == "SPT"
    assert company_hints.hint_for("Totally Unknown Co") is None
