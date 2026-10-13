import csv
from decimal import Decimal
from pathlib import Path

from si_domains.cli import main
from si_domains.research import validate_research, write_opportunities
from si_domains.scoring import weighted_total
from si_domains.trademarks import write_trademark_summary
from si_domains.valuation import write_valuations


CANDIDATE_FIELDS = ["domain_label", "category", "method", "seed", "tags", "quality_score"]
RDAP_FIELDS = ["domain", "category", "http_status", "utc_timestamp", "attempts", "classification", "error"]
WHOIS_FIELDS = ["domain", "category", "utc_timestamp", "classification", "matched_pattern", "error"]
TM_FIELDS = ["evidence_id", "domain", "source", "jurisdiction", "query", "utc_timestamp", "result_status", "source_url", "result_url", "mark_number", "mark_name", "mark_status", "classes", "notes"]
VALUATION_EVIDENCE_FIELDS = ["evidence_id", "access_date_utc", "sold_domain", "sale_category", "amount", "currency", "transaction_date", "report_date", "venue", "source_url", "evidence_type", "relevance", "limitations"]


def _write_csv(path: Path, fields: list[str], rows: list[dict[str, str]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def _read(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def test_summary_injection_reranks_shortlist_and_joins_evidence(tmp_path, capsys):
    candidates_path = tmp_path / "candidates.csv"
    rdap_path = tmp_path / "rdap.csv"
    whois_path = tmp_path / "whois.csv"
    scores_path = tmp_path / "scores.csv"
    baseline_shortlist = tmp_path / "baseline-shortlist.csv"
    baseline_excluded = tmp_path / "baseline-excluded.csv"
    baseline_sample = tmp_path / "baseline-sample.csv"
    domains_path = tmp_path / "screen-domains.csv"
    tm_evidence_path = tmp_path / "trademark_evidence.csv"
    tm_summary_path = tmp_path / "trademark_summary.csv"
    final_shortlist = tmp_path / "shortlist.csv"
    excluded_path = tmp_path / "excluded.csv"
    sample_path = tmp_path / "sample.csv"
    valuation_evidence = tmp_path / "valuation_evidence.csv"
    valuations_path = tmp_path / "valuations.csv"
    opportunities_path = tmp_path / "opportunities.csv"

    labels = [f"same{index:03d}" for index in range(101)]
    candidates = [
        {"domain_label": label, "category": "technology", "method": "concept", "seed": label, "tags": "", "quality_score": "80"}
        for label in labels
    ]
    _write_csv(candidates_path, CANDIDATE_FIELDS, candidates)
    _write_csv(
        rdap_path,
        RDAP_FIELDS,
        [{"domain": f"{label}.si", "category": "technology", "http_status": "404", "utc_timestamp": "2026-10-13T10:00:00Z", "attempts": "1", "classification": "potentially_unregistered", "error": ""} for label in labels],
    )
    _write_csv(
        whois_path,
        WHOIS_FIELDS,
        [{"domain": f"{label}.si", "category": "technology", "utc_timestamp": "2026-10-13T11:00:00Z", "classification": "not_registered", "matched_pattern": "no_entries_found", "error": ""} for label in labels],
    )

    assert main(["score", "--input", str(candidates_path), "--rdap-evidence", str(rdap_path), "--out", str(scores_path)]) == 0
    assert main(["shortlist", "--input", str(candidates_path), "--rdap-evidence", str(rdap_path), "--whois-evidence", str(whois_path), "--scores", str(scores_path), "--out", str(baseline_shortlist), "--excluded", str(baseline_excluded), "--sample-out", str(baseline_sample)]) == 0
    initial_domains = _read(baseline_shortlist)
    assert "same100.si" not in {row["domain"] for row in initial_domains[:100]}

    _write_csv(domains_path, ["rank", "domain"], [{"rank": str(index), "domain": f"{label}.si"} for index, label in enumerate(labels, start=1)])
    tm_rows = []
    source_urls = {
        "TMview": "https://www.tmdn.org/tmview/",
        "UKIPO": "https://trademarks.ipo.gov.uk/ipo-tmtext",
        "USPTO": "https://tmsearch.uspto.gov/",
    }
    for label in labels:
        for source, jurisdiction in (("TMview", "EU/participating offices"), ("UKIPO", "UK"), ("USPTO", "US")):
            conflict = label == "same000" and source == "TMview"
            tm_rows.append({
                "evidence_id": f"{source}-{label}",
                "domain": f"{label}.si",
                "source": source,
                "jurisdiction": jurisdiction,
                "query": label,
                "utc_timestamp": "2026-10-13T12:00:00Z",
                "result_status": "possible_conflict" if conflict else "no_obvious_match",
                "source_url": source_urls[source],
                "result_url": f"{source_urls[source]}?synthetic-query={label}",
                "mark_number": "SYNTH-1" if conflict else "",
                "mark_name": "Synthetic test mark" if conflict else "",
                "mark_status": "registered" if conflict else "",
                "classes": "9" if conflict else "",
                "notes": "Synthetic e2e evidence; not a real mark search.",
            })
    _write_csv(tm_evidence_path, TM_FIELDS, tm_rows)
    assert write_trademark_summary(tm_evidence_path, domains_path, tm_summary_path) == 101

    assert main([
        "score", "--input", str(candidates_path), "--rdap-evidence", str(rdap_path),
        "--trademark-evidence", str(tm_summary_path), "--trademark-source-evidence", str(tm_evidence_path),
        "--out", str(scores_path),
    ]) == 0
    assert main(["shortlist", "--input", str(candidates_path), "--rdap-evidence", str(rdap_path), "--whois-evidence", str(whois_path), "--scores", str(scores_path), "--out", str(final_shortlist), "--excluded", str(excluded_path), "--sample-out", str(sample_path)]) == 0

    before = {row["domain"] for row in initial_domains[:100]}
    final_rows = _read(final_shortlist)
    after = {row["domain"] for row in final_rows[:100]}
    assert "same000.si" in before and "same000.si" not in after
    assert "same100.si" not in before and "same100.si" in after
    conflict_score = next(row for row in _read(scores_path) if row["domain"] == "same000.si")
    assert conflict_score["trademark"] == "25"
    assert Decimal(conflict_score["total"]) == weighted_total({
        name: int(conflict_score[name])
        for name in ("brandability", "commercial", "shortness", "hack", "resale", "trademark")
    })
    assert all(
        len(row["rationale"]) <= 140
        and row["rationale"].isascii()
        and row["rationale"].count("weakness:") == 1
        for row in _read(scores_path)
    )

    _write_csv(valuation_evidence, VALUATION_EVIDENCE_FIELDS, [])
    assert write_valuations(final_shortlist, valuation_evidence, valuations_path) == len(final_rows)
    assert write_opportunities(final_shortlist, scores_path, valuations_path, tm_summary_path, opportunities_path) == len(final_rows)
    opportunity = next(row for row in _read(opportunities_path) if row["domain"] == "same100.si")
    assert opportunity["trademark_status"] == "limited_screen_no_obvious_match"
    assert opportunity["trademark_evidence_ids"]
    assert opportunity["valuation_status"] == "insufficiently supported"
    assert opportunity["valuation_currency"] == opportunity["valuation_low"] == opportunity["valuation_high"] == ""
    assert validate_research(
        shortlist_path=final_shortlist,
        scores_path=scores_path,
        valuation_path=valuations_path,
        valuation_evidence_path=valuation_evidence,
        trademark_evidence_path=tm_evidence_path,
        trademark_summary_path=tm_summary_path,
        opportunities_path=opportunities_path,
    ) == 0

    # Source-wide access outcomes are provenance, not per-domain query results.
    global_rows = [
        {
            "evidence_id": "TMV-ACCESS-001",
            "domain": "*",
            "source": "TMview",
            "jurisdiction": "EU/participating offices",
            "query": "source access check; no domain query",
            "utc_timestamp": "2026-10-13T12:30:00Z",
            "result_status": "unverified",
            "source_url": source_urls["TMview"],
            "result_url": "",
            "mark_number": "",
            "mark_name": "",
            "mark_status": "",
            "classes": "",
            "notes": "Synthetic browser-unavailable fixture; no per-domain query ran.",
        },
        {
            "evidence_id": "UKIPO-ACCESS-001",
            "domain": "*",
            "source": "UKIPO",
            "jurisdiction": "UK",
            "query": "source access check; no domain query",
            "utc_timestamp": "2026-10-13T12:30:00Z",
            "result_status": "blocked",
            "source_url": source_urls["UKIPO"],
            "result_url": "",
            "mark_number": "",
            "mark_name": "",
            "mark_status": "",
            "classes": "",
            "notes": "Synthetic initial HTTP 403; not retried; no per-domain query ran.",
        },
        {
            "evidence_id": "USPTO-ACCESS-001",
            "domain": "*",
            "source": "USPTO",
            "jurisdiction": "US",
            "query": "source access check; no domain query",
            "utc_timestamp": "2026-10-13T12:30:00Z",
            "result_status": "unverified",
            "source_url": source_urls["USPTO"],
            "result_url": "",
            "mark_number": "",
            "mark_name": "",
            "mark_status": "",
            "classes": "",
            "notes": "Synthetic browser-unavailable fixture; no per-domain query ran.",
        },
    ]
    _write_csv(tm_evidence_path, TM_FIELDS, global_rows)
    assert write_trademark_summary(tm_evidence_path, domains_path, tm_summary_path) == len(labels)
    assert all(row["status"] == "unverified" for row in _read(tm_summary_path))
    assert main([
        "score", "--input", str(candidates_path), "--rdap-evidence", str(rdap_path),
        "--trademark-evidence", str(tm_summary_path), "--trademark-source-evidence", str(tm_evidence_path),
        "--out", str(scores_path),
    ]) == 0
    assert main([
        "shortlist", "--input", str(candidates_path), "--rdap-evidence", str(rdap_path),
        "--whois-evidence", str(whois_path), "--scores", str(scores_path),
        "--out", str(final_shortlist), "--excluded", str(excluded_path), "--sample-out", str(sample_path),
    ]) == 0
    assert write_valuations(final_shortlist, valuation_evidence, valuations_path) == len(_read(final_shortlist))
    assert write_opportunities(final_shortlist, scores_path, valuations_path, tm_summary_path, opportunities_path) == len(_read(final_shortlist))
    assert validate_research(
        shortlist_path=final_shortlist,
        scores_path=scores_path,
        valuation_path=valuations_path,
        valuation_evidence_path=valuation_evidence,
        trademark_evidence_path=tm_evidence_path,
        trademark_summary_path=tm_summary_path,
        opportunities_path=opportunities_path,
    ) == 2
    report = capsys.readouterr()
    assert "TMview: completed_queries=0, sourcewide_blocked_domains=0, unverified_or_missing_domains=100" in report.out
    assert "UKIPO: completed_queries=0, sourcewide_blocked_domains=100, unverified_or_missing_domains=0" in report.out
    assert "USPTO: completed_queries=0, sourcewide_blocked_domains=0, unverified_or_missing_domains=100" in report.out
    assert "BLOCKED: required trademark query coverage is unresolved" in report.err

