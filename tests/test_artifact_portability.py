"""Git checkout rules for committed deterministic review artifacts."""

from pathlib import Path
import subprocess

from si_domains.candidates.build import CATEGORIES


ROOT = Path(__file__).parents[1]


def test_generated_artifacts_are_checked_out_with_lf_endings():
    paths = tuple(f"data/candidates_{category}.csv" for category in CATEGORIES) + (
        "data/candidates.csv",
        "docs/candidate_samples.md",
    )
    result = subprocess.run(
        ["git", "check-attr", "--all", "--", *paths],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )

    for path in paths:
        assert f"{path}: eol: lf" in result.stdout

    eol_result = subprocess.run(
        ["git", "ls-files", "--eol", "--", *paths],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    records = [line for line in eol_result.stdout.splitlines() if line]
    assert len(records) == len(paths)
    assert all("i/lf" in line and "w/lf" in line and "attr/text eol=lf" in line for line in records)
