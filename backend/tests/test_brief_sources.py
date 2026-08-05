"""Source display: web/prepared sources surface their URL, not the internal cache
`.md` filename; local docs keep their real filename (e.g. a PDF)."""
from app.contracts import SourceDoc
from app.services.brief_engine import _display_filename, _is_web_source, _sources_from_docs


def test_prepared_web_source_hides_md_and_keeps_url():
    doc = SourceDoc(
        marker="S1",
        title="TechCrunch — Sprout Social",
        filename="03-techcrunch-com.md",           # internal cache artifact
        url="https://techcrunch.com/2024/sprout",
        tags=["web", "prospect", "prepared"],
    )
    assert _is_web_source(doc) is True
    assert _display_filename(doc) is None
    [bs] = _sources_from_docs([doc])
    assert bs.url == "https://techcrunch.com/2024/sprout"
    assert bs.filename is None                       # no .md shown


def test_web_source_by_url_only_hides_filename():
    # A live-feed doc: tagged ["web"] with a URL — still a web source.
    doc = SourceDoc(marker="S2", title="News", filename=None,
                    url="https://news.example.com/x", tags=["web", "prospect"])
    assert _display_filename(doc) is None
    [bs] = _sources_from_docs([doc])
    assert bs.url == "https://news.example.com/x"


def test_local_pdf_keeps_filename_no_url():
    doc = SourceDoc(marker="S3", title="Annual report", filename="report.pdf",
                    url=None, tags=["prospect"])
    assert _is_web_source(doc) is False
    assert _display_filename(doc) == "report.pdf"
    [bs] = _sources_from_docs([doc])
    assert bs.filename == "report.pdf"
    assert bs.url is None


def test_local_md_knowledge_file_is_hidden():
    # The Zoho knowledge sheet (docs/zoho/zoho_capabilities.md) — a bare .md is an
    # internal/dev artifact, not a user-facing reference.
    doc = SourceDoc(marker="S4", title="zoho capabilities",
                    filename="zoho_capabilities.md", url=None, tags=["zoho"])
    assert _display_filename(doc) is None
    [bs] = _sources_from_docs([doc])
    assert bs.filename is None
