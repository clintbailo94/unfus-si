import csv

from si_domains import cli
from si_domains.config import DATA_DIR, EVIDENCE_PATH, WHOIS_EVIDENCE_PATH
from si_domains.evidence import EvidenceStore, WhoisEvidenceStore
from si_domains.rdap import Result
from si_domains.whois import WhoisResult


def _write_candidates(path, labels):
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=["domain_label", "category"],
            lineterminator="\r\n",
        )
        writer.writeheader()
        writer.writerows({"domain_label": label, "category": "tech"} for label in labels)


def _rdap_result(label, classification="potentially_unregistered"):
    return Result(
        f"{label}.si",
        404 if classification == "potentially_unregistered" else 200,
        "2026-10-13T09:00:00Z",
        1,
        classification,
    )


def _whois_result(label, classification="not_registered", error=""):
    pattern = "no_entries_found" if classification == "not_registered" else ""
    return WhoisResult(
        f"{label}.si",
        classification,
        "2026-10-13T10:00:00Z",
        pattern,
        error,
    )


def test_whois_check_selects_latest_rdap_404s_in_order_and_resumes(tmp_path, monkeypatch):
    input_path = tmp_path / "candidates.csv"
    _write_candidates(input_path, ["pendingb", "registered", "retryme", "pendinga"])
    rdap_path = tmp_path / "rdap_evidence.csv"
    rdap_store = EvidenceStore(rdap_path)
    rdap_store.append("tech", _rdap_result("pendingb"))
    rdap_store.append("tech", _rdap_result("registered", "registered"))
    rdap_store.append("tech", _rdap_result("retryme"))
    rdap_store.append("tech", _rdap_result("pendinga"))
    whois_path = tmp_path / "whois_evidence.csv"
    whois_store = WhoisEvidenceStore(whois_path)
    whois_store.append("tech", _whois_result("retryme", "unverified", "timeout"))

    calls = []

    def fake_check(label, **_kwargs):
        calls.append(label)
        return _whois_result(label)

    monkeypatch.setattr(cli.whois, "whois_check", fake_check)
    args = [
        "whois-check",
        "--input",
        str(input_path),
        "--rdap-evidence",
        str(rdap_path),
        "--evidence",
        str(whois_path),
    ]

    assert cli.main(args) == 0
    assert calls == ["pendingb", "pendinga"]
    assert cli.main([*args, "--retry-unverified"]) == 0
    assert calls == ["pendingb", "pendinga", "retryme"]


def test_whois_check_options_default_and_minimum_interval_validation():
    parser = cli.build_parser()
    args = parser.parse_args(["whois-check"])

    assert args.input == str(DATA_DIR / "candidates.csv")
    assert args.rdap_evidence == str(EVIDENCE_PATH)
    assert args.evidence == str(WHOIS_EVIDENCE_PATH)
    assert args.min_interval == 2.0
    try:
        parser.parse_args(["whois-check", "--min-interval", "0.99"])
    except SystemExit as exc:
        assert exc.code == 2
    else:
        raise AssertionError("a WHOIS interval below one second must be rejected")


def test_whois_pacing_and_adaptive_slowdown_after_timeout(tmp_path, monkeypatch):
    input_path = tmp_path / "candidates.csv"
    _write_candidates(input_path, ["first", "second", "third"])
    rdap_path = tmp_path / "rdap_evidence.csv"
    rdap_store = EvidenceStore(rdap_path)
    for label in ("first", "second", "third"):
        rdap_store.append("tech", _rdap_result(label))

    now = [0.0]
    sleeps = []
    starts = []

    def fake_sleep(seconds):
        sleeps.append(seconds)
        now[0] += seconds

    def fake_check(label, **_kwargs):
        starts.append(now[0])
        now[0] += 0.5
        if label == "first":
            return _whois_result(label, "unverified", "timeout")
        return _whois_result(label, "registered")

    monkeypatch.setattr(cli, "MONOTONIC", lambda: now[0])
    monkeypatch.setattr(cli, "SLEEP", fake_sleep)
    monkeypatch.setattr(cli.whois, "whois_check", fake_check)

    assert cli.main(
        [
            "whois-check",
            "--input",
            str(input_path),
            "--rdap-evidence",
            str(rdap_path),
            "--evidence",
            str(tmp_path / "whois_evidence.csv"),
            "--cooldown-seconds",
            "0",
        ]
    ) == 0

    assert starts == [0.0, 3.0, 6.0]
    assert [delay for delay in sleeps if delay > 0] == [2.5, 2.5]
    assert cli.WhoisRateLimiter(4.0).min_interval == 4.0
    limiter = cli.WhoisRateLimiter(4.0)
    limiter.increase_after_failure()
    limiter.increase_after_failure()
    assert limiter.min_interval == 6.0
    limiter.increase_after_failure()
    assert limiter.min_interval == 6.0


