"""Build reproducible, globally unique candidate sets for the supported tiers."""

from __future__ import annotations

import csv
import hashlib
from collections import defaultdict
from pathlib import Path
from typing import Callable

from ..config import DATA_DIR
from .generators import (
    ai,
    business_finance,
    consumer_brands,
    dictionary,
    domain_hacks,
    emerging_industries,
    health_science,
    invented,
    short,
    technology,
)
from .schema import CSV_FIELDS, Candidate


CATEGORIES = (
    "domain_hacks",
    "ai",
    "short",
    "dictionary",
    "invented",
    "technology",
    "business_finance",
    "health_science",
    "consumer_brands",
    "emerging_industries",
)
MAX_CANDIDATES = {
    "domain_hacks": 850,
    "ai": 1_500,
    "short": 700,
    "dictionary": 1_050,
    "invented": 1_400,
    "technology": 1_200,
    "business_finance": 1_200,
    "health_science": 1_200,
    "consumer_brands": 1_200,
    "emerging_industries": 1_200,
}
_GENERATORS: dict[str, Callable[[], list[Candidate]]] = {
    "domain_hacks": domain_hacks.generate,
    "ai": ai.generate,
    "short": short.generate,
    "dictionary": dictionary.generate,
    "invented": invented.generate,
    "technology": technology.generate,
    "business_finance": business_finance.generate,
    "health_science": health_science.generate,
    "consumer_brands": consumer_brands.generate,
    "emerging_industries": emerging_industries.generate,
}


def _plural_rank(candidate: Candidate) -> tuple[int, int, int, str]:
    label = candidate.domain_label
    return (candidate.quality_score, -len(label), candidate.quality_score, label)


def _pluralizes(singular: str, plural: str) -> bool:
    """Recognize a few predictable English plural spellings without stemming labels."""

    if plural == singular + "s":
        return True
    if singular.endswith(("s", "x", "z", "ch", "sh")) and plural == singular + "es":
        return True
    if (
        len(singular) > 1
        and singular.endswith("y")
        and singular[-2] not in "aeiou"
        and plural == singular[:-1] + "ies"
    ):
        return True
    return False


def _plural_forms(singular: str) -> set[str]:
    forms = {singular + "s"}
    if singular.endswith(("s", "x", "z", "ch", "sh")):
        forms.add(singular + "es")
    if (
        len(singular) > 1
        and singular.endswith("y")
        and singular[-2] not in "aeiou"
    ):
        forms.add(singular[:-1] + "ies")
    return forms


def _singular_forms(plural: str) -> set[str]:
    forms: set[str] = set()
    if plural.endswith("ies"):
        forms.add(plural[:-3] + "y")
    if plural.endswith("es"):
        forms.add(plural[:-2])
    if plural.endswith("s"):
        forms.add(plural[:-1])
    return {singular for singular in forms if _pluralizes(singular, plural)}


def _compound_label_forms(candidate: Candidate, *, plural: bool) -> set[str]:
    if candidate.method != "compound" or "+" not in candidate.seed:
        return set()
    parts = candidate.seed.split("+")
    if "".join(parts) != candidate.domain_label:
        return set()

    forms: set[str] = set()
    for index, part in enumerate(parts):
        variants = _plural_forms(part) if plural else _singular_forms(part)
        for variant in variants:
            other_parts = list(parts)
            other_parts[index] = variant
            forms.add("".join(other_parts))
    return forms


def _is_trivial_plural_pair(singular: Candidate, plural: Candidate) -> bool:
    labels_match = _pluralizes(singular.domain_label, plural.domain_label)
    if not labels_match:
        labels_match = plural.domain_label in _compound_label_forms(singular, plural=True)
    if not labels_match:
        return False

    word_methods = {"dictionary", "short", "concept"}
    if singular.method in word_methods and plural.method in word_methods:
        return singular.seed == singular.domain_label and plural.seed == plural.domain_label

    compound_methods = {"compound", "blend"}
    if singular.method not in compound_methods or plural.method not in compound_methods:
        return False
    singular_parts = singular.seed.split("+")
    plural_parts = plural.seed.split("+")
    if len(singular_parts) != len(plural_parts):
        return False
    changed_parts = sum(
        old != new and _pluralizes(old, new)
        for old, new in zip(singular_parts, plural_parts)
    )
    return changed_parts == 1 and all(
        old == new or _pluralizes(old, new)
        for old, new in zip(singular_parts, plural_parts)
    )


def _remove_trivial_plurals(candidates: list[Candidate]) -> list[Candidate]:
    by_label = {candidate.domain_label: candidate for candidate in candidates}
    kept: dict[str, Candidate] = {}
    for candidate in sorted(candidates, key=_plural_rank, reverse=True):
        label = candidate.domain_label
        related_labels = _singular_forms(label) | _compound_label_forms(candidate, plural=False)
        related_labels |= _plural_forms(label) | _compound_label_forms(candidate, plural=True)
        if any(
            other_label in kept
            and (
                _is_trivial_plural_pair(by_label[other_label], candidate)
                or _is_trivial_plural_pair(candidate, by_label[other_label])
            )
            for other_label in related_labels
        ):
            continue
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
