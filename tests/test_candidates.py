from pathlib import Path

import pytest

from si_domains.candidates.quality import evaluate_candidate
from si_domains.candidates.build import CATEGORIES, generate_all


@pytest.mark.parametrize(
    "label,category,accepted",
    [
        ("novara", "invented", True),
        ("ai", "short", True),
        ("anthropic", "ai", False),
        ("myopenaiidea", "ai", False),
        ("si", "short", False),
        ("rs", "short", False),
        ("112", "short", False),
        ("naïve", "dictionary", False),
        ("two-words", "dictionary", False),
        ("aabbb", "invented", False),
        ("zzzzzz", "invented", False),
        ("123", "dictionary", False),
        ("a9", "short", False),
        ("brrr", "invented", False),
        ("monene", "invented", False),
        ("moronic", "dictionary", False),
        ("cassette", "dictionary", True),
    ],
)
def test_quality_gate_accepts_only_safe_ascii_brandable_labels(label, category, accepted):
    score = evaluate_candidate(label, category)

    assert (score is not None) is accepted
    if score is not None:
        assert 0 <= score <= 100
        assert score == evaluate_candidate(label, category)


def test_short_abbreviations_and_brand_components_are_checked():
    assert evaluate_candidate("ml", "short", tags=("abbr",)) is not None
    assert evaluate_candidate("zara", "short", tags=("cvcv",)) is None
    assert evaluate_candidate("agentgpt", "ai", seed="agent+gpt") is None


def test_generators_are_deterministic_unique_and_meet_documented_counts():
    first = generate_all()
    second = generate_all()

    assert CATEGORIES == ("domain_hacks", "ai", "short", "dictionary", "invented")
    assert first == second
    assert len({row.domain_label for rows in first.values() for row in rows}) == sum(map(len, first.values()))
    labels = {row.domain_label for rows in first.values() for row in rows}
    assert "bird" in labels
    assert "birds" not in labels
    assert "mes" in labels
    assert len(first["domain_hacks"]) >= 250
    assert len(first["ai"]) >= 1_300
    assert len(first["short"]) >= 500
    assert len(first["dictionary"]) >= 800
    assert len(first["invented"]) >= 1_200


def test_generated_candidates_pass_registry_rules_and_brand_blocks():
    from si_domains.rules import classify

    generated = generate_all()
    labels = {row.domain_label for rows in generated.values() for row in rows}

    assert all(classify(label) == "ok" for label in labels)
    assert not {"si", "rs", "112"}.intersection(labels)
    brands = [
        line.strip().casefold()
        for line in (Path(__file__).parents[1] / "data" / "blocklist_brands.txt").read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    ]

    assert not any(
        brand in label
        for brand in brands
        if len(brand) >= 5
        for label in labels
    )


def test_generated_csv_rows_have_the_required_schema():
    from si_domains.candidates.schema import CSV_FIELDS

    generated = generate_all()
    for category, rows in generated.items():
        assert all(tuple(row.to_row()) == CSV_FIELDS for row in rows)
        assert all(row.category == category for row in rows)
        assert all(row.quality_score <= 100 and row.quality_score >= 0 for row in rows)


def test_category_cli_writes_a_valid_offline_csv(tmp_path):
    import csv

    from si_domains.cli import main

    output = tmp_path / "invented.csv"
    assert main(["candidates", "--category", "invented", "--out", str(output)]) == 0
    first_bytes = output.read_bytes()
    assert main(["candidates", "--category", "invented", "--out", str(output)]) == 0
    assert output.read_bytes() == first_bytes
    with output.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        rows = list(reader)
    assert reader.fieldnames == ["domain_label", "category", "method", "seed", "tags", "quality_score"]
    assert len(rows) >= 1_200
    assert {row["category"] for row in rows} == {"invented"}


def test_sample_cli_is_reproducible_and_includes_each_category(capsys):
    from si_domains.cli import main

    assert main(["candidates", "--sample", "40", "--seed", "1"]) == 0
    first = capsys.readouterr().out
    assert main(["candidates", "--sample", "40", "--seed", "1"]) == 0
    second = capsys.readouterr().out

    assert first == second
    for category in CATEGORIES:
        assert f"## {category} (40 of " in first


def test_all_cli_can_write_one_combined_unique_csv(tmp_path):
    import csv

    from si_domains.cli import main

    output = tmp_path / "all.csv"
    assert main(["candidates", "--all", "--out", str(output)]) == 0
    with output.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        rows = list(reader)
    assert reader.fieldnames == ["domain_label", "category", "method", "seed", "tags", "quality_score"]
    assert len(rows) == len({row["domain_label"] for row in rows})
