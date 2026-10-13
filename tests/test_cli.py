import csv

from si_domains import cli
from si_domains.evidence import EvidenceStore
import si_domains.rdap as rdap
import si_domains.rules as rules
from si_domains.rdap import RegistryInaccessible, Result


def _write_candidates(path, labels):
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=["domain_label", "category"],
            lineterminator="\r\n",
        )
        writer.writeheader()
        writer.writerows({"domain_label": label, "category": "tech"} for label in labels)


def _result(label, classification="potentially_unregistered", *, status=404, error=""):
    return Result(
        f"{label}.si",
        status,
        "2026-10-12T12:00:00Z",
        1,
        classification,
        error,
    )


def test_min_interval_defaults_to_one_and_rejects_values_below_one():
    parser = cli.build_parser()

    assert parser.parse_args(["check", "--input", "candidates.csv"]).min_interval == 1.0
    assert parser.parse_args(
        ["check", "--input", "candidates.csv", "--min-interval", "2.5"]
    ).min_interval == 2.5
    try:
        parser.parse_args(["check", "--input", "candidates.csv", "--min-interval", "0.99"])
    except SystemExit as exc:
        assert exc.code == 2
    else:
        raise AssertionError("an interval below one second must be rejected")


def test_retry_unverified_only_rechecks_unverified_and_latest_result_wins(
    tmp_path, monkeypatch, capsys
):
    input_path = tmp_path / "candidates.csv"
    _write_candidates(input_path, ["verified", "limited", "unchecked"])
    evidence_path = tmp_path / "rdap_evidence.csv"
    store = EvidenceStore(evidence_path)
    store.append("tech", _result("verified"))
    store.append("tech", _result("limited", "unverified", status=429, error="http_429"))
    monkeypatch.setattr(cli, "EvidenceStore", lambda path=evidence_path: EvidenceStore(path))
    calls = []
    configured_intervals = []

    def fake_check(label, session, *, rate_limiter):
        calls.append(label)
        configured_intervals.append(rate_limiter.configured_min_interval)
        return _result(label)

    monkeypatch.setattr(cli, "check_domain", fake_check)

    assert cli.main(
        [
            "check",
            "--input",
            str(input_path),
            "--retry-unverified",
            "--min-interval",
            "2.0",
        ]
    ) == 0

    assert calls == ["limited", "unchecked"]
    assert configured_intervals == [2.0, 2.0]
    with evidence_path.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    assert len(rows) == 4
    assert rows[1]["http_status"] == "429"
    assert EvidenceStore(evidence_path).load_latest()["limited.si"]["classification"] == (
        "potentially_unregistered"
    )

    assert cli.main(
        ["status", "--input", str(input_path), "--rdap-evidence", str(evidence_path)]
    ) == 0
    status = capsys.readouterr().out
    assert "Candidates: 3" in status
    assert "Potentially unregistered: 3" in status
    assert "Unverified: 0" in status
    assert "Candidates unchecked: 0" in status


def test_cli_reads_input_resumes_and_writes_evidence(tmp_path, monkeypatch):
    input_path = tmp_path / "candidates.csv"
    with input_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["domain_label", "category"])
        writer.writeheader()
        writer.writerow({"domain_label": "example", "category": "tech"})
        writer.writerow({"domain_label": "example", "category": "duplicate"})

    evidence_path = tmp_path / "output" / "rdap_evidence.csv"
    monkeypatch.setattr(cli, "EvidenceStore", lambda: EvidenceStore(evidence_path))
    monkeypatch.setattr(
        cli,
        "check_domain",
        lambda label, session, **kwargs: Result(
            "example.si",
            404,
            "2026-10-12T12:00:00Z",
            1,
            "potentially_unregistered",
        ),
    )

    assert cli.main(["check", "--input", str(input_path)]) == 0
    with evidence_path.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    assert len(rows) == 1
    assert rows[0]["category"] == "tech"
    assert rows[0]["classification"] == "potentially_unregistered"


