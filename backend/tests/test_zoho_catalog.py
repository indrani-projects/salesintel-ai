"""Zoho catalog seed integrity + deterministic condensation (offline, NO LLM)."""
from app.services import condense
from app.services.zoho_catalog import ZOHO_SOURCES, slug_for

_MD = """
# Zoho Expense

Zoho Expense is an online expense reporting application. It records and reports all
your business expenses. Receipts are autoscanned into expenses automatically.

## Key features
- ### Autoscan- Turn receipts into expenses
- STEP 01### Create a report from expenses
- Approve reports on the go
- Approve reports on the go
- x
"""


def test_lead_paragraph_is_first_prose_sentence_trimmed():
    lead = condense.lead_paragraph(_MD, max_chars=80)
    assert lead.startswith("Zoho Expense is an online expense reporting application")
    assert "#" not in lead and "- " not in lead
    assert len(lead) <= 81  # trimmed at a sentence boundary near the cap


def test_key_points_clean_dedupe_and_cap():
    pts = condense.key_points(_MD, cap=5)
    # markdown heading + STEP prefixes stripped (leading markers gone)
    assert any(p.startswith("Autoscan") and "Turn receipts into expenses" in p for p in pts)
    assert any(p.startswith("Create a report") for p in pts)
    # de-duped, and the too-short "x" bullet dropped
    assert pts.count("Approve reports on the go") == 1
    assert "x" not in pts
    assert all(not p.startswith(("#", "-", "*")) for p in pts)


def test_catalog_entries_are_well_formed():
    seen: set[str] = set()
    for src in ZOHO_SOURCES:
        assert src["product"] and src["url"], src
        assert src.get("kind") in {"overview", "integration"}
        assert src["url"].startswith("https://www.zoho.com/"), src["url"]
        # help.zoho.com KB portal is JS-only — must never be seeded (won't extract keyless)
        assert "help.zoho.com" not in src["url"], src["url"]
        slug = slug_for(src["product"])
        assert slug and slug not in seen, f"duplicate slug {slug}"
        seen.add(slug)


def test_slug_for():
    assert slug_for("Zoho Payroll") == "zoho-payroll"
    assert slug_for("Zoho Assist + Zoho Desk") == "zoho-assist-zoho-desk"
