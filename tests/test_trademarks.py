import csv
from pathlib import Path

import pytest

from si_domains.trademarks import TRADEMARK_SUMMARY_FIELDS, write_trademark_summary


EVIDENCE_FIELDS = [
    "evidence_id",
    "domain",
    "source",
    "jurisdiction",
    "query",
    "utc_timestamp",
    "result_status",
    "source_url",
    "result_url",
    "mark_number",
    "mark_name",
    "mark_status",
    "classes",
    "notes",
]


def _write_csv(path: Path, fields: list[str], rows: list[dict[str, str]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def _evidence(evidence_id: str, source: str, status: str, **overrides: str) -> dict[str, str]:
    source_url = {
        "TMview": "https://www.tmdn.org/tmview/",
        "UKIPO": "https://trademarks.ipo.gov.uk/ipo-tmtext",
        "USPTO": "https://tmsearch.uspto.gov/",
    }[source]
    row = {
        "evidence_id": evidence_id,
        "domain": "novara.si",
        "source": source,
        "jurisdiction": {"TMview": "EU/participating offices", "UKIPO": "UK", "USPTO": "US"}[source],
        "query": "novara",
        "utc_timestamp": "2026-10-13T12:00:00Z",
        "result_status": status,
        "source_url": source_url,
        "result_url": f"{source_url}?synthetic-query=novara",
        "mark_number": "",
        "mark_name": "",
        "mark_status": "",
        "classes": "",
        "notes": "Synthetic test evidence; not a real public mark search.",
    }
    if status == "possible_conflict":
        row.update(
            mark_number="SYNTH-001",
            mark_name="Synthetic test mark",
            mark_status="registered",
            classes="9",
        )
    return {**row, **overrides}


def _source_attempt(source: str, status: str) -> dict[str, str]:
    row = _evidence(f"{source.upper()}-ACCESS", source, status)
    row.update(
        domain="*",
        query="source access check",
        result_url="",
        notes="Synthetic source-wide attempt; no per-domain query ran.",
    )
    return row


@pytest.mark.parametrize(
    ("scenario", "evidence", "expected_status", "expected_score"),
    [
        (
            "clear_limited_screen",
            [_evidence("TM-1", "TMview", "no_obvious_match"), _evidence("UK-1", "UKIPO", "no_obvious_match"), _evidence("US-1", "USPTO", "no_obvious_match")],
            "limited_screen_no_obvious_match",
            "80",
        ),
        (
            "conflict_overrides_other_no_matches",
            [_evidence("TM-1", "TMview", "possible_conflict"), _evidence("UK-1", "UKIPO", "no_obvious_match"), _evidence("US-1", "USPTO", "no_obvious_match")],
            "needs legal review",
            "25",
        ),
        (
            "blocked_sources_do_not_clear",
            [_source_attempt("TMview", "blocked"), _source_attempt("UKIPO", "blocked"), _source_attempt("USPTO", "blocked")],
            "blocked",
            "70",
        ),
        (
            "unverified_sources_do_not_clear",
            [_source_attempt("TMview", "unverified"), _source_attempt("UKIPO", "unverified"), _source_attempt("USPTO", "unverified")],
            "unverified",
            "70",
        ),
        ("absent_evidence_does_not_clear", [], "unverified", "70"),
    ],
)
def test_trademark_aggregation_preserves_conservative_status_and_provenance(
    tmp_path, scenario, evidence, expected_status, expected_score
):
    domains = tmp_path / "domains.csv"
    evidence_path = tmp_path / "trademark_evidence.csv"
    summary_path = tmp_path / "trademark_summary.csv"
    _write_csv(domains, ["rank", "domain"], [{"rank": "1", "domain": "novara.si"}])
    _write_csv(evidence_path, EVIDENCE_FIELDS, evidence)

    assert write_trademark_summary(evidence_path, domains, summary_path) == 1

    with summary_path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        rows = list(reader)
        assert reader.fieldnames == list(TRADEMARK_SUMMARY_FIELDS)
    row = rows[0]
    assert row["status"] == expected_status
    assert row["trademark_score"] == expected_score
    assert row["coverage"]
    assert set(filter(None, row["evidence_ids"].split(";"))) == {
        item["evidence_id"] for item in evidence
    }
    if expected_status in {"blocked", "unverified"}:
        assert "limited_screen_no_obvious_match" != row["status"]

