"""Conservative offline valuation from curated completed-sale evidence."""

from __future__ import annotations

import csv
import re
from datetime import date
from decimal import Decimal, InvalidOperation
from pathlib import Path
from urllib.parse import urlparse


VALUATION_EVIDENCE_FIELDS = (
    "evidence_id",
    "access_date_utc",
    "sold_domain",
    "sale_category",
    "amount",
    "currency",
    "transaction_date",
    "report_date",
    "venue",
    "source_url",
    "evidence_type",
    "relevance",
    "limitations",
)
VALUATION_FIELDS = (
    "rank",
    "domain",
    "status",
    "currency",
    "low",
    "high",
    "evidence_ids",
    "rationale",
)
_DOMAIN = re.compile(r"^([a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?)\.([a-z]{2,})$")
_EVIDENCE_TYPES = frozenset({"completed_sale", "asking_price", "unsupported"})


def _read_csv(path: str | Path, required: set[str], description: str) -> list[dict[str, str]]:
    with Path(path).open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if not reader.fieldnames or not required.issubset(reader.fieldnames):
            raise ValueError(f"{description} CSV is missing required columns")
        return [{key: (value or "").strip() for key, value in row.items() if key} for row in reader]


def validate_valuation_evidence(rows: list[dict[str, str]]) -> dict[str, dict[str, str]]:
    indexed: dict[str, dict[str, str]] = {}
    for row in rows:
        evidence_id = row.get("evidence_id", "")
        if not evidence_id or evidence_id in indexed:
            raise ValueError(f"valuation evidence has a blank or duplicate evidence_id: {evidence_id!r}")
        evidence_type = row.get("evidence_type", "")
        if evidence_type not in _EVIDENCE_TYPES:
            raise ValueError(f"invalid valuation evidence_type for {evidence_id}")
        parsed_url = urlparse(row.get("source_url", ""))
        if parsed_url.scheme not in {"http", "https"} or not parsed_url.netloc:
            raise ValueError(f"valuation evidence needs a public source_url for {evidence_id}")
        try:
            date.fromisoformat(row.get("access_date_utc", ""))
            for date_field in ("transaction_date", "report_date"):
                if row.get(date_field):
                    date.fromisoformat(row[date_field])
        except ValueError as exc:
            raise ValueError(f"valuation evidence has an invalid ISO date for {evidence_id}") from exc
        if evidence_type == "completed_sale":
            sale_domain = row.get("sold_domain", "").casefold()
            if not _DOMAIN.fullmatch(sale_domain):
                raise ValueError(f"completed sale needs a sold domain for {evidence_id}")
            if not row.get("sale_category"):
                raise ValueError(f"completed sale needs a sale category for {evidence_id}")
            try:
                amount = Decimal(row.get("amount", ""))
            except InvalidOperation as exc:
                raise ValueError(f"completed sale has invalid amount for {evidence_id}") from exc
            if not amount.is_finite() or amount <= 0:
                raise ValueError(f"completed sale amount must be positive for {evidence_id}")
            if not re.fullmatch(r"[A-Z]{3}", row.get("currency", "")):
                raise ValueError(f"completed sale needs an ISO currency code for {evidence_id}")
            if not (row.get("transaction_date") or row.get("report_date")):
                raise ValueError(f"completed sale needs a transaction or report date for {evidence_id}")
            if not row.get("venue") or not row.get("relevance") or not row.get("limitations"):
                raise ValueError(f"completed sale needs venue, relevance, and limitations for {evidence_id}")
        indexed[evidence_id] = row
    return indexed


def read_valuation_evidence(path: str | Path) -> tuple[list[dict[str, str]], dict[str, dict[str, str]]]:
    rows = _read_csv(path, set(VALUATION_EVIDENCE_FIELDS), "valuation evidence")
    return rows, validate_valuation_evidence(rows)


def eligible_comps(
    domain: str, category: str, rows: list[dict[str, str]]
) -> list[dict[str, str]]:
    label_match = _DOMAIN.fullmatch(domain.casefold())
    if not label_match:
        raise ValueError(f"invalid target domain for valuation: {domain}")
    target_label, target_extension = label_match.groups()
    eligible: list[dict[str, str]] = []
    for row in rows:
        sale_match = _DOMAIN.fullmatch(row.get("sold_domain", "").casefold())
        if row.get("evidence_type") != "completed_sale" or not sale_match:
            continue
        sale_label, sale_extension = sale_match.groups()
        if row.get("relevance") != "direct_comparable":
            continue
        if sale_extension != target_extension or target_extension != "si":
            continue
        if row.get("sale_category") != category or abs(len(sale_label) - len(target_label)) > 2:
            continue
        if row.get("currency") not in {"GBP", "USD"}:
            continue
        eligible.append(row)
    return eligible


def _amount(value: str) -> str:
    amount = Decimal(value).normalize()
    return format(amount, "f")


def write_valuations(
    shortlist_path: str | Path,
    evidence_path: str | Path,
    output_path: str | Path,
) -> int:
    shortlist = _read_csv(shortlist_path, {"domain", "category"}, "shortlist")
    evidence_rows, _index = read_valuation_evidence(evidence_path)
    evidence_rows = sorted(evidence_rows, key=lambda row: row["evidence_id"])
    seen: set[str] = set()
    output_rows: list[dict[str, str]] = []
    for rank, candidate in enumerate(shortlist, start=1):
        domain = candidate["domain"].casefold()
        if domain in seen:
            raise ValueError(f"duplicate domain in shortlist for valuation: {domain}")
        seen.add(domain)
        comparable = eligible_comps(domain, candidate["category"], evidence_rows)
        amounts_by_currency: dict[str, list[tuple[Decimal, dict[str, str]]]] = {}
        for row in comparable:
            amounts_by_currency.setdefault(row["currency"], []).append((Decimal(row["amount"]), row))
        supported: list[tuple[str, list[tuple[Decimal, dict[str, str]]]]] = []
        for currency, items in sorted(amounts_by_currency.items()):
            distinct_sales = {row["sold_domain"] for _amount_value, row in items}
            if len(distinct_sales) >= 2:
                supported.append((currency, items))
        if len(supported) == 1:
            currency, items = supported[0]
            low = min(amount for amount, _row in items)
            high = max(amount for amount, _row in items)
            evidence_ids = ";".join(sorted({row["evidence_id"] for _amount_value, row in items}))
            rationale = (
                f"Speculative {currency} span from {len({row['sold_domain'] for _amount_value, row in items})} cited .si completed sales "
                f"in {candidate['category']} with labels within two characters; liquidity and buyer differences remain."
            )
            status = "supported_speculative_range"
            low_text, high_text = _amount(str(low)), _amount(str(high))
        else:
            status = "insufficiently supported"
            currency = low_text = high_text = ""
            evidence_ids = ";".join(row["evidence_id"] for row in evidence_rows)
            rationale = (
                "No two distinct, same-currency .si completed sales sufficiently close in category and label length; "
                "asking prices and other extensions are context only."
            )
        output_rows.append(
            {
                "rank": candidate.get("rank") or str(rank),
                "domain": domain,
                "status": status,
                "currency": currency,
                "low": low_text,
                "high": high_text,
                "evidence_ids": evidence_ids,
                "rationale": rationale,
            }
        )

    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=VALUATION_FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(output_rows)
    return len(output_rows)

