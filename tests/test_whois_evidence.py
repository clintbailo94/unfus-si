import csv
from pathlib import Path

from si_domains.evidence import WHOIS_FIELDNAMES, WhoisEvidenceStore
from si_domains.whois import WhoisResult


def _result(
    domain="example.si",
    classification="not_registered",
    matched_pattern="no_entries_found",
    error="",
):
    return WhoisResult(
        domain,
        classification,
        "2026-10-13T10:00:00Z",
        matched_pattern,
        error,
    )


def test_whois_evidence_is_body_free_append_only_and_latest_row_wins(tmp_path):
    path = tmp_path / "output" / "whois_evidence.csv"
    store = WhoisEvidenceStore(path)
    store.append("tech", _result())
    store.append("tech", _result(classification="unverified", matched_pattern="", error="timeout"))

    with path.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))

    assert tuple(rows[0]) == WHOIS_FIELDNAMES
    assert len(rows) == 2
    assert store.load_latest()["example.si"]["error"] == "timeout"
    assert b"\r" not in path.read_bytes()


def test_whois_evidence_repairs_torn_row_and_accepts_crlf(tmp_path):
    path = tmp_path / "whois_evidence.csv"
    path.write_bytes(
        b"domain,category,utc_timestamp,classification,matched_pattern,error\r\n"
        b"kept.si,tech,2026-10-13T10:00:00Z,not_registered,no_entries_found,\r\n"
        b"partial.si,tech,2026-10-13T"
    )

    store = WhoisEvidenceStore(path)

    assert set(store.load_latest()) == {"kept.si"}
    assert path.read_bytes().endswith(b"\n")
    store.append("tech", _result("added.si"))
    with path.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    assert len(rows) == 2
    assert tuple(rows[-1]) == WHOIS_FIELDNAMES
    contents = path.read_bytes()
    assert b"kept.si,tech,2026-10-13T10:00:00Z,not_registered,no_entries_found,\r\n" in contents
    assert contents.endswith(b"added.si,tech,2026-10-13T10:00:00Z,not_registered,no_entries_found,\n")


def test_whois_evidence_fields_use_closed_body_free_vocabularies(tmp_path):
    path = tmp_path / "whois_evidence.csv"
    payload = "registrar: private registrant payload"
    WhoisEvidenceStore(path).append(
        "tech",
        _result(
            classification=payload,
            matched_pattern=payload,
            error=payload,
        ),
    )

    with path.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    row = rows[0]
    assert set(row) == set(WHOIS_FIELDNAMES)
    assert row["classification"] == "unverified"
    assert row["matched_pattern"] == "unspecified_pattern"
    assert row["error"] == "unspecified_error"
    assert payload not in path.read_text(encoding="utf-8")


def test_committed_whois_artifact_has_lf_body_free_rows():
    path = Path(__file__).parents[1] / "output" / "whois_evidence.csv"
    contents = path.read_bytes()

    assert b"\r" not in contents
    assert contents.endswith(b"\n")
    lines = contents.splitlines()
    header = b"domain,category,utc_timestamp,classification,matched_pattern,error"
    assert lines[0] == header
    assert lines.count(header) == 1
    with path.open(encoding="utf-8", newline="") as handle:
        parsed_rows = list(csv.reader(handle))

    assert tuple(parsed_rows[0]) == WHOIS_FIELDNAMES
    assert all(len(row) == len(WHOIS_FIELDNAMES) for row in parsed_rows)
    rows = [dict(zip(WHOIS_FIELDNAMES, row)) for row in parsed_rows[1:]]
    assert len(rows) >= 30
    assert all(row["classification"] in {"not_registered", "registered", "unverified"} for row in rows)
    assert all(
        row["matched_pattern"]
        in {
            "",
            "no_entries_found",
            "no_match",
            "no_such_domain",
            "domain_not_found",
            "domain_does_not_exist",
            "field:registrar",
            "field:created",
            "field:registered",
            "field:nserver",
            "field:nameserver",
            "field:name_server",
            "no_recognized_pattern",
            "notice:rate_limited",
            "response_cap",
            "unspecified_pattern",
        }
        for row in rows
    )
    domain_timestamps = [(row["domain"], row["utc_timestamp"]) for row in rows]
    assert len(domain_timestamps) == len(set(domain_timestamps))
    assert all(
        row["error"]
        in {
            "",
            "invalid_label",
            "timeout",
            "connection_error",
            "empty_response",
            "response_too_large",
            "rate_limited",
            "unspecified_error",
        }
        for row in rows
    )
