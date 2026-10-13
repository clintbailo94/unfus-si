import csv
from decimal import Decimal
from pathlib import Path

import pytest

from si_domains.cli import main
from si_domains.research import validate_research, write_opportunities
from si_domains.scoring import SCORE_FIELDS, score_domain, weighted_total
from si_domains.shortlist import SHORTLIST_FIELDS
from si_domains.trademarks import TRADEMARK_SUMMARY_FIELDS, write_trademark_summary
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


def _single_domain_research(tmp_path: Path, *, screened: bool):
    candidate = {
        "domain_label": "novara",
        "category": "technology",
        "method": "concept",
        "seed": "novara",
        "tags": "",
        "quality_score": "80",
    }
    candidates_path = tmp_path / "candidates.csv"
    _write_csv(candidates_path, CANDIDATE_FIELDS, [candidate])
    source_urls = {
        "TMview": "https://www.tmdn.org/tmview/",
        "UKIPO": "https://trademarks.ipo.gov.uk/ipo-tmtext",
        "USPTO": "https://tmsearch.uspto.gov/",
    }
    evidence_path = tmp_path / "trademark_evidence.csv"
    evidence_rows = [
        {
            "evidence_id": f"{source}-{query_index}",
            "domain": "novara.si",
            "source": source,
            "jurisdiction": "synthetic",
            "query": query,
            "utc_timestamp": "2026-10-13T12:00:00Z",
            "result_status": "no_obvious_match",
            "source_url": source_url,
            "result_url": f"{source_url}?query=novara",
            "mark_number": "",
            "mark_name": "",
            "mark_status": "",
            "classes": "",
            "notes": "Synthetic validator fixture only.",
        }
        for source, source_url in source_urls.items()
        for query_index, query in enumerate(("novara", "novara [fuzzy-1]"), start=1)
    ] if screened else []
    _write_csv(evidence_path, TM_FIELDS, evidence_rows)

    summary_path = tmp_path / "trademark_summary.csv"
    shortlist_path = tmp_path / "shortlist.csv"
    score_path = tmp_path / "scores.csv"
    valuation_evidence_path = tmp_path / "valuation_evidence.csv"
    valuation_path = tmp_path / "valuations.csv"
    opportunity_path = tmp_path / "opportunities.csv"
    if screened:
        _write_csv(
            shortlist_path,
            ["rank", "domain"],
            [{"rank": "1", "domain": "novara.si"}],
        )
        write_trademark_summary(
            evidence_path, shortlist_path, summary_path, candidates_path=candidates_path
        )
        score = score_domain(
            candidate,
            trademark_status="limited_screen_no_obvious_match",
        )
    else:
        with summary_path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=TRADEMARK_SUMMARY_FIELDS, lineterminator="\n")
            writer.writeheader()
        score = score_domain(candidate)

    score_row = {field: str(score[field]) for field in SCORE_FIELDS}
    _write_csv(score_path, list(SCORE_FIELDS), [score_row])
    shortlist_row = {
        "rank": "1",
        "domain": "novara.si",
        "category": score_row["category"],
        "total": score_row["total"],
        **{name: score_row[name] for name in ("brandability", "commercial", "shortness", "hack", "resale", "trademark")},
        "rdap_timestamp": "2026-10-13T10:00:00Z",
        "whois_timestamp": "2026-10-13T11:00:00Z",
        "rationale": score_row["rationale"],
    }
    _write_csv(shortlist_path, list(SHORTLIST_FIELDS), [shortlist_row])
    _write_csv(valuation_evidence_path, VALUATION_EVIDENCE_FIELDS, [])
    write_valuations(shortlist_path, valuation_evidence_path, valuation_path)
    write_opportunities(shortlist_path, score_path, valuation_path, summary_path, opportunity_path)
    return {
        "candidate": candidate,
        "candidates": candidates_path,
        "evidence": evidence_path,
        "summary": summary_path,
        "shortlist": shortlist_path,
        "scores": score_path,
        "valuation_evidence": valuation_evidence_path,
        "valuations": valuation_path,
        "opportunities": opportunity_path,
    }


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
    categories = ("technology", "business_finance", "consumer_brands", "emerging_industries")
    candidates = [
        {"domain_label": label, "category": categories[index % len(categories)], "method": "concept", "seed": label, "tags": "", "quality_score": "80"}
        for index, label in enumerate(labels)
    ]
    _write_csv(candidates_path, CANDIDATE_FIELDS, candidates)
    _write_csv(
        rdap_path,
        RDAP_FIELDS,
        [{"domain": f"{candidate['domain_label']}.si", "category": candidate["category"], "http_status": "404", "utc_timestamp": "2026-10-13T10:00:00Z", "attempts": "1", "classification": "potentially_unregistered", "error": ""} for candidate in candidates],
    )
    _write_csv(
        whois_path,
        WHOIS_FIELDS,
        [{"domain": f"{candidate['domain_label']}.si", "category": candidate["category"], "utc_timestamp": "2026-10-13T11:00:00Z", "classification": "not_registered", "matched_pattern": "no_entries_found", "error": ""} for candidate in candidates],
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
            for query in (label, f"{label} [fuzzy-1]"):
                conflict = label == "same000" and source == "TMview" and query == label
                tm_rows.append({
                    "evidence_id": f"{source}-{label}-{query.endswith('[fuzzy-1]')}",
                    "domain": f"{label}.si",
                    "source": source,
                    "jurisdiction": jurisdiction,
                    "query": query,
                    "utc_timestamp": "2026-10-13T12:00:00Z",
                    "result_status": "possible_conflict" if conflict else "no_obvious_match",
                    "source_url": source_urls[source],
                    "result_url": f"{source_urls[source]}?query={label}",
                    "mark_number": "SYNTH-1" if conflict else "",
                    "mark_name": "Synthetic test mark" if conflict else "",
                    "mark_status": "registered" if conflict else "",
                    "classes": "9" if conflict else "",
                    "notes": "Synthetic e2e evidence; not a real mark search.",
                })
    _write_csv(tm_evidence_path, TM_FIELDS, tm_rows)
    assert write_trademark_summary(
        tm_evidence_path, domains_path, tm_summary_path, candidates_path=candidates_path
    ) == 101

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
        and row["rationale"]
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
        candidates_path=candidates_path,
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
    assert main([
        "trademark-summary", "--shortlist", str(domains_path),
        "--candidates", str(candidates_path), "--evidence", str(tm_evidence_path),
        "--out", str(tm_summary_path), "--top-n", str(len(labels)),
    ]) == 0
    assert len(_read(tm_summary_path)) == len(labels)
    assert all(row["status"] in {"blocked", "unverified"} for row in _read(tm_summary_path))
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
    assert main([
        "validate-research", "--shortlist", str(final_shortlist),
        "--scores", str(scores_path), "--valuations", str(valuations_path),
        "--valuation-evidence", str(valuation_evidence),
        "--trademark-evidence", str(tm_evidence_path),
        "--trademark-summary", str(tm_summary_path),
        "--opportunities", str(opportunities_path),
        "--candidates", str(candidates_path), "--top-n", "100",
    ]) == 2
    report = capsys.readouterr()
    assert "TMview: completed_queries=0, sourcewide_blocked_domains=0, query_blocked_domains=0, unverified_or_missing_domains=100" in report.out
    assert "UKIPO: completed_queries=0, sourcewide_blocked_domains=100, query_blocked_domains=0, unverified_or_missing_domains=0" in report.out
    assert "USPTO: completed_queries=0, sourcewide_blocked_domains=0, query_blocked_domains=0, unverified_or_missing_domains=100" in report.out
    assert "BLOCKED: required trademark query coverage is unresolved" in report.err


@pytest.mark.parametrize(
    ("defect", "expected_diagnostic"),
    [
        ("shortlist_score_drift", "shortlist total does not match score row"),
        ("opportunity_timestamp_drift", "opportunity rdap_timestamp does not match shortlist"),
        ("opportunity_category_drift", "opportunity category does not match shortlist"),
        ("opportunity_rationale_drift", "opportunity rationale does not match shortlist"),
        ("summary_score_not_injected", "does not match limited_screen_no_obvious_match evidence (85)"),
        ("unscreened_provenance_fabricated", "unscreened opportunity has fabricated trademark provenance"),
    ],
)
def test_validator_rejects_research_join_drift(tmp_path, capsys, defect, expected_diagnostic):
    screened = defect != "unscreened_provenance_fabricated"
    artifacts = _single_domain_research(tmp_path, screened=screened)

    if screened:
        assert validate_research(
            shortlist_path=artifacts["shortlist"],
            scores_path=artifacts["scores"],
            valuation_path=artifacts["valuations"],
            valuation_evidence_path=artifacts["valuation_evidence"],
            trademark_evidence_path=artifacts["evidence"],
            trademark_summary_path=artifacts["summary"],
            opportunities_path=artifacts["opportunities"],
            candidates_path=artifacts["candidates"],
            top_n=1,
        ) == 0
        capsys.readouterr()

    shortlist = _read(artifacts["shortlist"])
    opportunities = _read(artifacts["opportunities"])
    if defect == "shortlist_score_drift":
        shortlist[0]["total"] = "1.0"
        _write_csv(artifacts["shortlist"], list(SHORTLIST_FIELDS), shortlist)
    elif defect == "opportunity_timestamp_drift":
        opportunities[0]["rdap_timestamp"] = "2000-01-01T00:00:00Z"
        _write_csv(artifacts["opportunities"], list(opportunities[0]), opportunities)
    elif defect == "opportunity_category_drift":
        opportunities[0]["category"] = "invented"
        _write_csv(artifacts["opportunities"], list(opportunities[0]), opportunities)
    elif defect == "opportunity_rationale_drift":
        opportunities[0]["rationale"] = "fabricated copied rationale"
        _write_csv(artifacts["opportunities"], list(opportunities[0]), opportunities)
    elif defect == "summary_score_not_injected":
        baseline = score_domain(artifacts["candidate"])
        scores = _read(artifacts["scores"])
        scores[0] = {field: str(baseline[field]) for field in SCORE_FIELDS}
        _write_csv(artifacts["scores"], list(SCORE_FIELDS), scores)
        shortlist[0].update({field: str(baseline[field]) for field in SCORE_FIELDS if field != "domain"})
        _write_csv(artifacts["shortlist"], list(SHORTLIST_FIELDS), shortlist)
        write_opportunities(
            artifacts["shortlist"], artifacts["scores"], artifacts["valuations"],
            artifacts["summary"], artifacts["opportunities"],
        )
    else:
        opportunities[0]["trademark_coverage"] = "TMview:no_obvious_match"
        opportunities[0]["trademark_evidence_ids"] = "FABRICATED-1"
        _write_csv(artifacts["opportunities"], list(opportunities[0]), opportunities)

    result = validate_research(
        shortlist_path=artifacts["shortlist"],
        scores_path=artifacts["scores"],
        valuation_path=artifacts["valuations"],
        valuation_evidence_path=artifacts["valuation_evidence"],
        trademark_evidence_path=artifacts["evidence"],
        trademark_summary_path=artifacts["summary"],
        opportunities_path=artifacts["opportunities"],
        candidates_path=artifacts["candidates"],
        top_n=1,
    )
    report = capsys.readouterr()
    assert result == 2
    assert expected_diagnostic in report.err


@pytest.mark.parametrize(
    ("scope", "expected_exit", "expected_status", "expected_score"),
    [
        ("per_query", 2, "blocked", "40"),
        ("sourcewide", 2, "blocked", "40"),
        ("mixed", 2, "blocked", "40"),
        ("mixed_unverified", 2, "unverified", "40"),
        ("mixed_unproven", 2, "unverified", "40"),
    ],
)
def test_query_specific_refusals_remain_unresolved_with_sourcewide_context(
    tmp_path, capsys, scope, expected_exit, expected_status, expected_score
):
    artifacts = _single_domain_research(tmp_path, screened=True)
    evidence = _read(artifacts["evidence"])
    if scope == "sourcewide":
        evidence = [row for row in evidence if row["source"] != "TMview"]
        evidence.append({
            "evidence_id": "TMV-SOURCE-ACCESS", "domain": "*", "source": "TMview",
            "jurisdiction": "EU/participating offices", "query": "source access check",
            "utc_timestamp": "2026-10-13T12:00:00Z", "result_status": "blocked",
            "source_url": "https://www.tmdn.org/tmview/", "result_url": "",
            "mark_number": "", "mark_name": "", "mark_status": "", "classes": "",
            "notes": "Synthetic source-wide refusal; no per-domain query ran.",
        })
    else:
        evidence[0].update(
            result_status="blocked",
            result_url="",
            notes="Synthetic query-specific refusal; no real search was performed.",
        )
    if scope in {"mixed", "mixed_unverified", "mixed_unproven"}:
        evidence.append({
            **evidence[0], "evidence_id": "TMV-SOURCE-ACCESS", "domain": "*",
            "query": "source access check",
            "notes": "Synthetic source-wide refusal; no per-domain query ran.",
        })
        if scope == "mixed_unverified":
            evidence[0].update(
                result_status="unverified",
                notes="Synthetic explicit per-query unknown; not source-wide.",
            )
        elif scope == "mixed_unproven":
            evidence[0].update(
                result_status="no_obvious_match",
                result_url=f"{evidence[0]['source_url']}?tracking=novara",
                notes="Synthetic claimed query with unusable proof.",
            )

    _write_csv(artifacts["evidence"], TM_FIELDS, evidence)
    write_trademark_summary(
        artifacts["evidence"],
        artifacts["shortlist"],
        artifacts["summary"],
        candidates_path=artifacts["candidates"],
    )
    summary = _read(artifacts["summary"])[0]
    assert summary["status"] == expected_status
    assert summary["trademark_score"] == expected_score

    score = score_domain(
        artifacts["candidate"],
        trademark_override=int(summary["trademark_score"]),
        trademark_status=summary["status"],
    )
    _write_csv(artifacts["scores"], list(SCORE_FIELDS), [{field: str(score[field]) for field in SCORE_FIELDS}])
    shortlist = _read(artifacts["shortlist"])
    shortlist[0].update({field: str(score[field]) for field in SCORE_FIELDS if field != "domain"})
    _write_csv(artifacts["shortlist"], list(SHORTLIST_FIELDS), shortlist)
    write_opportunities(artifacts["shortlist"], artifacts["scores"], artifacts["valuations"], artifacts["summary"], artifacts["opportunities"])

    result = validate_research(**{
        "shortlist_path": artifacts["shortlist"], "scores_path": artifacts["scores"],
        "valuation_path": artifacts["valuations"], "valuation_evidence_path": artifacts["valuation_evidence"],
        "trademark_evidence_path": artifacts["evidence"], "trademark_summary_path": artifacts["summary"],
        "opportunities_path": artifacts["opportunities"], "candidates_path": artifacts["candidates"], "top_n": 1,
    })
    report = capsys.readouterr()
    assert result == expected_exit
    sourcewide_count = int(scope == "sourcewide")
    query_blocked_count = int(scope in {"per_query", "mixed"})
    unverified_count = int(scope in {"mixed_unverified", "mixed_unproven"})
    if scope == "sourcewide":
        assert "Blocked sources: TMview; no per-domain query ran there." in summary["limitations"]
    elif scope in {"per_query", "mixed"}:
        assert "Required per-domain queries blocked: TMview." in summary["limitations"]
    if scope in {"mixed", "mixed_unverified", "mixed_unproven"}:
        assert "Source-wide refusal also prevented missing required queries" not in summary["limitations"]
        assert "no per-domain query ran there" not in summary["limitations"]
    if scope in {"mixed_unverified", "mixed_unproven"}:
        assert "Unverified sources: TMview; no no-match conclusion." in summary["limitations"]
        assert "Blocked sources: TMview; no per-domain query ran there." not in summary["limitations"]
    assert (
        f"TMview: completed_queries=0, sourcewide_blocked_domains={sourcewide_count}, "
        f"query_blocked_domains={query_blocked_count}, unverified_or_missing_domains={unverified_count}"
    ) in report.out
    if expected_exit == 2:
        assert "BLOCKED: required trademark query coverage is unresolved" in report.err
    else:
        assert "Research validation PASS" in report.out

