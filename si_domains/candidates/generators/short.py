"""Short abbreviations, familiar words and pronounceable CVCV labels."""

from __future__ import annotations

from .common import make_candidate, read_terms, unique_candidates
from ..schema import Candidate


def generate() -> list[Candidate]:
    candidates: list[Candidate] = []
    for label in read_terms("short_abbr.txt"):
        candidate = make_candidate(label, "short", "short", label, ("abbr",), seed_quality=86)
        if candidate is not None:
            candidates.append(candidate)

    for label in read_terms("short_words.txt"):
        candidate = make_candidate(label, "short", "short", label, ("word",), seed_quality=86)
        if candidate is not None:
            candidates.append(candidate)

    onsets = read_terms("short_onsets.txt")
    endings = read_terms("short_endings.txt")
    for onset in onsets:
        for ending in endings:
            if onset == ending:
                continue
            label = onset + ending
            candidate = make_candidate(
                label,
                "short",
                "short",
                f"{onset}+{ending}",
                ("cvcv",),
                seed_quality=80,
            )
            if candidate is not None:
                candidates.append(candidate)
    return unique_candidates(candidates)
