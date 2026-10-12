import csv

from si_domains import cli
from si_domains.evidence import EvidenceStore
from si_domains.rdap import Result


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
        lambda label, session: Result("example.si", 404, "2026-10-12T12:00:00Z", 1, "potentially_unregistered"),
    )

    assert cli.main(["check", "--input", str(input_path)]) == 0
    with evidence_path.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    assert len(rows) == 1
    assert rows[0]["category"] == "tech"
    assert rows[0]["classification"] == "potentially_unregistered"
