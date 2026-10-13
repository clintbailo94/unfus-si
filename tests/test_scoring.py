import csv
from decimal import Decimal
from pathlib import Path

from si_domains.cli import main
from si_domains.scoring import SCORE_WEIGHTS, score_domain, weighted_total


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


def test_score_weights_sum_to_one():
    assert sum(SCORE_WEIGHTS.values()) == 1.0
    assert SCORE_WEIGHTS == {
        "brandability": 0.25,
        "commercial": 0.20,
        "shortness": 0.15,
        "hack": 0.15,
        "resale": 0.15,
        "trademark": 0.10,
    }


def test_score_domain_is_deterministic_bounded_and_explainable():
    row = _candidate("novara")
    first = score_domain(row)
    second = score_domain(row)

    assert first == second
    for component in SCORE_WEIGHTS:
        assert 0 <= first[component] <= 100
    assert 0 <= first["total"] <= 100
    assert first["trademark"] == 70
    assert "not yet screened" in first["rationale"]
    assert first["rationale"].startswith("Strengths: ")
    assert first["rationale"].count("weakness:") == 1
    assert len(first["rationale"]) <= 140
    first["rationale"].encode("ascii")


def test_total_is_the_weighted_sum_rounded_to_one_decimal():
    result = score_domain(_candidate("novara"))

    assert result["total"] == Decimal("72.0")


def test_weighted_total_uses_exact_decimal_half_even_rounding():
    # Captured before the heuristic rework; preserve these component fixtures.
    accesshub_components = {
        "brandability": 80,
        "commercial": 86,
        "shortness": 73,
        "hack": 12,
        "resale": 64,
        "trademark": 70,
    }
    accountinghub_components = {
        "brandability": 65,
        "commercial": 86,
        "shortness": 38,
        "hack": 12,
        "resale": 50,
        "trademark": 70,
    }

    assert weighted_total(accesshub_components) == Decimal("66.6")
    assert weighted_total(accountinghub_components) == Decimal("55.4")
    assert weighted_total({**accesshub_components, "shortness": 72}) == Decimal("66.4")
    assert weighted_total({name: 70 for name in SCORE_WEIGHTS}) == Decimal("70.0")


def test_trademark_override_recalculates_exact_weighted_total():
    baseline = score_domain(_candidate("novara"))
    overridden = score_domain(_candidate("novara"), trademark_override=22)

    assert baseline["trademark"] == 70
    assert overridden["trademark"] == 22
    assert baseline["total"] - overridden["total"] == Decimal("4.8")


def test_shorter_pronounceable_label_scores_at_least_as_high():
    short = score_domain(_candidate("mira"))
    long = score_domain(_candidate("mirabelle"))

    assert short["total"] >= long["total"]
    assert short["shortness"] > long["shortness"]


def test_domain_hack_category_gets_higher_hack_score():
    hack = score_domain(
        {
            "domain_label": "absorben",
            "category": "domain_hacks",
            "method": "hack-suffix",
            "seed": "absorbency",
            "tags": "",
            "quality_score": "91",
        }
    )
    ordinary = score_domain(_candidate("absorben", "technology"))
    unseeded = score_domain(
        {
            "domain_label": "absorben",
            "category": "domain_hacks",
            "method": "hack-suffix",
            "seed": "",
            "tags": "",
            "quality_score": "91",
        }
    )

    assert hack["hack"] > ordinary["hack"]
    assert hack["hack"] > unseeded["hack"]


def test_commercial_score_uses_secondary_tags_and_recorded_industry_roots():
    generic = score_domain(_candidate("novara", "dictionary"))
    tagged = score_domain({**_candidate("novara", "dictionary"), "tags": "health_science"})
    keyword = score_domain(_candidate("finance", "dictionary"))
    seeded_root = score_domain(
        {**_candidate("aichat", "dictionary"), "seed": "ai+chat"}
    )

    assert tagged["commercial"] > generic["commercial"]
    assert keyword["commercial"] > generic["commercial"]
    assert seeded_root["commercial"] > generic["commercial"]


def test_incidental_ai_substrings_do_not_raise_commercial_demand():
    baseline = score_domain(_candidate("novara", "dictionary"))["commercial"]

    for label in ("chair", "rain", "naivety", "naivete"):
        assert score_domain(_candidate(label, "dictionary"))["commercial"] == baseline


def test_common_dictionary_nouns_outscore_negative_and_niche_words_on_resale():
    broad_nouns = [
        score_domain({**_candidate(word, "dictionary"), "method": "dictionary"})
        for word in ("market", "travel", "bank")
    ]
    narrow_words = [
        score_domain({**_candidate(word, "dictionary"), "method": "dictionary"})
        for word in (
            "naivety",
            "naivete",
            "fidgety",
            "shadowy",
            "gaseous",
            "raucous",
            "walkout",
            "epaulet",
        )
    ]

    assert min(row["resale"] for row in broad_nouns) > max(
        row["resale"] for row in narrow_words
    )
    assert max(row["resale"] for row in narrow_words) < 85