def test_check_time_budget_stops_between_domains(tmp_path, monkeypatch, capsys):
    input_path = tmp_path / "candidates.csv"
    _write_candidates(input_path, ["first", "second", "third"])
    evidence_path = tmp_path / "rdap_evidence.csv"
    monkeypatch.setattr(cli, "EvidenceStore", lambda: EvidenceStore(evidence_path))
    now = [0.0]
    calls = []

    def fake_check(label, session, **kwargs):
        calls.append(label)
        now[0] += 61.0
        return _result(label)

    monkeypatch.setattr(cli, "check_domain", fake_check)
    monkeypatch.setattr(cli, "MONOTONIC", lambda: now[0])

    assert cli.main(["check", "--input", str(input_path), "--max-minutes", "1"]) == 0

    assert calls == ["first"]
    assert "time budget reached" in capsys.readouterr().out.casefold()
    assert len(EvidenceStore(evidence_path).load_latest()) == 1


def test_check_time_budget_caps_cooldown_before_stopping(tmp_path, monkeypatch, capsys):
    input_path = tmp_path / "candidates.csv"
    _write_candidates(input_path, [f"name{index}" for index in range(10)])
    evidence_path = tmp_path / "rdap_evidence.csv"
    monkeypatch.setattr(cli, "EvidenceStore", lambda: EvidenceStore(evidence_path))
    breaker = rdap.CircuitBreaker()
    monkeypatch.setattr(rdap, "CIRCUIT_BREAKER", breaker)
    now = [0.0]
    sleeps = []
    calls = 0

    def fake_sleep(seconds):
        sleeps.append(seconds)
        now[0] += seconds

    def fake_check(label, session, **kwargs):
        nonlocal calls
        calls += 1
        now[0] += 10.0
        result = _result(label, "unverified", status=503, error="http_503")
        if calls == 5:
            breaker.is_open = True
            raise RegistryInaccessible("breaker opened", result=result)
        return result

    monkeypatch.setattr(cli, "check_domain", fake_check)
    monkeypatch.setattr(cli, "MONOTONIC", lambda: now[0])
    monkeypatch.setattr(cli, "SLEEP", fake_sleep)

    assert cli.main(["check", "--input", str(input_path), "--max-minutes", "1"]) == 0

    assert calls == 5
    assert sleeps == [10.0]
    assert "time budget reached" in capsys.readouterr().out.casefold()
    assert breaker.is_open is False


def test_check_cools_down_and_resumes_after_circuit_breaker_open(tmp_path, monkeypatch, capsys):
    input_path = tmp_path / "candidates.csv"
    _write_candidates(input_path, [f"name{index}" for index in range(8)])
    evidence_path = tmp_path / "rdap_evidence.csv"
    monkeypatch.setattr(cli, "EvidenceStore", lambda: EvidenceStore(evidence_path))
    breaker = rdap.CircuitBreaker()
    monkeypatch.setattr(rdap, "CIRCUIT_BREAKER", breaker)
    now = [0.0]
    sleeps = []
    calls = 0

    def fake_sleep(seconds):
        sleeps.append(seconds)
        now[0] += seconds

    def fake_check(label, session, **kwargs):
        nonlocal calls
        calls += 1
        if calls <= 5:
            result = _result(label, "unverified", status=503, error="http_503")
            if calls == 5:
                breaker.is_open = True
                raise RegistryInaccessible("breaker opened", result=result)
            return result
        return _result(label)

    monkeypatch.setattr(cli, "check_domain", fake_check)
    monkeypatch.setattr(cli, "MONOTONIC", lambda: now[0])
    monkeypatch.setattr(cli, "SLEEP", fake_sleep)

    assert cli.main(["check", "--input", str(input_path)]) == 0

    assert sleeps == [300]
    assert calls == 8
    assert breaker.is_open is False
    assert len(EvidenceStore(evidence_path).load_latest()) == 8
    assert "1 cooldown cycles" in capsys.readouterr().out


