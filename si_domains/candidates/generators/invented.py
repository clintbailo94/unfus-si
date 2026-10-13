"""Pronounceable short brandables composed from reviewed stems and endings."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from ...config import DATA_DIR
from .common import make_candidate, read_terms, unique_candidates
from ..quality import evaluate_candidate
from ..schema import Candidate


def _read_word_terms(path: Path) -> set[str]:
    terms: set[str] = set()
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            term = line.strip().casefold()
            if term and not term.startswith("#"):
                terms.add(term)
    return terms


@lru_cache(maxsize=1)
def _known_real_words() -> frozenset[str]:
    """Combine repository vocabularies with the reviewed exact-word audit."""

    words: set[str] = set()
    for path in sorted((DATA_DIR / "seeds").glob("*.txt")):
        words.update(_read_word_terms(path))
    for path in sorted(DATA_DIR.glob("blocklist_*.txt")):
        words.update(_read_word_terms(path))
    words.update(_read_word_terms(DATA_DIR / "invented_real_words.txt"))
    return frozenset(words)


def _reclassified_candidate(
    label: str,
    seed: str,
    tags: tuple[str, ...],
) -> Candidate | None:
    real_word_tags = tuple(sorted({*tags, "real_word"}))
    score = evaluate_candidate(
        label,
        "dictionary",
        tags=real_word_tags,
        seed_quality=84,
        seed=label,
    )
    if score is None:
        return None
    return Candidate(
        label,
        "dictionary",
        "invented-reclassified",
        seed,
        real_word_tags,
        score,
    )


def generate() -> list[Candidate]:
    stems = read_terms("invented_stems.txt")
    endings = read_terms("affixes.txt")
    real_words = _known_real_words()
    candidates: list[Candidate] = []
    for stem in stems:
        for ending in endings:
            if stem.endswith(ending[:1]):
                label = stem + ending[1:]
            else:
                label = stem + ending
            seed = f"{stem}+{ending}"
            if label in real_words:
                candidate = _reclassified_candidate(label, seed, ("phonotactic",))
                if candidate is not None:
                    candidates.append(candidate)
                continue
            candidate = make_candidate(
                label,
                "invented",
                "invented",
                seed,
                ("phonotactic",),
                seed_quality=82,
            )
            if candidate is not None:
                candidates.append(candidate)
    return unique_candidates(candidates)
