"""Build reproducible, globally unique candidate sets for the supported tiers."""

from __future__ import annotations

import csv
import hashlib
from collections import defaultdict
from pathlib import Path
from typing import Callable

from ..config import DATA_DIR
from .generators import ai, dictionary, domain_hacks, invented, short
from .schema import CSV_FIELDS, Candidate


CATEGORIES = ("domain_hacks", "ai", "short", "dictionary", "invented")
MAX_CANDIDATES = {
    "domain_hacks": 850,
    "ai": 1_500,
    "short": 700,
    "dictionary": 1_050,
    "invented": 1_400,
}
_GENERATORS: dict[str, Callable[[], list[Candidate]]] = {
    "domain_hacks": domain_hacks.generate,
    "ai": ai.generate,
    "short": short.generate,
    "dictionary": dictionary.generate,
    "invented": invented.generate,
}


def _plural_rank(candidate: Candidate) -> tuple[int, int, int, str]:
    label = candidate.domain_label
    return (candidate.quality_score, -len(label), candidate.quality_score, label)


def _is_trivial_plural_pair(singular: Candidate, plural: Candidate) -> bool:
    if singular.category != plural.category or not plural.domain_label.endswith("s"):
        return False
    if plural.domain_label[:-1] != singular.domain_label:
        return False
    if singular.method in {"dictionary", "short"}:
        return singular.seed == singular.domain_label and plural.seed == plural.domain_label
    if singular.method in {"compound", "blend"} and plural.method == singular.method:
        singular_parts = singular.seed.split("+")
        plural_parts = plural.seed.split("+")
        if len(singular_parts) != len(plural_parts):
            return False
        return sum(
            old == new[:-1] and new.endswith("s")
            for old, new in zip(singular_parts, plural_parts)
        ) == 1 and all(
            old == new or (old == new[:-1] and new.endswith("s"))
            for old, new in zip(singular_parts, plural_parts)
        )
    return False


def _remove_trivial_plurals(candidates: list[Candidate]) -> list[Candidate]:
    by_label = {candidate.domain_label: candidate for candidate in candidates}
    kept: dict[str, Candidate] = {}
    for candidate in sorted(candidates, key=_plural_rank, reverse=True):
        label = candidate.domain_label
        if label.endswith("s") and len(label) > 3:
            singular = label[:-1]
            singular_candidate = by_label.get(singular)
            if singular_candidate is not None and _is_trivial_plural_pair(singular_candidate, candidate):
                if singular in kept or _plural_rank(singular_candidate) >= _plural_rank(candidate):
                    continue
        else:
            plural = by_label.get(label + "s")
            if plural is not None and _is_trivial_plural_pair(candidate, plural):
                if _plural_rank(plural) > _plural_rank(candidate):
                    continue
                kept.pop(label + "s", None)
        if label not in kept:
            kept[label] = candidate
    return sorted(kept.values(), key=lambda candidate: (candidate.category, candidate.domain_label))


def _rank_within_limit(category: str, candidates: list[Candidate]) -> list[Candidate]:
    limit = MAX_CANDIDATES[category]
    if len(candidates) <= limit:
        return candidates
    ranked = sorted(
        candidates,
        key=lambda candidate: (
            0 if category == "short" and {"abbr", "word"}.intersection(candidate.tags) else 1,
            -candidate.quality_score,
            hashlib.sha256(candidate.domain_label.encode("ascii")).hexdigest(),
            candidate.domain_label,
        ),
    )
    return sorted(ranked[:limit], key=lambda candidate: candidate.domain_label)


def generate_all() -> dict[str, list[Candidate]]:
    """Generate unique labels and retain applicable secondary categories as tags."""

    grouped: dict[str, list[Candidate]] = {category: [] for category in CATEGORIES}
    occurrences: dict[str, list[Candidate]] = defaultdict(list)
    for category in CATEGORIES:
        for candidate in _GENERATORS[category]():
            occurrences[candidate.domain_label].append(candidate)

    index = {category: position for position, category in enumerate(CATEGORIES)}
    combined: list[Candidate] = []
    for label in sorted(occurrences):
        options = sorted(
            occurrences[label],
            key=lambda candidate: (
                index[candidate.category],
                -candidate.quality_score,
                candidate.method,
                candidate.seed,
            ),
        )
        primary = options[0]
        tags = set(primary.tags)
        tags.update(candidate.category for candidate in options[1:])
        for other in options:
            tags.update(other.tags)
        tags.discard(primary.category)
        combined.append(
            Candidate(
                primary.domain_label,
                primary.category,
                primary.method,
                primary.seed,
                tuple(sorted(tags)),
                primary.quality_score,
            )
        )

    for candidate in _remove_trivial_plurals(combined):
        grouped[candidate.category].append(candidate)
    return {category: _rank_within_limit(category, rows) for category, rows in grouped.items()}


def generate_category(category: str) -> list[Candidate]:
    """Generate one primary category while applying global deduplication."""

    if category not in CATEGORIES:
        raise ValueError(f"unknown candidate category: {category}")
    return generate_all()[category]


def write_csv(path: str | Path, candidates: list[Candidate]) -> int:
    """Write candidates in stable label order with the agreed CSV columns."""

    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    rows = sorted(candidates, key=lambda candidate: candidate.domain_label)
    with output.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=CSV_FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(candidate.to_row() for candidate in rows)
    return len(rows)


def default_output(category: str) -> Path:
    return DATA_DIR / f"candidates_{category}.csv"
