import csv
from decimal import Decimal
from pathlib import Path

import pytest

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
    assert first["trademark"] == 40
    assert "unverified (no clearance implied)" in first["rationale"]
    assert "6 letters" in first["rationale"]
    assert len(first["rationale"]) <= 140
    first["rationale"].encode("ascii")


def test_total_is_the_weighted_sum_rounded_to_one_decimal():
    result = score_domain(_candidate("novara"))

    assert result["total"] == weighted_total(
        {name: result[name] for name in SCORE_WEIGHTS}
    )


def test_weighted_total_uses_exact_decimal_half_even_rounding():
    accesshub_components = {
        "brandability": 80,
        "commercial": 86,
        "shortness": 73,
        "hack": 12,
        "resale": 64,
        "trademark": 40,
    }
    accountinghub_components = {
        "brandability": 65,
        "commercial": 86,
        "shortness": 38,
        "hack": 12,
        "resale": 50,
        "trademark": 40,
    }

    assert weighted_total(accesshub_components) == Decimal("63.6")
    assert weighted_total(accountinghub_components) == Decimal("52.4")
    assert weighted_total({**accesshub_components, "shortness": 72}) == Decimal("63.4")
    assert weighted_total({name: 60 for name in SCORE_WEIGHTS}) == Decimal("60.0")


@pytest.mark.parametrize(
    ("status", "expected"),
    [
        ("limited_screen_no_obvious_match", 85),
        ("needs legal review", 25),
        ("unverified", 40),
        ("blocked", 40),
        ("not yet screened", 40),
    ],
)
def test_trademark_state_scores_are_centralized(status, expected):
    result = score_domain(_candidate("novara"), trademark_status=status)

    assert result["trademark"] == expected


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
    keyword = score_domain(_candidate("finance", "dictionary"))
    seeded_root = score_domain(
        {**_candidate("aichat", "dictionary"), "seed": "ai+chat"}
    )

    assert keyword["commercial"] > generic["commercial"]
    assert seeded_root["commercial"] > generic["commercial"]


def test_incidental_ai_substrings_do_not_receive_keyword_demand():
    high_demand = score_domain(_candidate("pay", "dictionary"))["commercial"]
    for label in ("chair", "rain", "naivety", "naivete"):
        assert score_domain(_candidate(label, "dictionary"))["commercial"] < high_demand


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
    assert "root 'news'" in clear["rationale"]
    assert "Awkward or truncated label 'indetermina'" in obscure["rationale"]


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
            **_candidate("brena", "invented"),
            "method": "given-name-reclassified",
            "seed": "bren+a",
            "tags": "phonotactic;given_name",
        }
    )

    assert reclassified["commercial"] < common["commercial"]
    assert reclassified["resale"] < common["resale"]


def test_trademark_score_can_be_injected():
    result = score_domain(_candidate("novara"), trademark_status="needs legal review")

    assert result["trademark"] == 25
    assert "needs legal review" in result["rationale"]


def test_high_demand_root_outranks_an_unknown_of_equal_shape():
    demand = score_domain(_candidate("pay", "dictionary"))
    unknown = score_domain(_candidate("paz", "dictionary"))

    assert demand["commercial"] > unknown["commercial"]


def test_synthetic_mini_pool_has_domain_specific_score_tuples():
    roots = (
        "ai", "pay", "cloud", "data", "health", "bank", "trade", "security",
        "energy", "travel", "agent", "credit", "crypto", "news", "robot",
        "solar", "ledger", "vexa", "luma", "nara",
    )
    tails = (
        "a", "io", "ly", "er", "on", "ora", "net", "hub", "ify", "um",
        "ino", "ava", "pay", "cloud", "data", "wise", "works", "flow", "mate", "zen",
    )
    candidates = []
    for index, (root, tail) in enumerate(
        (pair for root in roots for pair in ((root, tail) for tail in tails))
    ):
        label = root + tail
        method = "compound" if index % 2 else "concept"
        seed = f"{root}+{tail}" if method == "compound" else label
        category = ("technology", "business_finance", "invented", "dictionary")[index % 4]
        candidates.append(
            {
                **_candidate(label, category),
                "method": method,
                "seed": seed,
                "quality_score": str(60 + (index * 7) % 41),
            }
        )

    vectors = {
        tuple(int(score_domain(candidate)[name]) for name in ("brandability", "commercial", "shortness", "hack", "resale"))
        for candidate in candidates
    }

    assert len(candidates) == 400
    assert len(vectors) >= 350


def test_rationales_name_specific_roots_for_same_category_neighbours():
    pay = score_domain({**_candidate("paywave"), "seed": "pay+wave", "method": "compound"})
    data = score_domain({**_candidate("dataflow"), "seed": "data+flow", "method": "compound"})

    assert pay["category"] == data["category"]
    assert pay["rationale"] != data["rationale"]
    assert "'pay'" in pay["rationale"] and "7 letters" in pay["rationale"]
    assert "'data'" in data["rationale"] and "8 letters" in data["rationale"]


def test_rationales_explain_reviewed_awkward_and_technical_labels():
    awkward = score_domain(_candidate("plian", "domain_hacks"))
    technical = score_domain(
        {**_candidate("galium", "invented"), "tags": "technical_term"}
    )

    assert "Awkward or truncated label 'plian'" in awkward["rationale"]
    assert "Niche technical term 'galium'" in technical["rationale"]


@pytest.mark.parametrize(
    "label",
    ["venal", "melena", "roguish", "fidgety", "jittery", "naivety", "raucous", "gaseous", "elitism"],
)
def test_reviewed_negative_terms_receive_strong_brandability_penalties(label):
    result = score_domain({**_candidate(label, "dictionary"), "method": "dictionary"})

    assert result["brandability"] <= 60
    assert result["commercial"] <= 30
    assert result["resale"] <= 50


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
