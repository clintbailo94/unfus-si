import csv
from pathlib import Path

import pytest

from si_domains.trademarks import (
    TRADEMARK_EVIDENCE_FIELDS,
    TRADEMARK_SUMMARY_FIELDS,
    normalize_seed,
    write_trademark_summary,
)
from si_domains.uspto import (
    is_similar_wordmark,
    probe_uspto_controls,
    search_uspto_label,
)


EVIDENCE_FIELDS = list(TRADEMARK_EVIDENCE_FIELDS)


def test_uspto_json_controls_and_fuzzy_screen_use_distilled_fields():
    class Response:
        status_code = 200
        headers = {"content-type": "application/json; charset=UTF-8"}

        def __init__(self, payload):
            self.payload = payload

        def json(self):
            return self.payload

    def result(label, hits):
        return {
            "hits": {
                "totalValue": len(hits),
                "hits": [{"source": hit} for hit in hits],
            }
        }

    google_hit = {
        "id": "98842355",
        "wordmark": "GOOGLE",
        "alive": True,
        "statusDescription": "REGISTERED",
        "internationalClass": ["IC 042", "IC 009"],
        "ownerName": "must not be copied",
    }
    fuzzy_hit = {
        "id": "12345678",
        "wordmark": "UNFUSE",
        "alive": True,
        "statusDescription": "LIVE",
        "internationalClass": ["IC 009", "IC 042"],
        "ownerName": "must not be copied",
    }
    whole_word_hit = {
        "id": "87654321",
        "wordmark": "AI CLOUD",
        "alive": True,
        "statusDescription": "REGISTERED",
        "internationalClass": ["IC 042"],
    }

    class Session:
        def __init__(self):
            self.calls = []

        def post(self, url, *, headers, json, timeout):
            self.calls.append((url, headers, json, timeout))
            query = json["query"]["bool"]["must"][0]
            field, value = next(iter(query.items()))
            if field == "match_phrase":
                label = value["wordmark"]
            else:
                label = value["wordmark"]["query"]
            if label == "google":
                return Response(result(label, [google_hit]))
            if label == "qzxwvk":
                return Response(result(label, []))
            if label == "unfus" and field == "match_phrase":
                return Response(result(label, []))
            if label == "unfus" and field == "match":
                return Response(result(label, [fuzzy_hit]))
            if label == "ai" and field == "match_phrase":
                return Response(result(label, []))
            if label == "ai" and field == "match":
                return Response(result(label, [whole_word_hit]))
            raise AssertionError(f"unexpected USPTO query: {json!r}")

    session = Session()
    controls = probe_uspto_controls(session)

    assert controls["google"].total == 1
    assert controls["qzxwvk"].total == 0
    assert len(session.calls) == 2

    exact, near = search_uspto_label(session, "unfus")
    assert exact.total == 0
    assert near.total == 1
    assert near.hits[0].serial_number == "12345678"
    assert near.hits[0].wordmark == "UNFUSE"
    assert near.hits[0].alive is True
    assert near.hits[0].status == "LIVE"
    assert near.hits[0].classes == ("9", "42")
    assert not hasattr(near.hits[0], "ownerName")
    assert is_similar_wordmark("unfus", "UNFUSE")
    assert is_similar_wordmark("paywave", "PAY WAVE INC")
    assert not is_similar_wordmark("unfus", "UNFURL")
    assert session.calls[2][2]["query"]["bool"]["must"][0] == {
        "match_phrase": {"wordmark": "unfus"}
    }
    assert session.calls[3][2]["query"]["bool"]["must"][0]["match"]["wordmark"]["fuzziness"] == 1

    exact_short, whole_word = search_uspto_label(session, "ai")
    assert exact_short.total == 0
    assert whole_word.mode == "whole-word"
    assert whole_word.hits[0].wordmark == "AI CLOUD"
    assert "fuzziness" not in session.calls[5][2]["query"]["bool"]["must"][0]["match"]["wordmark"]
    assert is_similar_wordmark("ai", whole_word.hits[0].wordmark)


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