def test_check_stops_after_three_failed_cooldown_cycles_and_reports_unverified_count(
    tmp_path, monkeypatch, capsys
):
    input_path = tmp_path / "candidates.csv"
    _write_candidates(input_path, [f"name{index}" for index in range(20)])
    evidence_path = tmp_path / "rdap_evidence.csv"
    monkeypatch.setattr(cli, "EvidenceStore", lambda: EvidenceStore(evidence_path))
    breaker = rdap.CircuitBreaker()
    monkeypatch.setattr(rdap, "CIRCUIT_BREAKER", breaker)
    now = [0.0]
    sleeps = []
    calls = 0

    def fake_sleep(seconds):
        sleeps.append(seconds)
        now[0] += seconds

    def fake_check(label, session, **kwargs):
        nonlocal calls
        calls += 1
        result = _result(label, "unverified", status=503, error="http_503")
        if calls % 5 == 0:
            breaker.is_open = True
            raise RegistryInaccessible("breaker opened", result=result)
        return result

    monkeypatch.setattr(cli, "check_domain", fake_check)
    monkeypatch.setattr(cli, "MONOTONIC", lambda: now[0])
    monkeypatch.setattr(cli, "SLEEP", fake_sleep)

    assert cli.main(["check", "--input", str(input_path)]) == 2

    assert calls == 20
    assert sleeps == [300, 300, 300]
    output = capsys.readouterr().err.casefold()
    assert "registry inaccessible" in output
    assert "20 domains unverified" in output


def test_successful_result_resets_consecutive_cooldown_failures(tmp_path, monkeypatch):
    input_path = tmp_path / "candidates.csv"
    _write_candidates(input_path, [f"name{index}" for index in range(31)])
    evidence_path = tmp_path / "rdap_evidence.csv"
    monkeypatch.setattr(cli, "EvidenceStore", lambda: EvidenceStore(evidence_path))
    breaker = rdap.CircuitBreaker()
    monkeypatch.setattr(rdap, "CIRCUIT_BREAKER", breaker)
    now = [0.0]
    sleeps = []
    calls = 0
    breaker_calls = {5, 10, 16, 21, 26, 31}

    def fake_sleep(seconds):
        sleeps.append(seconds)
        now[0] += seconds

    def fake_check(label, session, **kwargs):
        nonlocal calls
        calls += 1
        if calls == 11:
            return _result(label)
        result = _result(label, "unverified", status=503, error="http_503")
        if calls in breaker_calls:
            breaker.is_open = True
            raise RegistryInaccessible("breaker opened", result=result)
        return result

    monkeypatch.setattr(cli, "check_domain", fake_check)
    monkeypatch.setattr(cli, "MONOTONIC", lambda: now[0])
    monkeypatch.setattr(cli, "SLEEP", fake_sleep)

    assert cli.main(["check", "--input", str(input_path)]) == 2

    assert calls == 31
    assert sleeps == [300, 300, 300, 300, 300]
    latest = EvidenceStore(evidence_path).load_latest()
    assert latest["name10.si"]["classification"] == "potentially_unregistered"


def test_check_resume_limit_is_counted_from_newly_checked_rows(tmp_path, monkeypatch):
    input_path = tmp_path / "candidates.csv"
    _write_candidates(input_path, [f"name{index}" for index in range(30)])
    evidence_path = tmp_path / "rdap_evidence.csv"
    monkeypatch.setattr(cli, "EvidenceStore", lambda: EvidenceStore(evidence_path))
    calls = []

    def fake_check(label, session, **kwargs):
        calls.append(label)
        return _result(label)

    monkeypatch.setattr(cli, "check_domain", fake_check)

    assert cli.main(["check", "--input", str(input_path), "--limit", "25"]) == 0
    assert cli.main(["check", "--input", str(input_path), "--limit", "25"]) == 0

    assert calls == [f"name{index}" for index in range(30)]
    assert len(EvidenceStore(evidence_path).load_latest()) == 30


def test_check_progress_reports_request_rate_and_eta(tmp_path, monkeypatch, capsys):
    input_path = tmp_path / "candidates.csv"
    _write_candidates(input_path, [f"name{index}" for index in range(51)])
    evidence_path = tmp_path / "rdap_evidence.csv"
    monkeypatch.setattr(cli, "EvidenceStore", lambda: EvidenceStore(evidence_path))
    now = [0.0]

    def fake_check(label, session, **kwargs):
        now[0] += 1.0
        return _result(label)

    monkeypatch.setattr(cli, "check_domain", fake_check)
    monkeypatch.setattr(cli, "MONOTONIC", lambda: now[0])

    assert cli.main(["check", "--input", str(input_path)]) == 0

    progress = capsys.readouterr().err
    assert "Checked 50 domains" in progress
    assert "60.0 requests/min" in progress
    assert "ETA 1 sec" in progress