def test_whois_stops_after_three_failed_cooldown_cycles(tmp_path, monkeypatch, capsys):
    input_path = tmp_path / "candidates.csv"
    labels = [f"name{index}" for index in range(6)]
    _write_candidates(input_path, labels)
    rdap_path = tmp_path / "rdap_evidence.csv"
    rdap_store = EvidenceStore(rdap_path)
    for label in labels:
        rdap_store.append("tech", _rdap_result(label))

    now = [0.0]
    sleeps = []
    calls = []

    def fake_sleep(seconds):
        sleeps.append(seconds)
        now[0] += seconds

    def fake_check(label, **_kwargs):
        calls.append(label)
        return _whois_result(label, "unverified", "connection_error")

    monkeypatch.setattr(cli, "MONOTONIC", lambda: now[0])
    monkeypatch.setattr(cli, "SLEEP", fake_sleep)
    monkeypatch.setattr(cli.whois, "whois_check", fake_check)
    evidence_path = tmp_path / "whois_evidence.csv"

    assert cli.main(
        [
            "whois-check",
            "--input",
            str(input_path),
            "--rdap-evidence",
            str(rdap_path),
            "--evidence",
            str(evidence_path),
            "--cooldown-seconds",
            "1",
        ]
    ) == 2

    assert calls == labels[:4]
    assert sleeps.count(1.0) == 3
    assert len(WhoisEvidenceStore(evidence_path).load_latest()) == 4
    assert "3 consecutive cooldown cycles" in capsys.readouterr().err


def test_status_reports_whois_counts_confirmations_and_conflicts_read_only(
    tmp_path, capsys
):
    input_path = tmp_path / "candidates.csv"
    labels = ["confirmed", "conflict", "uncertain", "unchecked", "rdaponly"]
    _write_candidates(input_path, labels)
    rdap_path = tmp_path / "rdap_evidence.csv"
    rdap_store = EvidenceStore(rdap_path)
    for label in labels[:4]:
        rdap_store.append("tech", _rdap_result(label))
    rdap_store.append("tech", _rdap_result("rdaponly", "registered"))
    whois_path = tmp_path / "whois_evidence.csv"
    whois_store = WhoisEvidenceStore(whois_path)
    whois_store.append("tech", _whois_result("confirmed", "not_registered"))
    whois_store.append("tech", _whois_result("conflict", "registered"))
    whois_store.append("tech", _whois_result("uncertain", "unverified", "timeout"))
    before = (rdap_path.read_bytes(), whois_path.read_bytes())

    assert cli.main(
        [
            "status",
            "--input",
            str(input_path),
            "--rdap-evidence",
            str(rdap_path),
            "--whois-evidence",
            str(whois_path),
        ]
    ) == 0

    output = capsys.readouterr().out
    assert "WHOIS not_registered: 1" in output
    assert "WHOIS registered: 1" in output
    assert "WHOIS unverified: 1" in output
    assert "WHOIS not yet checked: 1" in output
    assert "Confirmed available (two channels): 1" in output
    assert "Conflicts (RDAP 404 but WHOIS registered): 1" in output
    assert "Pending/unverified: 2" in output
    assert before == (rdap_path.read_bytes(), whois_path.read_bytes())


