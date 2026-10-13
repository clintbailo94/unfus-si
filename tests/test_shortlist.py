import csv
from collections import Counter
from pathlib import Path

from si_domains.cli import main
from si_domains.shortlist import select_eligible


CANDIDATE_FIELDS = [
    "domain_label",
    "category",
    "method",
    "seed",
    "tags",
    "quality_score",
]
RDAP_FIELDS = [
    "domain",
    "category",
    "http_status",
    "utc_timestamp",
    "attempts",
    "classification",
    "error",
]
WHOIS_FIELDS = [
    "domain",
    "category",
    "utc_timestamp",
    "classification",
    "matched_pattern",
    "error",
]
SCORE_FIELDS = [
    "domain",
    "category",
    "brandability",
    "commercial",
    "shortness",
    "hack",
    "resale",
    "trademark",
    "total",
    "rationale",
]
SHORTLIST_FIELDS = [
    "rank",
    "domain",
    "category",
    "total",
    "brandability",
    "commercial",
    "shortness",
    "hack",
    "resale",
    "trademark",
    "rdap_timestamp",
    "whois_timestamp",
    "rationale",
]
SAMPLE_FIELDS = [
    "domain",
    "category",
    "rdap_timestamp",
    "whois_result",
    "whois_timestamp",
]
EXCLUDED_FIELDS = [
    "domain",
    "category",
    "reason",
    "rdap_classification",
    "whois_classification",
    "rdap_timestamp",
    "whois_timestamp",
]


