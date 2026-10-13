import csv
from datetime import datetime, timezone

import si_domains.rdap as rdap
from si_domains.evidence import EvidenceStore, FIELDNAMES
from si_domains.rdap import Result


def make_result(classification, *, error="", status=200, attempts=1):
    return Result(
        "example.si",
        status,
        datetime(2026, 10, 12, 12, 0, 0, tzinfo=timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
        attempts,
        classification,
        error,
    )


def test_csv_appends_flushable_rows_and_latest_row_wins(tmp_path):
    path = tmp_path / "output" / "rdap_evidence.csv"
    store = EvidenceStore(path)
    store.append("tech", make_result("unverified", error="network_timeout", status=None, attempts=5))
    store.append("tech", make_result("registered"))

    with path.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    assert list(rows[0]) == list(FIELDNAMES)
    assert len(rows) == 2
    assert rows[0]["http_status"] == ""
    assert store.load_latest()["example.si"]["classification"] == "registered"
    assert b"\r" not in path.read_bytes()


def test_resume_skips_final_and_skips_unverified_until_retry_option(tmp_path):
    path = tmp_path / "evidence.csv"
    store = EvidenceStore(path)
    store.append("tech", make_result("registered"))
    assert store.should_skip("example.si")
    assert store.should_skip("example.si", retry_unverified=True)

    store.append("tech", make_result("unverified", error="network_timeout", status=None))
    assert store.should_skip("example.si")
    assert not store.should_skip("example.si", retry_unverified=True)


def test_retrying_old_429_appends_and_supersedes_it_for_status(tmp_path):
    path = tmp_path / "evidence.csv"
    store = EvidenceStore(path)
    old_429 = Result(
        "example.si",
        429,
        "2026-10-11T10:00:00Z",
        5,
        "unverified",
        "http_429",
    )
    latest_404 = Result(
        "example.si",
        404,
        "2026-10-12T10:00:00Z",
        1,
        "potentially_unregistered",
    )
    store.append("tech", old_429)

    assert not store.should_skip("example.si", retry_unverified=True)

    store.append("tech", latest_404)

    with path.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    assert len(rows) == 2
    assert rows[0]["http_status"] == "429"
    assert store.load_latest()["example.si"]["classification"] == "potentially_unregistered"
    assert store.should_skip("example.si", retry_unverified=True)


def test_invalid_syntax_is_final_and_retry_option_does_not_override(tmp_path):
    store = EvidenceStore(tmp_path / "evidence.csv")
    store.append("tech", make_result("invalid_syntax", status=None, attempts=0))
    assert store.should_skip("example.si", retry_unverified=True)


def test_response_body_never_written_to_evidence(tmp_path, monkeypatch):
    path = tmp_path / "evidence.csv"
    store = EvidenceStore(path)
    class Response:
        status_code = 404
        headers = {"Content-Type": "text/html"}
        text = "secret registrant payload"

        def json(self):
            raise AssertionError("HTML response must not be parsed")

    class Session:
        def get(self, url, **kwargs):
            return Response()

    monkeypatch.setattr(rdap, "CIRCUIT_BREAKER", rdap.CircuitBreaker())
    monkeypatch.setattr(rdap, "RATE_LIMITER", rdap.RateLimiter(clock=lambda: 0.0, sleep=lambda _: None))
    result = rdap.check_domain("example", session=Session())
    store.append("tech", result)
    contents = path.read_text(encoding="utf-8")
    assert "secret registrant payload" not in contents
    assert "unexpected_content_type" in contents


def test_error_field_rejects_unexpected_body_text(tmp_path):
    path = tmp_path / "evidence.csv"
    EvidenceStore(path).append("tech", make_result("unverified", error="secret registrant payload"))
    contents = path.read_text(encoding="utf-8")
    assert "secret registrant payload" not in contents
    assert "unspecified_error" in contents


def test_torn_final_row_is_repaired_without_losing_prior_rows_or_repeating_header(tmp_path):
    path = tmp_path / "evidence.csv"
    path.write_bytes(
        b"domain,category,http_status,utc_timestamp,attempts,classification,error\n"
        b"kept.si,tech,404,2026-10-12T10:00:00Z,1,potentially_unregistered,\n"
        b"partial.si,tech,20"
    )

    store = EvidenceStore(path)

    assert set(store.load_latest()) == {"kept.si"}
    assert path.read_bytes().endswith(b"\n")

    store.append(
        "tech",
        Result("added.si", 200, "2026-10-12T11:00:00Z", 1, "registered"),
    )

    contents = path.read_text(encoding="utf-8")
    with path.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    assert contents.count("domain,category,http_status") == 1
    assert {row["domain"] for row in rows} == {"kept.si", "added.si"}


def test_evidence_loader_accepts_crlf_csv(tmp_path):
    path = tmp_path / "evidence.csv"
    path.write_bytes(
        b"domain,category,http_status,utc_timestamp,attempts,classification,error\r\n"
        b"example.si,tech,404,2026-10-12T10:00:00Z,1,potentially_unregistered,\r\n"
    )

    latest = EvidenceStore(path).load_latest()

    assert latest["example.si"]["classification"] == "potentially_unregistered"
    assert latest["example.si"]["error"] == ""
