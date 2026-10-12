"""Utilities shared by candidate generators."""

from __future__ import annotations

from pathlib import Path
from typing import Iterable

from ...config import DATA_DIR
from ..quality import evaluate_candidate
from ..schema import Candidate


SEED_DIR = DATA_DIR / "seeds"


def read_terms(filename: str) -> tuple[str, ...]:
    terms: list[str] = []
    with (SEED_DIR / filename).open("r", encoding="utf-8") as handle:
        for line in handle:
            term = line.strip().casefold()
            if term and not term.startswith("#"):
                terms.append(term)
    return tuple(terms)


def make_candidate(
    label: str,
    category: str,
    method: str,
    seed: str,
    tags: Iterable[str] = (),
    *,
    seed_quality: float = 80.0,
) -> Candidate | None:
    normalized_tags = tuple(sorted({tag for tag in tags if tag}))
    score = evaluate_candidate(
        label,
        category,
        tags=normalized_tags,
        seed_quality=seed_quality,
        seed=seed,
    )
    if score is None:
        return None
    return Candidate(label, category, method, seed, normalized_tags, score)


def unique_candidates(candidates: Iterable[Candidate]) -> list[Candidate]:
    by_label: dict[str, Candidate] = {}
    for candidate in candidates:
        current = by_label.get(candidate.domain_label)
        key = (candidate.quality_score, -len(candidate.seed), candidate.method, candidate.seed)
        if current is None or key > (
            current.quality_score,
            -len(current.seed),
            current.method,
            current.seed,
        ):
            by_label[candidate.domain_label] = candidate
    return [by_label[label] for label in sorted(by_label)]