def test_hack_source_seed_changes_buyer_breadth_but_keeps_hack_score_high():
    clear = score_domain(
        {
            **_candidate("newsagen", "domain_hacks"),
            "method": "hack-suffix",
            "seed": "newsagency",
            "quality_score": "91",
        }
    )
    obscure = score_domain(
        {
            **_candidate("indetermina", "domain_hacks"),
            "method": "hack-suffix",
            "seed": "indeterminacy",
            "quality_score": "91",
        }
    )
    conversational = score_domain(
        {
            **_candidate("tryto", "domain_hacks"),
            "method": "hack-phrase",
            "seed": "tryto + see",
            "quality_score": "81",
        }
    )
    narrow_legal = score_domain(
        {
            **_candidate("subtenan", "domain_hacks"),
            "method": "hack-suffix",
            "seed": "subtenancy",
            "quality_score": "91",
        }
    )

    assert clear["hack"] >= 75 and obscure["hack"] >= 75
    assert clear["commercial"] > obscure["commercial"]
    assert clear["resale"] > obscure["resale"]
    assert conversational["resale"] > narrow_legal["resale"]
    assert "newsagency" in clear["rationale"]
    assert "indeterminacy" in obscure["rationale"]


def test_reclassified_invented_names_do_not_receive_common_dictionary_resale_score():
    common = score_domain(
        {
            **_candidate("brena", "dictionary"),
            "method": "dictionary",
            "seed": "brena",
        }
    )
    reclassified = score_domain(
        {
            **_candidate("brena", "dictionary"),
            "method": "invented-reclassified",
            "seed": "bren+a",
            "tags": "phonotactic;real_word",
        }
    )

    assert reclassified["commercial"] < common["commercial"]
    assert reclassified["resale"] < common["resale"]


def test_trademark_score_can_be_injected():
    result = score_domain(_candidate("novara"), trademark_override=22)

    assert result["trademark"] == 22
    assert "not yet screened" not in result["rationale"]


def test_score_command_scores_only_latest_rdap_404_rows(tmp_path):
    candidates_path = tmp_path / "candidates.csv"
    rdap_path = tmp_path / "rdap.csv"
    output_path = tmp_path / "scores.csv"
    _write_csv(
        candidates_path,
        ["domain_label", "category", "method", "seed", "tags", "quality_score"],
        [_candidate("available"), _candidate("taken"), _candidate("updated")],
    )
    _write_csv(
        rdap_path,
        [
            "domain",
            "category",
            "http_status",
            "utc_timestamp",
            "attempts",
            "classification",
            "error",
        ],
        [
            {
                "domain": "available.si",
                "category": "technology",
                "http_status": "404",
                "utc_timestamp": "2026-10-13T01:00:00Z",
                "attempts": "1",
                "classification": "potentially_unregistered",
                "error": "",
            },
            {
                "domain": "taken.si",
                "category": "technology",
                "http_status": "404",
                "utc_timestamp": "2026-10-13T01:01:00Z",
                "attempts": "1",
                "classification": "registered",
                "error": "",
            },
            {
                "domain": "updated.si",
                "category": "technology",
                "http_status": "404",
                "utc_timestamp": "2026-10-13T01:02:00Z",
                "attempts": "1",
                "classification": "potentially_unregistered",
                "error": "",
            },
            {
                "domain": "updated.si",
                "category": "technology",
                "http_status": "200",
                "utc_timestamp": "2026-10-13T02:02:00Z",
                "attempts": "1",
                "classification": "registered",
                "error": "",
            },
        ],
    )

    assert main(
        [
            "score",
            "--input",
            str(candidates_path),
            "--rdap-evidence",
            str(rdap_path),
            "--out",
            str(output_path),
        ]
    ) == 0

    with output_path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        rows = list(reader)
        assert reader.fieldnames == SCORE_FIELDS
    assert [row["domain"] for row in rows] == ["available.si"]


def test_score_csv_bytes_are_deterministic(tmp_path):
    candidates_path = tmp_path / "candidates.csv"
    rdap_path = tmp_path / "rdap.csv"
    first_path = tmp_path / "first.csv"
    second_path = tmp_path / "second.csv"
    _write_csv(
        candidates_path,
        ["domain_label", "category", "method", "seed", "tags", "quality_score"],
        [_candidate("zebra"), _candidate("alpha")],
    )
    _write_csv(
        rdap_path,
        [
            "domain",
            "category",
            "http_status",
            "utc_timestamp",
            "attempts",
            "classification",
            "error",
        ],
        [
            {
                "domain": f"{label}.si",
                "category": "technology",
                "http_status": "404",
                "utc_timestamp": "2026-10-13T01:00:00Z",
                "attempts": "1",
                "classification": "potentially_unregistered",
                "error": "",
            }
            for label in ("zebra", "alpha")
        ],
    )
    args = ["score", "--input", str(candidates_path), "--rdap-evidence", str(rdap_path)]

    assert main([*args, "--out", str(first_path)]) == 0
    assert main([*args, "--out", str(second_path)]) == 0

    assert first_path.read_bytes() == second_path.read_bytes()
    assert first_path.read_bytes().endswith(b"\n")
    assert b"\r\n" not in first_path.read_bytes()
