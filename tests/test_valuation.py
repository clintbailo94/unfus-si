import csv
from pathlib import Path

import pytest

from si_domains.valuation import VALUATION_FIELDS, write_valuations


EVIDENCE_FIELDS = [
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
]


def _write_csv(path: Path, fields: list[str], rows: list[dict[str, str]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def _sale(evidence_id: str, domain: str, amount: str, **overrides: str) -> dict[str, str]:
    row = {
        "evidence_id": evidence_id,
        "access_date_utc": "2026-10-13",
        "sold_domain": domain,
        "sale_category": "technology",
        "amount": amount,
        "currency": "USD",
        "transaction_date": "2025-02-01",
        "report_date": "2025-02-02",
        "venue": "Synthetic test fixture",
        "source_url": f"https://example.test/sales/{evidence_id}",
        "evidence_type": "completed_sale",
        "relevance": "direct_comparable",
        "limitations": "Synthetic fixture only; not a real transaction.",
    }
    return {**row, **overrides}


@pytest.mark.parametrize(
    ("scenario", "evidence", "expected_status"),
    [
        (
            "asking_only",
            [_sale("ASK-1", "novara.si", "900", evidence_type="asking_price")],
            "insufficiently supported",
        ),
        (
            "unrelated",
            [_sale("OTHER-1", "longenterpriseplatform.si", "4000")],
            "insufficiently supported",
        ),
        ("absent", [], "insufficiently supported"),
        (
            "blocked",
            [{
                "evidence_id": "BLOCK-1",
                "access_date_utc": "2026-10-13",
                "sold_domain": "",
                "sale_category": "",
                "amount": "",
                "currency": "",
                "transaction_date": "",
                "report_date": "",
                "venue": "",
                "source_url": "https://example.test/search",
                "evidence_type": "unsupported",
                "relevance": "unavailable",
                "limitations": "Public source was blocked; no per-domain search ran.",
            }],
            "insufficiently supported",
        ),
        (
            "defensible_synthetic_comps",
            [
                _sale("SYN-1", "bright.si", "500"),
                _sale("SYN-2", "cloudy.si", "800"),
            ],
            "supported_speculative_range",
        ),
    ],
)
def test_valuation_ranges_require_traceable_relevant_completed_sales(
    tmp_path, scenario, evidence, expected_status
):
    shortlist = tmp_path / "shortlist.csv"
    evidence_path = tmp_path / "valuation_evidence.csv"
    first = tmp_path / f"{scenario}-first.csv"
    second = tmp_path / f"{scenario}-second.csv"
    _write_csv(shortlist, ["rank", "domain", "category"], [{"rank": "1", "domain": "novara.si", "category": "technology"}])
    _write_csv(evidence_path, EVIDENCE_FIELDS, evidence)

    assert write_valuations(shortlist, evidence_path, first) == 1
    assert write_valuations(shortlist, evidence_path, second) == 1
    assert first.read_bytes() == second.read_bytes()

    with first.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        rows = list(reader)
        assert reader.fieldnames == list(VALUATION_FIELDS)
    row = rows[0]
    assert row["status"] == expected_status
    if expected_status == "supported_speculative_range":
        assert (row["currency"], row["low"], row["high"]) == ("USD", "500", "800")
        refs = set(row["evidence_ids"].split(";"))
        assert refs == {"SYN-1", "SYN-2"}
        assert all(item["evidence_type"] == "completed_sale" for item in evidence if item["evidence_id"] in refs)
    else:
        assert row["currency"] == row["low"] == row["high"] == ""

