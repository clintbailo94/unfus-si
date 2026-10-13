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
_GENERIC_TERMS = DATA_DIR / "blocklist_generic_candidate_terms.txt"


def read_terms(filename: str) -> tuple[str, ...]:
    terms: list[str] = []
    with (SEED_DIR / filename).open("r", encoding="utf-8") as handle:
        for line in handle:
            term = line.strip().casefold()
            if term and not term.startswith("#"):
                terms.append(term)
    return tuple(terms)


def read_generic_candidate_terms() -> frozenset[str]:
    """Read exact root/suffix terms that are too generic for sector joins."""

    terms: set[str] = set()
    with _GENERIC_TERMS.open("r", encoding="utf-8") as handle:
        for raw_line in handle:
            term = raw_line.strip().casefold()
            if term and not term.startswith("#"):
                terms.add(term)
    return frozenset(terms)


def _validated_vocabularies(
    roots_file: str,
    suffixes_file: str,
) -> tuple[tuple[str, ...], tuple[str, ...]]:
    roots = read_terms(roots_file)
    suffixes = read_terms(suffixes_file)
    if len(roots) != len(set(roots)) or len(suffixes) != len(set(suffixes)):
        raise ValueError("duplicate root or suffix term")
    if not roots or not suffixes or set(roots).intersection(suffixes):
        raise ValueError("root and suffix vocabularies must be non-empty and distinct")
    generic = read_generic_candidate_terms()
    if generic.intersection(roots) or generic.intersection(suffixes):
        raise ValueError("generic component in root or suffix vocabulary")
    return roots, suffixes


def read_reviewed_compounds(
    roots_file: str,
    suffixes_file: str,
    compounds_file: str,
) -> tuple[tuple[str, str], ...]:
    """Read exact, hand-reviewed ``root+suffix`` entries; never cross lists."""

    roots, suffixes = _validated_vocabularies(roots_file, suffixes_file)
    root_set, suffix_set = set(roots), set(suffixes)
    generic = read_generic_candidate_terms()
    compounds: list[tuple[str, str]] = []
    seen: set[tuple[str, str]] = set()
    with (SEED_DIR / compounds_file).open("r", encoding="utf-8") as handle:
        for raw_line in handle:
            line = raw_line.strip().casefold()
            if not line or line.startswith("#"):
                continue
            try:
                root, suffix = line.split("+", maxsplit=1)
            except ValueError as exc:
                raise ValueError(f"invalid reviewed compound in {compounds_file}: {line}") from exc
            if not root or not suffix or root not in root_set or suffix not in suffix_set:
                raise ValueError(
                    f"reviewed compound uses an unknown root or suffix in {compounds_file}: {line}"
                )
            if generic.intersection((root, suffix)):
                raise ValueError(f"generic component in reviewed compound {compounds_file}: {line}")
            if suffix in root or root in suffix:
                raise ValueError(f"reviewed compound repeats a component in {compounds_file}: {line}")
            pair = (root, suffix)
            if pair in seen:
                raise ValueError(f"duplicate reviewed compound in {compounds_file}: {line}")
            seen.add(pair)
            compounds.append(pair)
    if not compounds:
        raise ValueError(f"reviewed compound list is empty: {compounds_file}")
    return tuple(compounds)


def read_standalone_roots(roots_file: str, standalone_file: str) -> tuple[str, ...]:
    """Read the subset of roots reviewed as standalone candidate labels."""

    roots = read_terms(roots_file)
    if len(roots) != len(set(roots)) or read_generic_candidate_terms().intersection(roots):
        raise ValueError(f"invalid root vocabulary in {roots_file}")
    root_set = set(roots)
    standalone = read_terms(standalone_file)
    if not standalone or len(standalone) != len(set(standalone)) or not set(standalone) <= root_set:
        raise ValueError(
            f"standalone roots must be a unique subset of {roots_file}"
        )
    return standalone


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


def generate_root_suffix_pool(
    category: str,
    roots_file: str,
    suffixes_file: str,
    compounds_file: str,
    standalone_file: str,
    *,
    blends: Iterable[tuple[str, str]] = (),
) -> list[Candidate]:
    """Emit reviewed root+suffix compounds, reviewed roots, and selected blends."""

    pairs = read_reviewed_compounds(roots_file, suffixes_file, compounds_file)
    standalone = read_standalone_roots(roots_file, standalone_file)
    blocked_pairs = read_candidate_pair_blocks()
    candidates: list[Candidate] = []
    for root in standalone:
        candidate = make_candidate(root, category, "root", root, seed_quality=90)
        if candidate is not None:
            candidates.append(candidate)

    for root, suffix in pairs:
        seed = f"{root}+{suffix}"
        if (category, seed) in blocked_pairs:
            continue
        candidate = make_candidate(
            root + suffix,
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
