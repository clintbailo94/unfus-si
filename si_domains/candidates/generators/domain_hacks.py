"""Pronunciation-safe .si completions and a small set of clear phrases."""

from __future__ import annotations

from .common import make_candidate, read_terms, unique_candidates
from ..schema import Candidate


# These -sy words have a voiced /z/ realization in a common English variety,
# so replacing the ending with the /s/ sound of .si would be unreliable.
_VOICED_SY = frozenset(
    {
        "ballsy",
        "bluesy",
        "busy",
        "cheesy",
        "choosy",
        "clumsy",
        "daisy",
        "drowsy",
        "easy",
        "greasy",
        "lousy",
        "mousy",
        "noisy",
        "nosy",
        "prosy",
        "posy",
        "pansy",
        "quinsy",
        "queasy",
        "rosy",
        "speakeasy",
        "sudsy",
        "uneasy",
        "whimsy",
        "newsy",
        "tansy",
        "teensy",
        "outdoorsy",
        "woodsy",
        "japanesy",
    }
)
_VOICED_SEE = frozenset({"franchisee", "fusee", "quasi"})


def generate() -> list[Candidate]:
    candidates: list[Candidate] = []
    for word in read_terms("domain_hacks.txt"):
        if word.endswith("cy"):
            label = word[:-2]
        elif word.endswith("sy") and word not in _VOICED_SY:
            label = word[:-2]
        elif word.endswith("see") and word not in _VOICED_SEE:
            label = word[:-3]
        elif word.endswith("si") and word not in _VOICED_SEE:
            label = word[:-2]
        else:
            continue
        candidate = make_candidate(label, "domain_hacks", "hack-suffix", word, seed_quality=84)
        if candidate is not None:
            candidates.append(candidate)

    for label in read_terms("domain_hack_phrases.txt"):
        candidate = make_candidate(label, "domain_hacks", "hack-phrase", f"{label} + see", seed_quality=86)
        if candidate is not None:
            candidates.append(candidate)
    return unique_candidates(candidates)
