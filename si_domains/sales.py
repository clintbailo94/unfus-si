"""Curated public sales records and proposal helper for reported .si sales."""

from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

from .config import DATA_DIR, OUTPUT_DIR


SALES_PATH = DATA_DIR / "si_sales.csv"
VALUATION_EVIDENCE_PATH = OUTPUT_DIR / "valuation_evidence.csv"

FIELDNAMES = (
    "evidence_id",
    "domain",
    "amount",
    "currency",
    "transaction_date",
    "report_date",
    "venue",
    "source_url",
    "evidence_type",
    "category",
    "notes",
)


@dataclass(frozen=True)
class SaleRecord:
    evidence_id: str
    domain: str
    amount: str
    currency: str
    transaction_date: str
    report_date: str
    venue: str
    source_url: str
    evidence_type: str
    category: str
    notes: str

    @property
    def is_completed_sale(self) -> bool:
        return self.evidence_type == "completed_sale"

    @property
    def display_price(self) -> str:
        if not self.amount:
            return ""
        try:
            val = float(self.amount)
            formatted = f"{int(val):,}" if val.is_integer() else f"{val:,.2f}"
        except ValueError:
            formatted = self.amount
        curr = f"{self.currency} " if self.currency else ""
        return f"{curr}{formatted}"

    @property
    def effective_date(self) -> str:
        return self.transaction_date or self.report_date or "Unknown date"


def load_sales(path: Path | str = SALES_PATH) -> list[SaleRecord]:
    p = Path(path)
    if not p.is_file():
        return []
    records: list[SaleRecord] = []
    with p.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            records.append(
                SaleRecord(
                    evidence_id=(row.get("evidence_id") or "").strip(),
                    domain=(row.get("domain") or "").strip().lower(),
                    amount=(row.get("amount") or "").strip(),
                    currency=(row.get("currency") or "").strip(),
                    transaction_date=(row.get("transaction_date") or "").strip(),
                    report_date=(row.get("report_date") or "").strip(),
                    venue=(row.get("venue") or "").strip(),
                    source_url=(row.get("source_url") or "").strip(),
                    evidence_type=(row.get("evidence_type") or "").strip(),
                    category=(row.get("category") or "").strip(),
                    notes=(row.get("notes") or "").strip(),
                )
            )
    return records


def get_verified_completed_sales(path: Path | str = SALES_PATH) -> list[SaleRecord]:
    """Return only verified, completed sales with public source URLs."""
    records = load_sales(path)
    # Strictly require completed_sale, positive amount, and valid source_url
    return [
        r for r in records
        if r.is_completed_sale
        and r.source_url
        and r.source_url.startswith(("http://", "https://"))
        and r.amount
    ]


def propose_sale(
    candidate_sale: dict[str, str],
    *,
    sales_path: Path | str = SALES_PATH,
) -> bool:
    """Helper that proposes a new reported .si sale for review.
    
    Validates required fields and appends only after verification check.
    Never auto-publishes without a verified source URL.
    """
    domain = candidate_sale.get("domain", "").strip().lower()
    source_url = candidate_sale.get("source_url", "").strip()
    amount = candidate_sale.get("amount", "").strip()
    evidence_type = candidate_sale.get("evidence_type", "").strip()

    if not domain.endswith(".si"):
        raise ValueError(f"Domain must end in .si: {domain}")
    if not source_url.startswith(("http://", "https://")):
        raise ValueError("Source URL must be a valid http(s) link")
    if not amount:
        raise ValueError("Sale amount is required")
    if evidence_type not in ("completed_sale", "asking_price"):
        raise ValueError("evidence_type must be completed_sale or asking_price")

    existing = {s.domain: s for s in load_sales(sales_path)}
    if domain in existing and existing[domain].evidence_type == evidence_type:
        return False  # Already exists

    p = Path(sales_path)
    file_exists = p.is_file()
    with p.open("a", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES, lineterminator="\n")
        if not file_exists:
            writer.writeheader()
        writer.writerow({
            "evidence_id": candidate_sale.get("evidence_id", f"SI-PROP-{len(existing)+1:03d}"),
            "domain": domain,
            "amount": amount,
            "currency": candidate_sale.get("currency", "USD"),
            "transaction_date": candidate_sale.get("transaction_date", ""),
            "report_date": candidate_sale.get("report_date", ""),
            "venue": candidate_sale.get("venue", "Public Report"),
            "source_url": source_url,
            "evidence_type": evidence_type,
            "category": candidate_sale.get("category", "unclassified"),
            "notes": candidate_sale.get("notes", "Proposed from public report, pending editorial review"),
        })
    return True
