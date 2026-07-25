"""CLI: build the Zoho product catalog from zoho.com — deterministic, NO LLM.

Run from backend/ with the checked-in venv:

    .\\.venv\\Scripts\\python.exe -m app.tools.build_zoho_catalog

For every source in `app/services/zoho_catalog.py` it fetches the page (keyless,
trafilatura), writes the full clean content to docs/zoho/products/<slug>.md, and
assembles the compact docs/zoho/zoho_products_summary.md (one short entry per product:
what it does + key points + source). The summary auto-loads into every brief; the full
per-product docs sit in products/ for reference and are not auto-injected.
"""
from __future__ import annotations

import sys
from typing import List, Tuple

from app.config import settings
from app.services import condense, retrieval
from app.services.zoho_catalog import ZOHO_SOURCES, slug_for

_ZOHO_DIR = settings.docs_root_path / "zoho"
_PRODUCTS_DIR = _ZOHO_DIR / "products"

_SUMMARY_HEADER = (
    "# Zoho Product Catalog (summary)\n\n"
    "_Deterministically prepared from zoho.com — NO LLM. One compact entry per product: "
    "what it does + key capabilities, for matching Zoho products to a prospect's pain "
    "points. Full extracted content per product is in `products/`. Curate by editing "
    "`app/services/zoho_catalog.py` and re-running `python -m app.tools.build_zoho_catalog`._\n"
)


def build() -> Tuple[int, List[str]]:
    _PRODUCTS_DIR.mkdir(parents=True, exist_ok=True)
    sections: List[str] = [_SUMMARY_HEADER]
    written = 0
    missing: List[str] = []

    for src in ZOHO_SOURCES:
        product, url, kind = src["product"], src["url"], src.get("kind", "overview")
        page = retrieval.fetch_and_extract(url)
        if not page or not page.markdown.strip():
            missing.append(product)
            continue

        slug = slug_for(product)
        (_PRODUCTS_DIR / f"{slug}.md").write_text(
            f"# {product}\n\n_Source: {url} ({kind})_\n\n{page.markdown.strip()}\n",
            encoding="utf-8",
        )
        written += 1

        lead = condense.lead_paragraph(page.markdown)
        points = condense.key_points(page.markdown)
        block = [f"## {product}"]
        if kind == "integration":
            block.append("_Zoho Assist integration._")
        if lead:
            block.append(lead)
        block.extend(f"- {p}" for p in points)
        block.append(f"Source: {url}")
        sections.append("\n".join(block))

    (_ZOHO_DIR / "zoho_products_summary.md").write_text(
        "\n\n".join(sections).strip() + "\n", encoding="utf-8"
    )
    return written, missing


def main(argv: List[str] | None = None) -> int:
    if settings.mock_web:
        print("MOCK_WEB is on — refusing to build the catalog from canned data. "
              "Run with MOCK_WEB=0.")
        return 1
    written, missing = build()
    print(f"Wrote {written} product doc(s) + zoho_products_summary.md under docs/zoho/")
    print(f"  full docs: docs/zoho/products/  ·  summary: docs/zoho/zoho_products_summary.md")
    if missing:
        print("Skipped (no extractable content — likely JS-rendered): "
              + ", ".join(missing))
    return 0


if __name__ == "__main__":
    sys.exit(main())
