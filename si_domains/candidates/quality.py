"""Deterministic quality and safety gates shared by all generators."""

from __future__ import annotations

import re
from functools import lru_cache
from pathlib import Path
from typing import Iterable

from ..config import DATA_DIR
from ..rules import classify


_CATEGORIES = {"domain_hacks", "ai", "dictionary", "short", "invented"}
_ASCII_LABEL = re.compile(r"^[a-z]+$")
_REPEATED_LETTER = re.compile(r"([a-z])\1\1")
_REPEATED_CHUNK = re.compile(r"(.{2,3})\1")
_TOKEN = re.compile(r"[a-z0-9]+")
_VOWELS = frozenset("aeiouy")
_IDEAL_LENGTH = {
    "domain_hacks": 8,
    "ai": 9,
    "dictionary": 7,
    "short": 4,
    "invented": 7,
}


@lru_cache(maxsize=8)
def _read_terms(path: str) -> tuple[str, ...]:
    terms: list[str] = []
    with Path(path).open("r", encoding="utf-8") as handle:
        for line in handle:
            term = line.strip().casefold()
            if term and not term.startswith("#"):
                terms.append(term)
    return tuple(terms)


def _blocklist(filename: str) -> tuple[str, ...]:
    return _read_terms(str(DATA_DIR / filename))


def _is_blocked(label: str, terms: Iterable[str], *, minimum_substring: int) -> bool:
    tokens = set(_TOKEN.findall(label))
    for term in terms:
        if len(term) >= minimum_substring:
            if term in label:
                return True
        elif term in tokens:
            return True
    return False


def evaluate_candidate(
    label: object,
    category: str,
    *,
    tags: Iterable[str] = (),
    seed_quality: float = 80.0,
    seed: str | None = None,
) -> int | None:
    """Return a stable 0-100 quality score, or ``None`` when rejected.

    Candidate labels are deliberately ASCII letters only. Digits and other
    syntax accepted by the registry are excluded because they underperform as
    brand names; the short category can admit vowel-free labels only when they
    are explicitly tagged as a meaningful abbreviation.
    """

    if category not in _CATEGORIES or not isinstance(label, str):
        return None
    canonical = label.casefold()
    if canonical != label or not canonical.isascii() or not _ASCII_LABEL.fullmatch(canonical):
        return None

    lower_bound = (
        4
        if category in {"dictionary", "invented"}
        else 2
        if category in {"short", "domain_hacks"}
        else 3
    )
    upper_bound = (
        5
        if category == "short"
        else 9
        if category == "invented"
        else 16
        if category == "ai"
        else 15
    )
    if not lower_bound <= len(canonical) <= upper_bound:
        return None
    if classify(canonical) != "ok":
        return None
    if _REPEATED_LETTER.search(canonical):
        return None
    if category == "invented" and _REPEATED_CHUNK.search(canonical):
        return None
    brands = _blocklist("blocklist_brands.txt")
    offensive = _blocklist("blocklist_offensive.txt")
    source_tokens = set(_TOKEN.findall(seed.casefold())) if seed else set()
    if _is_blocked(canonical, brands, minimum_substring=5) or source_tokens.intersection(brands):
        return None
    if _is_blocked(canonical, offensive, minimum_substring=4) or source_tokens.intersection(offensive):
        return None
    low_quality = _blocklist("blocklist_low_quality.txt")
    # These are semantic exclusions for whole labels and source terms, not
    # substring fragments; substring matching would reject valid terms such
    # as "dynasty" merely because they contain "nasty".
    if canonical in low_quality or source_tokens.intersection(low_quality):
        return None

    supplied_tags = {tag.casefold() for tag in tags}
    vowel_count = sum(character in _VOWELS for character in canonical)
    if vowel_count == 0 and not (category == "short" and "abbr" in supplied_tags and len(canonical) <= 4):
        return None

    longest_cluster = max((len(run) for run in re.findall(r"[^aeiouy]+", canonical)), default=0)
    if longest_cluster > 3:
        return None

    length = len(canonical)
    length_score = max(0, 100 - abs(length - _IDEAL_LENGTH[category]) * 13)
    vowel_ratio = vowel_count / length
    vowel_score = max(0, 100 - round(abs(vowel_ratio - 0.42) * 170))
    pronunciation_score = max(0, 100 - max(0, longest_cluster - 1) * 16)
    seed_score = min(100.0, max(0.0, seed_quality))
    score = round(
        length_score * 0.30
        + vowel_score * 0.25
        + pronunciation_score * 0.25
        + seed_score * 0.20
    )
    return score if score >= 50 else None
