"""Pronounceable short brandables composed from reviewed stems and endings."""

from __future__ import annotations

from .common import make_candidate, read_terms, unique_candidates
from ..schema import Candidate


def generate() -> list[Candidate]:
    stems = read_terms("invented_stems.txt")
    endings = read_terms("affixes.txt")
    candidates: list[Candidate] = []
    for stem in stems:
        for ending in endings:
            if stem.endswith(ending[:1]):
                label = stem + ending[1:]
            else:
                label = stem + ending
            candidate = make_candidate(
                label,
                "invented",
                "invented",
                f"{stem}+{ending}",
                ("phonotactic",),
                seed_quality=82,
            )
            if candidate is not None:
                candidates.append(candidate)
    return unique_candidates(candidates)
