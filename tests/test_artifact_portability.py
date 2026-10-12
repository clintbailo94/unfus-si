"""Git checkout rules for committed deterministic review artifacts."""

from pathlib import Path
import subprocess


ROOT = Path(__file__).parents[1]


def test_generated_artifacts_are_checked_out_with_lf_endings():
    paths = (
        "data/candidates_ai.csv",
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

    assert "data/candidates_ai.csv: eol: lf" in result.stdout
    assert "data/candidates.csv: eol: lf" in result.stdout
    assert "docs/candidate_samples.md: eol: lf" in result.stdout
