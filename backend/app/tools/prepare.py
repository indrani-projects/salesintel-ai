"""CLI: prepare (fetch + extract + keyword-filter, NO LLM) cached web docs.

Run from backend/ with the checked-in venv:

    .\\.venv\\Scripts\\python.exe -m app.tools.prepare "Freshworks"
    .\\.venv\\Scripts\\python.exe -m app.tools.prepare --all
    .\\.venv\\Scripts\\python.exe -m app.tools.prepare "Braze" --force

Writes backend/.cache/prepared/<slug>/ (clean .md docs + manifest.json). Pre-seed the
five research-guide companies once with --all so demos are instant and quota-free.
"""
from __future__ import annotations

import argparse
import sys
from typing import List

from app.services import prep

# The five publicly-traded B2B SaaS targets from the research guide (docs/shared).
GUIDE_COMPANIES = ["Freshworks", "Braze", "Sprout Social", "Amplitude", "Zuora"]


def _run_one(company: str, force: bool) -> int:
    manifest = prep.prepare_company(company, force=force)
    docs = manifest.get("docs", [])
    print(f"\n{company}  ->  backend/.cache/prepared/{manifest.get('slug')}/")
    if not docs:
        print("  (no relevant sources found — check connectivity or try --force)")
        return 0
    for d in docs:
        cats = ", ".join(d.get("categories", [])) or "-"
        print(
            f"  {d['file']:<28} cred {d['credibility']:>3}/100 "
            f"({d['source_type']:<12}) [{cats}]"
        )
    return len(docs)


def main(argv: List[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        prog="python -m app.tools.prepare",
        description="Prepare cached, keyword-filtered web docs for a company (no LLM).",
    )
    ap.add_argument("company", nargs="?", help="Company name, e.g. \"Freshworks\"")
    ap.add_argument("--all", action="store_true", help="Prepare all 5 guide companies")
    ap.add_argument("--force", action="store_true", help="Ignore the TTL cache and re-fetch")
    args = ap.parse_args(argv)

    if not args.all and not args.company:
        ap.error("provide a company name or --all")

    companies = GUIDE_COMPANIES if args.all else [args.company]
    total = 0
    for company in companies:
        total += _run_one(company, args.force)
    print(f"\nDone. {total} prepared doc(s) across {len(companies)} company(ies).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