class FakeSocket:
    def __init__(self, payload):
        self.payload = payload
        self.sent = b""

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def settimeout(self, _timeout):
        pass

    def sendall(self, data):
        self.sent += data

    def recv(self, size):
        if not self.payload:
            return b""
        result = self.payload[:size]
        self.payload = self.payload[size:]
        return result


def test_whois_cli_never_writes_socket_response_text(tmp_path, monkeypatch):
    input_path = tmp_path / "candidates.csv"
    _write_candidates(input_path, ["bodyfree"])
    rdap_path = tmp_path / "rdap_evidence.csv"
    EvidenceStore(rdap_path).append("tech", _rdap_result("bodyfree"))
    evidence_path = tmp_path / "whois_evidence.csv"
    connection = FakeSocket(b"Registrar: private registrant payload\r\n")
    monkeypatch.setattr(cli.whois.socket, "create_connection", lambda *a, **kw: connection)

    assert cli.main(
        [
            "whois-check",
            "--input",
            str(input_path),
            "--rdap-evidence",
            str(rdap_path),
            "--evidence",
            str(evidence_path),
        ]
    ) == 0

    with evidence_path.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    assert tuple(rows[0]) == ("domain", "category", "utc_timestamp", "classification", "matched_pattern", "error")
    assert rows[0]["classification"] == "registered"
    assert rows[0]["matched_pattern"] == "field:registrar"
    assert "private registrant payload" not in evidence_path.read_text(encoding="utf-8")


def test_whois_progress_reports_rate_and_eta_every_fifty(tmp_path, monkeypatch, capsys):
    input_path = tmp_path / "candidates.csv"
    labels = [f"domain{index}" for index in range(50)]
    _write_candidates(input_path, labels)
    rdap_path = tmp_path / "rdap_evidence.csv"
    rdap_store = EvidenceStore(rdap_path)
    for label in labels:
        rdap_store.append("tech", _rdap_result(label))

    now = [0.0]

    def fake_sleep(seconds):
        now[0] += seconds

    def fake_check(label, **_kwargs):
        now[0] += 0.5
        return _whois_result(label)

    monkeypatch.setattr(cli, "MONOTONIC", lambda: now[0])
    monkeypatch.setattr(cli, "SLEEP", fake_sleep)
    monkeypatch.setattr(cli.whois, "whois_check", fake_check)

    assert cli.main(
        [
            "whois-check",
            "--input",
            str(input_path),
            "--rdap-evidence",
            str(rdap_path),
            "--evidence",
            str(tmp_path / "whois_evidence.csv"),
        ]
    ) == 0

    progress = capsys.readouterr().err
    assert "Checked 50 domains" in progress
    assert "requests/min" in progress
    assert "ETA" in progress


def test_whois_time_budget_stops_between_requests_with_exit_zero(tmp_path, monkeypatch, capsys):
    input_path = tmp_path / "candidates.csv"
    labels = ["first", "second", "third"]
    _write_candidates(input_path, labels)
    rdap_path = tmp_path / "rdap_evidence.csv"
    rdap_store = EvidenceStore(rdap_path)
    for label in labels:
        rdap_store.append("tech", _rdap_result(label))

    now = [0.0]
    calls = []

    def fake_sleep(seconds):
        now[0] += seconds

    def fake_check(label, **_kwargs):
        calls.append(label)
        now[0] += 0.4
        return _whois_result(label)

    monkeypatch.setattr(cli, "MONOTONIC", lambda: now[0])
    monkeypatch.setattr(cli, "SLEEP", fake_sleep)
    monkeypatch.setattr(cli.whois, "whois_check", fake_check)

    assert cli.main(
        [
            "whois-check",
            "--input",
            str(input_path),
            "--rdap-evidence",
            str(rdap_path),
            "--evidence",
            str(tmp_path / "whois_evidence.csv"),
            "--max-minutes",
            "0.01",
        ]
    ) == 0

    assert calls == ["first"]
    assert "time budget reached" in capsys.readouterr().out.casefold()
