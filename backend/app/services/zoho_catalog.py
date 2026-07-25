"""Zoho product catalog seed — the internal "Plane B" knowledge source list.

Each entry is one keyless, static zoho.com page to cache into the product catalog.
The builder (`app/tools/build_zoho_catalog.py`) fetches these with NO LLM, writes a
clean full doc per product under docs/zoho/products/, and assembles the compact
docs/zoho/zoho_products_summary.md that feeds every brief.

Edit this list to curate the catalog — add a dict with product/url/kind and re-run the
builder. Only STATIC www.zoho.com pages work: the help.zoho.com/portal KB is a
JavaScript app and yields nothing to a keyless fetch, so product-overview or
help/marketing pages are used for those products instead.

kind: "overview"     — what the product is / does (for pain→product matching)
      "integration"  — how Zoho Assist connects to another product
"""
from __future__ import annotations

import re
from typing import Dict, List

ZOHO_SOURCES: List[Dict[str, str]] = [
    # --- Product overviews (user-provided help pages + verified static substitutes) ---
    {"product": "Zoho Payroll", "kind": "overview",
     "url": "https://www.zoho.com/in/payroll/help/employer/basics/"},
    {"product": "Zoho Expense", "kind": "overview",
     "url": "https://www.zoho.com/in/expense/help/getting-started/how-zoho-expense-works/"},
    # KB portal (help.zoho.com) links the user gave are JS-only; these static product
    # pages carry the same "what it does" content and extract keyless.
    {"product": "Zoho Bigin", "kind": "overview", "url": "https://www.zoho.com/bigin/"},
    {"product": "Zoho Bookings", "kind": "overview", "url": "https://www.zoho.com/bookings/"},
    {"product": "Zoho Forms", "kind": "overview", "url": "https://www.zoho.com/forms/"},
    {"product": "Zoho SalesIQ", "kind": "overview", "url": "https://www.zoho.com/salesiq/"},
    {"product": "Zoho Thrive", "kind": "overview", "url": "https://www.zoho.com/thrive/"},
    {"product": "Zoho RouteIQ", "kind": "overview", "url": "https://www.zoho.com/routeiq/"},

    # --- Zoho Assist integrations (user-provided; static help pages) ---
    {"product": "Zoho Assist + Zoho Desk", "kind": "integration",
     "url": "https://www.zoho.com/assist/help/integrations/zoho-desk.html"},
    {"product": "Zoho Assist + Zoho SalesIQ", "kind": "integration",
     "url": "https://www.zoho.com/assist/help/integrations/zoho-salesiq.html"},
    {"product": "Zoho Assist + Zoho CRM", "kind": "integration",
     "url": "https://www.zoho.com/assist/help/integrations/zoho-crm.html"},
    {"product": "Zoho Assist + Zoho Meeting", "kind": "integration",
     "url": "https://www.zoho.com/assist/help/integrations/zoho-meeting.html"},
    {"product": "Zoho Assist + Zoho Bookings", "kind": "integration",
     "url": "https://www.zoho.com/assist/help/integrations/zoho-bookings.html"},
    {"product": "Zoho Assist + Zoho Flow", "kind": "integration",
     "url": "https://www.zoho.com/assist/help/integrations/zoho-flow.html"},
    {"product": "Zoho Assist + Zoho Mail", "kind": "integration",
     "url": "https://www.zoho.com/assist/help/integrations/zoho-mail.html"},
]


def slug_for(product: str) -> str:
    """Filesystem-safe slug for a product name."""
    s = re.sub(r"[^a-z0-9]+", "-", product.lower()).strip("-")
    return s or "zoho"
