"""Optional per-company enrichment for the 5 target companies in the research guide
(docs/shared). These are HINTS only — the web-intel path is generic and works for
any company name without an entry here. When a hint exists it adds the stock ticker
(for future ticker-based financial APIs) and a ready Zoho pitch angle to the intel.
"""
from __future__ import annotations

import re
from typing import Optional


def _norm(s: str) -> str:
    return re.sub(r"[^a-z0-9]", "", (s or "").lower())


# name-key -> {ticker, competitors, zoho_products, why}
COMPANY_HINTS = {
    "freshworks": {
        "ticker": "FRSH",
        "competitors": ["Zoho", "Salesforce"],
        "zoho_products": ["Zoho Payroll", "Zoho Expense", "Zoho Analytics"],
        "why": "CRM & helpdesk SaaS needing integrated payroll, expense & analytics; "
               "Zoho One can undercut on price across the full suite.",
    },
    "braze": {
        "ticker": "BRZE",
        "competitors": ["Salesforce", "Workday"],
        "zoho_products": ["Zoho CRM", "Zoho People", "Zoho Books"],
        "why": "Customer-engagement platform scaling fast; needs CRM for its own sales "
               "org plus HR & finance tools.",
    },
    "sproutsocial": {
        "ticker": "SPT",
        "competitors": ["Salesforce"],
        "zoho_products": ["Zoho CRM", "Zoho Campaigns", "Zoho Desk"],
        "why": "Social-media management SaaS with a growing sales team on Salesforce; "
               "Zoho can displace with a cost-effective integrated suite.",
    },
    "amplitude": {
        "ticker": "AMPL",
        "competitors": ["Salesforce", "Workday", "QuickBooks"],
        "zoho_products": ["Zoho CRM", "Zoho People", "Zoho Books"],
        "why": "Product-analytics firm needing CRM, HR & finance tooling beyond its "
               "core product.",
    },
    "zuora": {
        "ticker": "ZUO",
        "competitors": ["Workday", "Salesforce"],
        "zoho_products": ["Zoho People", "Zoho Projects", "Zoho CRM"],
        "why": "Subscription-management platform whose own ops team needs HR, project "
               "management & CRM.",
    },
}


def hint_for(company_name: str) -> Optional[dict]:
    key = _norm(company_name)
    if not key:
        return None
    for name_key, hint in COMPANY_HINTS.items():
        if name_key in key or key in name_key:
            return hint
    return None
