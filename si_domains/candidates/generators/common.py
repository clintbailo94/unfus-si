"""Utilities shared by candidate generators."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Iterable

from ...config import DATA_DIR
from ..quality import evaluate_candidate
from ..schema import Candidate


SEED_DIR = DATA_DIR / "seeds"
_PAIR_BLOCKLIST = DATA_DIR / "blocklist_candidate_pairs.txt"


def read_terms(filename: str) -> tuple[str, ...]:
    terms: list[str] = []
    with (SEED_DIR / filename).open("r", encoding="utf-8") as handle:
        for line in handle:
            term = line.strip().casefold()
            if term and not term.startswith("#"):
                terms.append(term)
    return tuple(terms)


def read_grouped_terms(filename: str) -> dict[str, tuple[str, ...]]:
    """Read reviewed vocabularies grouped by the products they can sensibly form."""

    groups: dict[str, list[str]] = {}
    current_group: str | None = None
    with (SEED_DIR / filename).open("r", encoding="utf-8") as handle:
        for raw_line in handle:
            line = raw_line.strip().casefold()
            if not line or line.startswith("#"):
                continue
            if line.startswith("[") and line.endswith("]"):
                current_group = line[1:-1].strip()
                if not current_group or current_group in groups:
                    raise ValueError(f"invalid or duplicate seed group in {filename}: {line}")
                groups[current_group] = []
            elif current_group is None:
                raise ValueError(f"seed term precedes its group in {filename}: {line}")
            else:
                groups[current_group].append(line)
    return {group: tuple(terms) for group, terms in groups.items()}


@lru_cache(maxsize=1)
def read_candidate_pair_blocks() -> frozenset[tuple[str, str]]:
    """Read exact, category-scoped root/product pairs removed after sample review."""

    blocks: set[tuple[str, str]] = set()
    with _PAIR_BLOCKLIST.open("r", encoding="utf-8") as handle:
        for raw_line in handle:
            line = raw_line.strip().casefold()
            if not line or line.startswith("#"):
                continue
            try:
                category, seed = line.split("|", maxsplit=1)
            except ValueError as exc:
                raise ValueError(f"invalid candidate pair exclusion: {line}") from exc
            if not category or "+" not in seed:
                raise ValueError(f"invalid candidate pair exclusion: {line}")
            blocks.add((category, seed))
    return frozenset(blocks)


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


def generate_curated_compounds(
    category: str,
    concepts_file: str,
    products_file: str,
    *,
    blends: Iterable[tuple[str, str]] = (),
) -> list[Candidate]:
    """Combine one reviewed sector vocabulary with its compatible product vocabulary."""

    concepts = read_grouped_terms(concepts_file)
    products = read_grouped_terms(products_file)
    if concepts.keys() != products.keys():
        raise ValueError(f"seed groups must match for {category}")
    blocked_pairs = read_candidate_pair_blocks()
    candidates: list[Candidate] = []
    for group in concepts:
        for concept in concepts[group]:
            for product in products[group]:
                if concept in product or product in concept:
                    continue
                seed = f"{concept}+{product}"
                if (category, seed) in blocked_pairs:
                    continue
                candidate = make_candidate(
                    concept + product,
                    category,
                    "compound",
                    seed,
                    seed_quality=84,
                )
                if candidate is not None:
                    candidates.append(candidate)

    for label, seed in blends:
        candidate = make_candidate(label, category, "blend", seed, seed_quality=88)
        if candidate is not None:
            candidates.append(candidate)
    return unique_candidates(candidates)
