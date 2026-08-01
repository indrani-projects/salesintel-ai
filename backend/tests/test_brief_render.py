"""D2 — direct coverage for the hand-rolled markdown->HTML renderer and render_html.

The block/inline converter (brief_render._md_to_html) is regex-based, so these pin
its edge cases: escaping, bold/italic/code, links, [S#] citations, and lists.
"""
from app.schemas import BriefContent, BriefSection, BriefSource, Confidence, Persona
from app.services.brief_render import _md_to_html, render_html


def test_md_escapes_html_before_formatting():
    h = _md_to_html("<script>alert(1)</script>")
    assert "<script>" not in h
    assert "&lt;script&gt;alert(1)&lt;/script&gt;" in h


def test_md_bold_italic_code():
    h = _md_to_html("**bold** then *italic* then `code`")
    assert "<strong>bold</strong>" in h
    assert "<em>italic</em>" in h
    assert "<code>code</code>" in h


def test_md_links_and_citation_chips():
    h = _md_to_html("See [docs](https://example.com) and [S1].")
    assert '<a href="https://example.com">docs</a>' in h
    assert '<span class="cite">S1</span>' in h


def test_md_unordered_and_ordered_lists():
    h = _md_to_html("- alpha\n- beta\n\n1. one\n2. two")
    assert "<ul>" in h and "<li>alpha</li>" in h and "<li>beta</li>" in h
    assert "<ol>" in h and "<li>one</li>" in h and "<li>two</li>" in h


def test_md_headings_shift_below_section_h2():
    # A markdown "# x" shifts to <h3> so a section's own <h2> stays the top level.
    assert "<h3>" in _md_to_html("# Heading")


def test_md_empty_is_empty():
    assert _md_to_html("") == ""


def _brief(company: str) -> BriefContent:
    return BriefContent(
        company=company,
        company_slug="acme",
        persona=Persona.sales_rep,
        headline="A headline",
        sections=[
            BriefSection(id="company_snapshot", title="Snapshot", content_md="**fact** [S1]"),
            BriefSection(
                id="risks", title="Risks", content_md="risky", confidence=Confidence.low
            ),
        ],
        sources=[BriefSource(marker="S1", title="Annual report", filename="report.pdf")],
    )


def test_render_html_includes_company_sections_and_sources():
    html = render_html(_brief("The Sleep Company"))
    assert "The Sleep Company" in html
    assert "Snapshot" in html and "Risks" in html
    assert "report.pdf" in html
    assert "Verify before use" in html  # low-confidence section badge


def test_render_html_escapes_company_name():
    html = render_html(_brief("<img src=x onerror=alert(1)>"))
    assert "<img src=x onerror" not in html
    assert "&lt;img src=x onerror=alert(1)&gt;" in html
