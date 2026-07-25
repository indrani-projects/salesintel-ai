"""Deterministic web-to-doc preparation stage (offline, NO LLM, NO network).

Every test here runs without the network: `retrieval.search`/`fetch_and_extract` are
monkeypatched, `web_sources.fetch_intel` is canned via MOCK_WEB (conftest), and the
prepared cache is redirected to a tmp dir. The final test enforces "no LLM by
construction" — the prep modules must not import the LLM client at all.
"""
import inspect
import json

import pytest

from app.services import (
    credibility,
    prep,
    research_keywords as rk,
    retrieval,
    sources,
)
from app.services.retrieval import ExtractedPage

_ARTICLE_HTML = """
<html><head><title>Freshworks reports strong quarter</title></head>
<body>
  <nav>Home · Products · Login</nav>
  <article>
    <h1>Freshworks reports strong quarter and a new CFO</h1>
    <p>Freshworks announced quarterly earnings today with revenue growth of 20 percent
    year over year, and reaffirmed guidance for the full year.</p>
    <p>The company also named a new CFO, its second executive hire this quarter, as it
    plans an expansion into new markets.</p>
    <p>Some customers on Reddit raised a pricing complaint and said they switched from
    Freshworks to a cheaper alternative after comparing it against Salesforce.</p>
  </article>
  <footer>Copyright 2026</footer>
</body></html>
"""


# --------------------------------------------------------------------------- #
# research_keywords
# --------------------------------------------------------------------------- #
def test_match_categories_tags_and_drops():
    assert "financial_intel" in rk.match_categories("Q3 quarterly earnings, revenue growth")
    assert "leadership_changes" in rk.match_categories("appointed a new CFO this week")
    assert "pain_points" in rk.match_categories(
        "users switched from Freshworks to an alternative", "Freshworks", ["Zoho"]
    )
    assert rk.match_categories("the weather is pleasant today") == []


def test_search_queries_include_company_and_signals():
    qs = rk.search_queries("Freshworks", ["Salesforce"])
    assert "Freshworks" in qs
    assert any("earnings" in q for q in qs)
    assert any("Salesforce" in q for q in qs)  # competitor-vs query


# --------------------------------------------------------------------------- #
# credibility
# --------------------------------------------------------------------------- #
def test_credibility_tiers():
    assert credibility.score("https://efts.sec.gov/x", "Freshworks") == (95, "regulatory")
    assert credibility.score("https://en.wikipedia.org/wiki/Freshworks", "Freshworks")[1] == "encyclopedia"
    assert credibility.score("https://www.freshworks.com/about", "Freshworks")[1] == "official"
    assert credibility.score("https://www.reuters.com/x", "Freshworks")[1] == "tier1_press"
    assert credibility.score("https://www.reddit.com/r/sales", "Freshworks") == (35, "social")
    assert credibility.score("https://some-random-site.io/post", "Freshworks")[1] == "web"
    assert credibility.is_authoritative("encyclopedia")
    assert not credibility.is_authoritative("social")


# --------------------------------------------------------------------------- #
# retrieval.extract_page (pure — no network)
# --------------------------------------------------------------------------- #
def test_extract_page_strips_boilerplate():
    page = retrieval.extract_page(_ARTICLE_HTML, "https://www.reuters.com/tech/freshworks")
    assert page is not None
    assert page.domain == "reuters.com"
    assert "revenue growth" in page.markdown.lower()
    assert "login" not in page.markdown.lower()  # nav boilerplate removed


# --------------------------------------------------------------------------- #
# prep.prepare_company (offline: patched retrieval + canned feeds + tmp cache)
# --------------------------------------------------------------------------- #
@pytest.fixture
def _offline_prep(monkeypatch, tmp_path):
    monkeypatch.setattr(prep, "PREPARED_ROOT", tmp_path)
    page = ExtractedPage(
        url="https://www.reuters.com/tech/freshworks",
        domain="reuters.com",
        title="Freshworks reports strong quarter",
        markdown=(
            "Freshworks reported quarterly earnings with revenue growth of 20 percent.\n\n"
            "The company named a new CFO and announced an expansion.\n\n"
            "Customers raised a pricing complaint and switched to an alternative."
        ),
    )
    monkeypatch.setattr(retrieval, "search", lambda company, competitors=None: [page.url])
    monkeypatch.setattr(retrieval, "fetch_and_extract", lambda url: page)
    return tmp_path


def test_prepare_company_writes_manifest_and_docs(_offline_prep):
    manifest = prep.prepare_company("Freshworks", force=True)
    assert manifest["slug"] == "freshworks"
    assert manifest["docs"], "expected at least one prepared doc"

    cdir = _offline_prep / "freshworks"
    assert (cdir / "manifest.json").exists()
    md_files = list(cdir.glob("*.md"))
    assert md_files, "expected prepared .md files on disk"

    # The Reuters doc is present, credibility-tiered and category-tagged.
    reuters = next(d for d in manifest["docs"] if d["domain"] == "reuters.com")
    assert reuters["credibility"] == 80
    assert reuters["source_type"] == "tier1_press"
    assert "financial_intel" in reuters["categories"]
    body = (cdir / reuters["file"]).read_text(encoding="utf-8")
    assert "## financial_intel" in body
    assert "revenue growth" in body.lower()


def test_prepare_company_is_idempotent(_offline_prep, monkeypatch):
    prep.prepare_company("Freshworks", force=True)  # seed a fresh manifest

    def _boom(*a, **k):
        raise AssertionError("prep re-fetched despite a fresh cache")

    monkeypatch.setattr(retrieval, "search", _boom)
    monkeypatch.setattr(retrieval, "fetch_and_extract", _boom)
    manifest = prep.prepare_company("Freshworks")  # no force → must short-circuit
    assert manifest["docs"]


# --------------------------------------------------------------------------- #
# sources integration
# --------------------------------------------------------------------------- #
def test_load_prepared_docs_and_intel_prefers_prepared(_offline_prep):
    prep.prepare_company("Freshworks", force=True)

    docs, idx = sources.load_prepared_docs("Freshworks", None, 1)
    assert docs, "prepared docs should load from the manifest"
    assert all(d.tags == ["web", "prospect", "prepared"] for d in docs)
    assert docs[0].marker == "S1"

    intel = sources.load_company_intel("Freshworks", None)
    tags = [t for d in intel for t in d.tags]
    assert "prepared" in tags          # prepared docs preferred over live feeds
    assert "zoho" in tags              # shared Zoho knowledge still appended
    markers = [d.marker for d in intel]
    assert markers == [f"S{i}" for i in range(1, len(intel) + 1)]  # sequential


# --------------------------------------------------------------------------- #
# "No LLM by construction"
# --------------------------------------------------------------------------- #
def test_prep_stage_has_no_llm_dependency():
    for module in (prep, retrieval, credibility, rk):
        src = inspect.getsource(module).lower()
        assert "llm_client" not in src
        assert "openai" not in src