def _complete_rows(label: str, *, conflict_source: str = "") -> list[dict[str, str]]:
    rows = []
    near_mode = "fuzzy-1" if len(label) >= 5 else "whole-word"
    for source in ("TMview", "UKIPO", "USPTO"):
        for query in (label, f"{label} [{near_mode}]"):
            status = "possible_conflict" if source == conflict_source and query == label else "no_obvious_match"
            rows.append(
                _evidence(
                    f"{source}-{len(rows)}", source, status,
                    domain=f"{label}.si", query=query,
                    result_url=f"{_evidence('seed', source, 'no_obvious_match')['source_url']}?query={label}",
                )
            )
    return rows


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
            _complete_rows("novara"),
            "limited_screen_no_obvious_match",
            "85",
        ),
        (
            "conflict_overrides_other_no_matches",
            _complete_rows("novara", conflict_source="TMview"),
            "needs legal review",
            "25",
        ),
        (
            "blocked_sources_do_not_clear",
            [_source_attempt("TMview", "blocked"), _source_attempt("UKIPO", "blocked"), _source_attempt("USPTO", "blocked")],
            "blocked",
            "40",
        ),
        (
            "unverified_sources_do_not_clear",
            [_source_attempt("TMview", "unverified"), _source_attempt("UKIPO", "unverified"), _source_attempt("USPTO", "unverified")],
            "unverified",
            "40",
        ),
        ("absent_evidence_does_not_clear", [], "unverified", "40"),
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


def test_summary_keeps_prior_screen_results_for_domains_that_exit_top_n(tmp_path):
    domains = tmp_path / "domains.csv"
    evidence_path = tmp_path / "trademark_evidence.csv"
    summary_path = tmp_path / "trademark_summary.csv"
    candidates_path = tmp_path / "candidates.csv"
    _write_csv(
        domains,
        ["rank", "domain"],
        [{"rank": "1", "domain": "novara.si"}, {"rank": "2", "domain": "oldname.si"}],
    )
    _write_csv(
        candidates_path,
        ["domain_label", "category", "method", "seed", "tags", "quality_score"],
        [
            {"domain_label": label, "category": "technology", "method": "concept", "seed": label, "tags": "", "quality_score": "80"}
            for label in ("novara", "oldname")
        ],
    )
    _write_csv(
        evidence_path,
        EVIDENCE_FIELDS,
        _complete_rows("oldname", conflict_source="USPTO"),
    )

    assert write_trademark_summary(
        evidence_path,
        domains,
        summary_path,
        top_n=1,
        candidates_path=candidates_path,
    ) == 2

    with summary_path.open(encoding="utf-8", newline="") as handle:
        rows = {row["domain"]: row for row in csv.DictReader(handle)}
    assert rows["oldname.si"]["status"] == "needs legal review"
    assert rows["oldname.si"]["trademark_score"] == "25"


@pytest.mark.parametrize(
    ("scenario", "expected_status", "expected_score", "query_key"),
    [
    ("exact_and_near_queries", "limited_screen_no_obvious_match", "85", "query"),
    ("missing_near_query", "unverified", "40", "query"),
        ("wrong_exact_query", "unverified", "40", "query"),
        ("newer_blocked_label", "blocked", "40", "query"),
        ("cosmetic_home_query", "unverified", "40", "synthetic-query"),
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
    near = "fuzzy-1"
    queries = {
        "wrong_exact_query": ["unrelated"],
        "missing_near_query": ["unfus"],
        "newer_blocked_label": ["unfus", f"unfus [{near}]"],
    }.get(scenario, ["unfus", f"unfus [{near}]"])
    evidence = []
    for source, source_url in source_urls.items():
        for index, query in enumerate(queries):
            status = "blocked" if scenario == "newer_blocked_label" and source == "TMview" else "no_obvious_match"
            evidence.append(
                _evidence(
                    f"{source}-{index}", source, status,
                    domain="unfus.si",
                    query=query,
                    source_url=source_url,
                    result_url="" if status == "blocked" else f"{source_url}?{query_key}={query.removesuffix(' [fuzzy-1]')}",
                    utc_timestamp="2026-10-13T12:00:00Z" if index == 0 else "2026-10-13T12:01:00Z",
                    notes="Synthetic query-coverage fixture.",
                )
            )
        if scenario == "newer_blocked_label" and source == "TMview":
            evidence.append(
                _evidence(
                    "TMview-newer-blocked", source, "blocked",
                    domain="unfus.si", query="unfus", source_url=source_url, result_url="",
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
    if scenario == "exact_and_near_queries":
        assert normalize_seed("tryto + see") == "try to see"
        assert "[2/2]" in row["coverage"]
    if scenario == "newer_blocked_label":
        assert "[0/2]" in row["coverage"]


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
    evidence = []
    for source, source_url in source_urls.items():
        for index, query in enumerate(("novara", "novara [fuzzy-1]")):
            evidence.append(
                _evidence(
                    f"{source}-{index}", source, "no_obvious_match", query=query,
                    result_url=f"{source_url}?query=novara",
                )
            )
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