def _write_csv(path: Path, fields: list[str], rows: list[dict[str, str]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def _candidate(label: str, category: str = "technology") -> dict[str, str]:
    return {
        "domain_label": label,
        "category": category,
        "method": "concept",
        "seed": label,
        "tags": "",
        "quality_score": "80",
    }


def _rdap(label: str, classification: str = "potentially_unregistered") -> dict[str, str]:
    return {
        "domain": f"{label}.si",
        "category": "technology",
        "http_status": "404" if classification == "potentially_unregistered" else "200",
        "utc_timestamp": "2026-10-13T01:00:00Z",
        "attempts": "1",
        "classification": classification,
        "error": "",
    }


def _whois(label: str, classification: str) -> dict[str, str]:
    return {
        "domain": f"{label}.si",
        "category": "technology",
        "utc_timestamp": "2026-10-13T02:00:00Z",
        "classification": classification,
        "matched_pattern": "no_entries_found" if classification == "not_registered" else "",
        "error": "",
    }


def _score(label: str, total: str = "80.0") -> dict[str, str]:
    return {
        "domain": f"{label}.si",
        "category": "technology",
        "brandability": "80",
        "commercial": "80",
        "shortness": "80",
        "hack": "12",
        "resale": "70",
        "trademark": "40",
        "total": total,
        "rationale": "Strengths: demand 80, brand 80; weakness: hack 12. TM not yet screened.",
    }


def _run(
    tmp_path: Path,
    candidates: list[dict[str, str]],
    rdap_rows: list[dict[str, str]],
    whois_rows: list[dict[str, str]],
    score_rows: list[dict[str, str]],
    *,
    seed: int = 20261013,
    suffix: str = "one",
) -> dict[str, Path]:
    paths = {
        "candidates": tmp_path / f"candidates-{suffix}.csv",
        "rdap": tmp_path / f"rdap-{suffix}.csv",
        "whois": tmp_path / f"whois-{suffix}.csv",
        "scores": tmp_path / f"scores-{suffix}.csv",
        "shortlist": tmp_path / f"shortlist-{suffix}.csv",
        "excluded": tmp_path / f"excluded-{suffix}.csv",
        "sample": tmp_path / f"sample-{suffix}.csv",
    }
    _write_csv(paths["candidates"], CANDIDATE_FIELDS, candidates)
    _write_csv(paths["rdap"], RDAP_FIELDS, rdap_rows)
    _write_csv(paths["whois"], WHOIS_FIELDS, whois_rows)
    _write_csv(paths["scores"], SCORE_FIELDS, score_rows)

    assert main(
        [
            "shortlist",
            "--input",
            str(paths["candidates"]),
            "--rdap-evidence",
            str(paths["rdap"]),
            "--whois-evidence",
            str(paths["whois"]),
            "--scores",
            str(paths["scores"]),
            "--out",
            str(paths["shortlist"]),
            "--excluded",
            str(paths["excluded"]),
            "--sample-out",
            str(paths["sample"]),
            "--seed",
            str(seed),
        ]
    ) == 0
    return paths


def _read_rows(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        return reader.fieldnames or [], list(reader)


def test_shortlist_applies_each_eligibility_and_exclusion_reason(tmp_path, monkeypatch):
    import si_domains.rules as rules

    monkeypatch.setitem(rules._RESERVED_NAMES, "reservedname", {"class": "reserved"})
    monkeypatch.setitem(rules._RESTRICTED_NAMES, "restrictedname", {"class": "restricted"})
    monkeypatch.setitem(rules._PREMIUM_NAMES, "premiumname", {"class": "premium"})
    labels = [
        "eligible",
        "conflict",
        "unverified",
        "unchecked",
        "rdapregistered",
        "reservedname",
        "restrictedname",
        "premiumname",
        "a",
        "rdapunverified",
    ]
    classifications = {
        "eligible": "potentially_unregistered",
        "conflict": "potentially_unregistered",
        "unverified": "potentially_unregistered",
        "unchecked": "potentially_unregistered",
        "rdapregistered": "registered",
        "reservedname": "potentially_unregistered",
        "restrictedname": "potentially_unregistered",
        "premiumname": "potentially_unregistered",
        "a": "potentially_unregistered",
        "rdapunverified": "unverified",
    }
    candidates = [_candidate(label) for label in labels]
    rdap_rows = [
        _rdap("eligible", "registered"),
        *[_rdap(label, classifications[label]) for label in labels],
    ]
    whois_rows = [
        _whois("conflict", "not_registered"),
        _whois("eligible", "not_registered"),
        _whois("conflict", "registered"),
        _whois("unverified", "unverified"),
        _whois("rdapregistered", "registered"),
        _whois("reservedname", "not_registered"),
        _whois("restrictedname", "not_registered"),
        _whois("premiumname", "not_registered"),
        _whois("a", "not_registered"),
    ]
    paths = _run(
        tmp_path,
        candidates,
        rdap_rows,
        whois_rows,
        [_score(label) for label in labels],
    )

    shortlist_header, shortlist = _read_rows(paths["shortlist"])
    excluded_header, excluded = _read_rows(paths["excluded"])
    reasons = {row["domain"]: row["reason"] for row in excluded}
    assert shortlist_header == SHORTLIST_FIELDS
    assert [row["domain"] for row in shortlist] == ["eligible.si"]
    assert excluded_header == EXCLUDED_FIELDS
    assert reasons == {
        "conflict.si": "whois_registered_conflict",
        "unverified.si": "whois_unverified",
        "unchecked.si": "whois_unchecked",
        "rdapregistered.si": "rdap_registered",
        "reservedname.si": "reserved",
        "restrictedname.si": "restricted",
        "premiumname.si": "premium",
        "a.si": "invalid",
        "rdapunverified.si": "rdap_unverified",
    }


def test_shortlist_ranks_by_score_then_label_length_then_alphabetically(tmp_path):
    labels = ["longname", "beta", "high", "able"]
    candidates = [_candidate(label) for label in labels]
    paths = _run(
        tmp_path,
        candidates,
        [_rdap(label) for label in labels],
        [_whois(label, "not_registered") for label in labels],
        [
            _score("longname", "80.0"),
            _score("beta", "80.0"),
            _score("high", "95.0"),
            _score("able", "80.0"),
        ],
    )

    _header, rows = _read_rows(paths["shortlist"])

    assert [row["domain"] for row in rows] == ["high.si", "able.si", "beta.si", "longname.si"]
    assert [row["rank"] for row in rows] == ["1", "2", "3", "4"]


def test_shortlist_caps_each_category_at_100_and_fills_to_500(tmp_path):
    groups = [
        ("a", "ai"),
        ("d", "dictionary"),
        ("i", "consumer_brands"),
        ("t", "technology"),
        ("h", "health_science"),
        ("b", "business_finance"),
        ("e", "emerging_industries"),
    ]
    candidates = []
    rdap_rows = []
    whois_rows = []
    score_rows = []
    for prefix, category in groups:
        for index in range(105):
            label = f"{prefix}{index:04d}"
            candidate = _candidate(label, category)
            candidates.append(candidate)
            rdap_rows.append(_rdap(label))
            whois_rows.append(_whois(label, "not_registered"))
            score_rows.append(_score(label, "100.0" if category == "ai" else "90.0"))

    paths = _run(tmp_path, candidates, rdap_rows, whois_rows, score_rows)
    _header, rows = _read_rows(paths["shortlist"])

    assert len(rows) == 500
    assert max(Counter(row["category"] for row in rows).values()) <= 100
    assert max(Counter(row["category"] for row in rows[:100]).values()) <= 35
    assert all(row["rank"] == str(index) for index, row in enumerate(rows, start=1))


def test_shortlist_limits_given_name_and_compound_families():
    candidates = []
    for label in (
        "brelvia", "krelvia", "mrelvia", "nrelvia", "qrelvia", "srelvia", "trelvia", "vrelvia",
    ):
        candidates.append({**_candidate(label, "invented"), "method": "given-name-reclassified", "tags": "given_name"})
    for label in (
        "lumara", "lumabi", "lumace", "lumada", "lumafo", "lumage", "lumaha", "lumaji",
    ):
        candidates.append({**_candidate(label, "invented"), "method": "given-name-reclassified", "tags": "given_name"})

    for head in ("pay", "data", "health", "cloud", "bank", "trade", "secure", "market", "credit", "robot", "solar"):
        label = f"{head}lab"
        candidates.append({**_candidate(label), "method": "compound", "seed": f"{head}+lab"})
    for tail in ("hub", "scan", "pay", "data", "ledger", "flow", "ware", "tech", "shop", "care"):
        label = f"cloud{tail}"
        candidates.append({**_candidate(label), "method": "compound", "seed": f"cloud+{tail}"})
    for head in (
        "chat", "data", "omni", "algo", "cash", "sema", "risk", "synap", "bond", "fund", "vision",
    ):
        label = f"{head}ledger"
        candidates.append({**_candidate(label), "method": "blend", "seed": f"{head}+ledger"})

    eligible = [
        (
            f"{candidate['domain_label']}.si",
            candidate,
            {**_score(candidate["domain_label"], "90.0"), "total": "90.0"},
            None,
        )
        for candidate in candidates
    ]
    selected, selection_reasons = select_eligible(eligible)
    selected_domains = {item[0] for item in selected}

    def selected_count(labels):
        return sum(f"{label}.si" in selected_domains for label in labels)

    via = [row["domain_label"] for row in candidates if row["domain_label"].endswith("via")]
    luma = [row["domain_label"] for row in candidates if row["domain_label"].startswith("luma")]
    lab_tail = [row["domain_label"] for row in candidates if row["domain_label"].endswith("lab")]
    cloud_head = [row["domain_label"] for row in candidates if row["domain_label"].startswith("cloud")]
    ledger_tail = [row["domain_label"] for row in candidates if row["domain_label"].endswith("ledger")]

    assert selected_count(via) == 6
    assert selected_count(luma) == 6
    assert selected_count(lab_tail) == 10
    assert selected_count(cloud_head) == 10
    assert selected_count(ledger_tail) == 10
    assert len([reason for reason in selection_reasons.values() if reason == "family cap"]) == 7
    assert all(reason == "family cap" for reason in selection_reasons.values())


def test_sample_404_has_seeded_deterministic_30_rows_and_status_mix(tmp_path):
    candidates = []
    rdap_rows = []
    whois_rows = []
    score_rows = []
    status_counts = {"not_registered": 20, "registered": 2, "unverified": 3, "unchecked": 20}
    counter = 0
    for status, count in status_counts.items():
        for _ in range(count):
            label = f"sample{counter:03d}"
            counter += 1
            candidates.append(_candidate(label))
            rdap_rows.append(_rdap(label))
            score_rows.append(_score(label))
            if status != "unchecked":
                whois_rows.append(_whois(label, status))

    first = _run(tmp_path, candidates, rdap_rows, whois_rows, score_rows, suffix="first")
    second = _run(tmp_path, candidates, rdap_rows, whois_rows, score_rows, suffix="second")
    header, rows = _read_rows(first["sample"])
    statuses = Counter(row["whois_result"] for row in rows)

    assert header == SAMPLE_FIELDS
    assert len(rows) == 30
    assert all(
        first[name].read_bytes() == second[name].read_bytes()
        for name in ("shortlist", "excluded", "sample")
    )
    assert {"not_registered", "registered", "unverified", "not yet checked"}.issubset(statuses)


def test_sample_404_is_limited_by_available_candidates(tmp_path):
    labels = ["availableone", "availabletwo", "availablethree"]
    paths = _run(
        tmp_path,
        [_candidate(label) for label in labels],
        [_rdap(label) for label in labels],
        [_whois(label, "not_registered") for label in labels],
        [_score(label) for label in labels],
    )

    header, rows = _read_rows(paths["sample"])

    assert header == SAMPLE_FIELDS
    assert len(rows) == 3
