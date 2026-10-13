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


def read_curated_pairs(
    concepts_file: str,
    products_file: str,
    pairs_file: str,
) -> tuple[tuple[str, str], ...]:
    """Expand a hand-reviewed root-to-suffix whitelist and validate its sources.

    Each non-comment line in ``pairs_file`` is ``concept|suffix,suffix``. This
    compact format records exact permitted pairs and never infers compatibility
    from shared groups or a Cartesian product.
    """

    concepts = set(read_terms(concepts_file))
    products = set(read_terms(products_file))
    pairs: list[tuple[str, str]] = []
    seen: set[tuple[str, str]] = set()
    with (SEED_DIR / pairs_file).open("r", encoding="utf-8") as handle:
        for raw_line in handle:
            line = raw_line.strip().casefold()
            if not line or line.startswith("#"):
                continue
            try:
                concept, suffix_list = line.split("|", maxsplit=1)
            except ValueError as exc:
                raise ValueError(f"invalid curated pair line in {pairs_file}: {line}") from exc
            suffixes = [suffix.strip() for suffix in suffix_list.split(",")]
            if (
                not concept
                or concept not in concepts
                or not suffixes
                or any(not suffix or suffix not in products for suffix in suffixes)
            ):
                raise ValueError(f"curated pair uses an unknown concept or product in {pairs_file}: {line}")
            for suffix in suffixes:
                pair = (concept, suffix)
                if pair in seen:
                    raise ValueError(f"duplicate curated pair in {pairs_file}: {concept}+{suffix}")
                seen.add(pair)
                pairs.append(pair)
    if not pairs:
        raise ValueError(f"curated pair list is empty: {pairs_file}")
    return tuple(pairs)


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
    pairs_file: str,
    *,
    blends: Iterable[tuple[str, str]] = (),
) -> list[Candidate]:
    """Combine one reviewed sector vocabulary with its compatible product vocabulary."""

    pairs = read_curated_pairs(concepts_file, products_file, pairs_file)
    blocked_pairs = read_candidate_pair_blocks()
    candidates: list[Candidate] = []
    for concept, product in pairs:
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
