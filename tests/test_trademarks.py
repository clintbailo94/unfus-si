import csv
from pathlib import Path

import pytest

from si_domains.trademarks import (
    TRADEMARK_EVIDENCE_FIELDS,
    TRADEMARK_SUMMARY_FIELDS,
    normalize_seed,
    write_trademark_summary,
)


EVIDENCE_FIELDS = list(TRADEMARK_EVIDENCE_FIELDS)


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
        "result_url": f"{source_url}?query=novara",
        "mark_number": "",
        "mark_name": "",
        "mark_status": "",
        "classes": "",
        "notes": "Synthetic test evidence; not a real public mark search.",
        "proof_kind": "",
        "proof_path": "",
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


def _candidate(path: Path, label: str, category: str, seed: str) -> None:
    _write_csv(
        path,
        ["domain_label", "category", "method", "seed", "tags", "quality_score"],
        [{"domain_label": label, "category": category, "method": "hack-suffix", "seed": seed, "tags": "", "quality_score": "80"}],
    )


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
    candidates_path = tmp_path / "candidates.csv"
    _write_csv(domains, ["rank", "domain"], [{"rank": "1", "domain": "novara.si"}])
    _candidate(candidates_path, "novara", "technology", "novara")
    _write_csv(evidence_path, EVIDENCE_FIELDS, evidence)

    assert write_trademark_summary(evidence_path, domains, summary_path, candidates_path=candidates_path) == 1

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


@pytest.mark.parametrize(
    ("scenario", "expected_status", "expected_score", "query_key"),
    [
        ("exact_label_and_seed", "limited_screen_no_obvious_match", "80", "query"),
        ("wrong_exact_query", "unverified", "70", "query"),
        ("missing_seed_query", "unverified", "70", "query"),
        ("newer_blocked_seed", "blocked", "70", "query"),
        ("cosmetic_home_query", "unverified", "70", "synthetic-query"),
    ],
)
def test_hack_coverage_requires_each_current_exact_query(
    tmp_path, scenario, expected_status, expected_score, query_key
):
    source_urls = {
        "TMview": "https://www.tmdn.org/tmview/",
        "UKIPO": "https://trademarks.ipo.gov.uk/ipo-tmtext",
        "USPTO": "https://tmsearch.uspto.gov/",
    }
    queries = {
        "wrong_exact_query": ["unrelated", "unfussy"],
        "missing_seed_query": ["unfus"],
    }.get(scenario, ["unfus", "unfussy"])
    evidence = []
    for source, source_url in source_urls.items():
        for index, query in enumerate(queries):
            status = "blocked" if scenario == "newer_blocked_seed" and source == "TMview" and query == "unfussy" else "no_obvious_match"
            evidence.append(
                _evidence(
                    f"{source}-{index}", source, status,
                    domain="unfus.si",
                    query=query,
                    source_url=source_url,
                    result_url="" if status == "blocked" else f"{source_url}?{query_key}={query}",
                    utc_timestamp="2026-10-13T12:00:00Z" if index == 0 else "2026-10-13T12:01:00Z",
                    notes="Synthetic query-coverage fixture.",
                )
            )
        if scenario == "newer_blocked_seed" and source == "TMview":
            evidence.append(
                _evidence(
                    "TMview-newer-blocked", source, "blocked",
                    domain="unfus.si", query="unfussy", source_url=source_url, result_url="",
                    utc_timestamp="2026-10-13T12:02:00Z", notes="Synthetic later blocked state.",
                )
            )

    evidence_path = tmp_path / "trademark_evidence.csv"
    domains_path = tmp_path / "domains.csv"
    summary_path = tmp_path / "summary.csv"
    candidates_path = tmp_path / "candidates.csv"
    _write_csv(evidence_path, EVIDENCE_FIELDS, evidence)
    _write_csv(domains_path, ["rank", "domain"], [{"rank": "1", "domain": "unfus.si"}])
    _candidate(candidates_path, "unfus", "domain_hacks", "unfussy")

    assert write_trademark_summary(
        evidence_path, domains_path, summary_path, candidates_path=candidates_path
    ) == 1
    with summary_path.open(encoding="utf-8", newline="") as handle:
        row = next(csv.DictReader(handle))
    assert row["status"] == expected_status, scenario
    assert row["trademark_score"] == expected_score, scenario
    if scenario == "exact_label_and_seed":
        assert normalize_seed("tryto + see") == "try to see"
        assert "[2/2]" in row["coverage"]
    if scenario == "newer_blocked_seed":
        assert "[1/2]" in row["coverage"]


@pytest.mark.parametrize(
    ("proof_path", "write_proof", "should_pass"),
    [
        ("proofs/tmview.png", True, True),
        ("../outside.png", False, False),
        ("proofs/missing.png", False, False),
    ],
)
def test_portable_proof_paths_are_relative_present_and_query_associated(
    tmp_path, proof_path, write_proof, should_pass
):
    source_urls = {
        "TMview": "https://www.tmdn.org/tmview/",
        "UKIPO": "https://trademarks.ipo.gov.uk/ipo-tmtext",
        "USPTO": "https://tmsearch.uspto.gov/",
    }
    evidence = [
        _evidence(f"{source}-1", source, "no_obvious_match", query="novara", result_url=f"{source_url}?query=novara")
        for source, source_url in source_urls.items()
    ]
    evidence[0]["result_url"] = source_urls["TMview"]
    evidence[0]["proof_kind"] = "screenshot"
    evidence[0]["proof_path"] = proof_path
    output_root = tmp_path / "output"
    evidence_path = output_root / "trademark_evidence.csv"
    output_root.mkdir()
    if write_proof:
        proof_file = output_root / proof_path
        proof_file.parent.mkdir(parents=True)
        proof_file.write_bytes(b"synthetic proof fixture")
    domains_path = tmp_path / "domains.csv"
    candidates_path = tmp_path / "candidates.csv"
    summary_path = tmp_path / "summary.csv"
    _write_csv(evidence_path, EVIDENCE_FIELDS, evidence)
    _write_csv(domains_path, ["rank", "domain"], [{"rank": "1", "domain": "novara.si"}])
    _candidate(candidates_path, "novara", "technology", "novara")

    if should_pass:
        assert write_trademark_summary(
            evidence_path, domains_path, summary_path, candidates_path=candidates_path
        ) == 1
        with summary_path.open(encoding="utf-8", newline="") as handle:
            assert next(csv.DictReader(handle))["status"] == "limited_screen_no_obvious_match"
    else:
        with pytest.raises(ValueError, match="proof_path|proof file"):
            write_trademark_summary(
                evidence_path, domains_path, summary_path, candidates_path=candidates_path
            )

