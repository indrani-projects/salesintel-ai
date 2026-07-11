"""PDF text extraction + cache."""
from app.config import settings
from app.services.ingestion import extract_text


def _a_sleep_pdf():
    folder = settings.docs_root_path / "sleep_company"
    pdfs = sorted(folder.glob("*.pdf"))
    assert pdfs, "expected Sleep Company PDFs in docs/sleep_company/"
    return pdfs[0]


def test_extract_text_nonempty():
    text = extract_text(_a_sleep_pdf())
    assert isinstance(text, str)
    assert len(text) > 200
    assert "sleep" in text.lower()


def test_extract_text_cached_is_stable():
    p = _a_sleep_pdf()
    assert extract_text(p) == extract_text(p)


def test_missing_file_returns_empty():
    assert extract_text(settings.docs_root_path / "does_not_exist.pdf") == ""
