"""Single-word candidates selected from the included lexeme seed list."""

from __future__ import annotations

from .common import make_candidate, read_terms, unique_candidates
from ..schema import Candidate


def generate() -> list[Candidate]:
    candidates: list[Candidate] = []
    for word in read_terms("dictionary.txt"):
        candidate = make_candidate(word, "dictionary", "dictionary", word, seed_quality=84)
        if candidate is not None:
            candidates.append(candidate)
    return unique_candidates(candidates)