def test_check_reports_request_rate_and_429_response_count(tmp_path, monkeypatch, capsys):
    input_path = tmp_path / "candidates.csv"
    _write_candidates(input_path, ["limited"])
    evidence_path = tmp_path / "rdap_evidence.csv"
    monkeypatch.setattr(cli, "EvidenceStore", lambda: EvidenceStore(evidence_path))
    now = [0.0]

    def fake_check(label, session, *, rate_limiter):
        rate_limiter.increase_after_429()
        now[0] += 30.0
        return _result(label)

    monkeypatch.setattr(cli, "check_domain", fake_check)
    monkeypatch.setattr(cli, "MONOTONIC", lambda: now[0])

    assert cli.main(["check", "--input", str(input_path), "--min-interval", "2"]) == 0

    output = capsys.readouterr().out
    assert (
        "Run totals: 1 requests; 2.0 requests/min; 1 HTTP 429 responses; "
        "0 cooldown cycles"
    ) in output


def test_stop_on_unverified_still_flushes_evidence_and_returns_error(
    tmp_path, monkeypatch, capsys
):
    input_path = tmp_path / "candidates.csv"
    _write_candidates(input_path, ["first", "second"])
    evidence_path = tmp_path / "rdap_evidence.csv"
    monkeypatch.setattr(cli, "EvidenceStore", lambda: EvidenceStore(evidence_path))
    calls = []

    def fake_check(label, session, **kwargs):
        calls.append(label)
        return _result(label, "unverified", status=403, error="http_403")

    monkeypatch.setattr(cli, "check_domain", fake_check)

    assert (
        cli.main(
            ["check", "--input", str(input_path), "--limit", "25", "--stop-on-unverified"]
        )
        == 2
    )

    assert calls == ["first"]
    assert EvidenceStore(evidence_path).load_latest()["first.si"]["error"] == "http_403"
    assert "stopped on unverified" in capsys.readouterr().err.casefold()


def test_status_reports_evidence_rules_unchecked_and_timestamp_range(
    tmp_path, monkeypatch, capsys
):
    input_path = tmp_path / "candidates.csv"
    _write_candidates(
        input_path,
        ["registered", "unregistered", "timedout", "unchecked", "x", "si", "restricted", "premium"],
    )
    evidence_path = tmp_path / "rdap_evidence.csv"
    store = EvidenceStore(evidence_path)
    store.append("tech", Result("registered.si", 200, "2026-10-10T10:00:00Z", 1, "registered"))
    store.append(
        "tech",
        Result(
            "unregistered.si",
            404,
            "2026-10-11T10:00:00Z",
            1,
            "potentially_unregistered",
        ),
    )
    store.append(
        "tech",
        Result("timedout.si", None, "2026-10-12T10:00:00Z", 5, "unverified", "network_timeout"),
    )
    monkeypatch.setitem(rules._RESTRICTED_NAMES, "restricted", {"class": "restricted"})
    monkeypatch.setitem(rules._PREMIUM_NAMES, "premium", {"class": "premium"})
    monkeypatch.setattr(cli, "EvidenceStore", lambda path=evidence_path: EvidenceStore(path))

    assert cli.main(
        ["status", "--input", str(input_path), "--rdap-evidence", str(evidence_path)]
    ) == 0

    output = capsys.readouterr().out
    assert "Registered: 1" in output
    assert "Potentially unregistered: 1" in output
    assert "Unverified network_timeout: 1" in output
    assert "Invalid: 1" in output
    assert "Reserved: 1" in output
    assert "Restricted: 1" in output
    assert "Premium: 1" in output
    assert "Candidates unchecked: 1" in output
    assert "Oldest evidence timestamp: 2026-10-10T10:00:00Z" in output
    assert "Newest evidence timestamp: 2026-10-12T10:00:00Z" in output
