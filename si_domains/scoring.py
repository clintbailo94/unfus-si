"""Deterministic, explainable heuristic scores for RDAP-404 candidates."""

from __future__ import annotations

import csv
import re
from functools import lru_cache
from decimal import Decimal, ROUND_HALF_EVEN
from pathlib import Path
from typing import Mapping

from .config import DATA_DIR


SCORE_WEIGHTS = {
    "brandability": 0.25,
    "commercial": 0.20,
    "shortness": 0.15,
    "hack": 0.15,
    "resale": 0.15,
    "trademark": 0.10,
}
SCORE_FIELDS = (
    "domain",
    "category",
    "brandability",
    "commercial",
    "shortness",
    "hack",
    "resale",
    "trademark",
    "total",
    "rationale",
)

TRADEMARK_CLEAR_SCORE = 85
TRADEMARK_CONFLICT_SCORE = 25
TRADEMARK_UNVERIFIED_SCORE = 40
TRADEMARK_SCORE_BY_STATUS = {
    "limited_screen_no_obvious_match": TRADEMARK_CLEAR_SCORE,
    "needs legal review": TRADEMARK_CONFLICT_SCORE,
    "blocked": TRADEMARK_UNVERIFIED_SCORE,
    "unverified": TRADEMARK_UNVERIFIED_SCORE,
    "not yet screened": TRADEMARK_UNVERIFIED_SCORE,
}

# Each root has (tier, demand score, buyer-pool breadth, buyer summary). The
# values are relative ranking inputs, not traffic, sales, or valuation data.
COMMERCIAL_ROOTS: dict[str, tuple[int, int, int, str]] = {
    "ai": (1, 96, 24, "software and automation"),
    "pay": (1, 94, 20, "fintech and payments"),
    "cloud": (1, 92, 22, "software and hosting"),
    "data": (1, 92, 25, "cross-industry analytics"),
    "health": (1, 90, 18, "health technology"),
    "bank": (1, 89, 18, "finance"),
    "finance": (1, 89, 17, "financial services"),
    "trade": (1, 87, 20, "commerce and trade"),
    "invest": (1, 86, 17, "investment"),
    "security": (1, 86, 18, "security and IT"),
    "insurance": (1, 85, 15, "insurance"),
    "software": (1, 85, 16, "software"),
    "wallet": (1, 85, 14, "payments"),
    "energy": (1, 84, 18, "energy"),
    "market": (1, 84, 21, "commerce"),
    "travel": (1, 82, 20, "travel"),
    "agent": (2, 78, 16, "automation and services"),
    "auto": (2, 78, 16, "automotive"),
    "business": (2, 77, 16, "business services"),
    "care": (2, 77, 14, "care services"),
    "credit": (2, 79, 15, "finance"),
    "crypto": (2, 78, 13, "digital finance"),
    "education": (2, 76, 16, "education"),
    "fintech": (2, 82, 16, "financial technology"),
    "med": (2, 74, 12, "medical services"),
    "news": (2, 76, 17, "media"),
    "robot": (2, 77, 14, "robotics"),
    "science": (2, 75, 14, "science"),
    "tech": (2, 77, 17, "technology"),
    "hotel": (2, 73, 13, "hospitality"),
    "office": (2, 72, 13, "workplace services"),
    "bio": (3, 66, 11, "biotechnology"),
    "legal": (3, 66, 11, "legal services"),
    "law": (3, 64, 10, "legal services"),
    "food": (3, 68, 15, "food and retail"),
    "game": (3, 67, 13, "games and entertainment"),
    "shop": (3, 66, 14, "retail"),
    "sport": (3, 65, 13, "sports"),
    "solar": (3, 68, 12, "solar energy"),
    "carbon": (3, 64, 11, "climate technology"),
    "ledger": (3, 68, 12, "accounting and finance"),
    "medical": (3, 68, 12, "medical services"),
    "pharma": (3, 67, 10, "pharmaceuticals"),
    "genome": (3, 64, 10, "genomics"),
    "ticket": (3, 65, 13, "events and travel"),
    "web": (3, 67, 18, "internet services"),
    "mobile": (3, 68, 15, "mobile technology"),
}
_UNKNOWN_ROOT_DEMAND = 48
_UNKNOWN_ROOT_BREADTH = 4
_NEGATIVE_PENALTY = 50
_AWKWARD_LABELS = frozenset(
    {
        "absorben",
        "astringen",
        "ferven",
        "floun",
        "indetermina",
        "interagen",
        "intermitten",
        "pedslab",
        "piquan",
        "plian",
        "pungen",
        "stringen",
        "subtenan",
    }
)
_BROAD_BUYER_NOUNS = frozenset(
    {
        "bank",
        "cloud",
        "credit",
        "energy",
        "food",
        "home",
        "hotel",
        "market",
        "office",
        "security",
        "service",
        "travel",
        "wallet",
        "water",
    }
)
# Curated low-breadth dictionary entries: negative traits, adjectives, niche
# terms, and narrow activities do not get a generic dictionary resale premium.
_LOW_BREADTH_DICTIONARY_WORDS = frozenset(
    {
        "askance",
        "belated",
        "cowhide",
        "decorous",
        "epaulet",
        "elitism",
        "fidgety",
        "gaseous",
        "jittery",
        "jugular",
        "leaning",
        "naivete",
        "naivety",
        "orifice",
        "powdery",
        "raucous",
        "roguish",
        "shadowy",
        "stoical",
        "tenuous",
        "walkout",
        "wizened",
    }
)
# Per-seed adjustments separate phonetic hack quality from likely buyer breadth.
# Tuple order is brandability, commercial demand, and resale potential. The
# seed names and adjustments are reviewed lexical notes, not sale-price claims.
_HACK_SEED_ADJUSTMENTS = {
    "flouncy": (-16, 0, -24),     # playful adjective with an awkward short stem
    "pliancy": (-16, -5, -24),    # obscure abstract trait and awkward stem
    "unfussy": (0, 2, 6),         # familiar positive consumer adjective
    "piquancy": (-16, -2, -22),   # niche abstract/culinary sense
    "tryto + see": (0, 2, 7),     # clear conversational phrase
    "fervency": (-14, -2, -24),   # abstract intensity and awkward stem
    "pungency": (-14, -2, -24),   # narrow sensory property
    "absorbency": (-12, 0, -22),  # material/product attribute
    "subtenancy": (-14, -10, -28), # narrow real-estate/legal term
    "newsagency": (0, 12, 8),     # recognizable media-service term
    "shallwe + see": (0, 2, 7),   # clear conversational phrase
    "interagency": (-14, -8, -25), # institutional use
    "stringency": (-14, -2, -25), # standards/technical term
    "astringency": (-14, -3, -25), # narrow sensory property
    "indeterminacy": (-16, -8, -26), # technical abstraction
    "intermittency": (-14, 3, -18), # technical reliability term
}
_AMBIGUOUS_PAIRS = ("cl", "rn", "vv", "ii", "0o", "1l")
_VOWELS = frozenset("aeiouy")
_COMMON_ONSETS = frozenset(
    {"br", "bl", "ch", "cl", "cr", "dr", "fl", "fr", "gl", "gr", "pl", "pr", "sc", "sh", "sk", "sl", "sm", "sn", "sp", "st", "sw", "th", "tr", "wh"}
)
_COMMON_ENDINGS = (
    "able", "ate", "er", "ify", "ing", "ion", "ive", "ly", "ment", "ness", "on", "or", "y"
)
_COMMON_VOWEL_PAIRS = frozenset({"ai", "ea", "ee", "ie", "io", "oa", "oo", "ou", "ue", "ui"})
_CLEAR_CONSONANT_PAIRS = frozenset(
    {"bl", "br", "ch", "ck", "cl", "cr", "dr", "fl", "fr", "gl", "gr", "ld", "lk", "ll", "lt", "mp", "nd", "ng", "nk", "nt", "pl", "pr", "rk", "rl", "rm", "rn", "rs", "rt", "sc", "sh", "sk", "sl", "sm", "sn", "sp", "st", "sw", "th", "tr", "ts", "wh"}
)
_ONSET_CLARITY = {"b": 2, "c": 1, "d": 2, "f": 2, "g": 1, "h": 0, "j": -1, "k": 1, "l": 2, "m": 2, "n": 2, "p": 2, "q": -4, "r": 3, "s": 2, "t": 2, "v": 0, "w": 0, "x": -4, "y": 0, "z": -1}
_ENDING_CLARITY = {"a": 1, "e": 2, "i": 1, "o": 1, "u": 0, "y": 0, "l": 2, "n": 3, "r": 3, "s": 2, "t": 1, "k": 0, "x": -3, "z": -2, "q": -4}
_LETTER_CLARITY = {
    "a": 8, "b": 7, "c": 6, "d": 7, "e": 8, "f": 8, "g": 6,
    "h": 5, "i": 7, "j": 4, "k": 7, "l": 8, "m": 8, "n": 9,
    "o": 8, "p": 7, "q": 2, "r": 9, "s": 8, "t": 8, "u": 6,
    "v": 6, "w": 5, "x": 3, "y": 5, "z": 4,
}


@lru_cache(maxsize=1)
def _negative_connotations() -> frozenset[str]:
    terms: set[str] = set()
    with (DATA_DIR / "scoring_penalties.txt").open("r", encoding="utf-8") as handle:
        for line in handle:
            term = line.strip().casefold()
            if term and not term.startswith("#"):
                terms.add(term)
    return frozenset(terms)


def trademark_score_for_status(status: str) -> int:
    """Return the documented, conservative trademark component for a state."""

    try:
        return TRADEMARK_SCORE_BY_STATUS[status]
    except KeyError as exc:
        raise ValueError(f"unknown trademark screening status: {status}") from exc


def _matched_roots(candidate: Mapping[str, object], label: str) -> tuple[str, ...]:
    """Return exact seed roots or whole-label edge roots, never inner substrings."""

    seed = str(candidate.get("seed") or "").casefold()
    if "+" in seed:
        parts = [part.strip() for part in seed.split("+") if part.strip()]
        matches = tuple(dict.fromkeys(part for part in parts if part in COMMERCIAL_ROOTS))
        if matches:
            return matches
    edge_matches = [
        root
        for root in COMMERCIAL_ROOTS
        if label == root
        or label.startswith(root)
        or (len(root) >= 3 and label.endswith(root))
    ]
    return tuple(sorted(edge_matches, key=lambda root: (-len(root), root))[:2])


def _compound_seed_parts(candidate: Mapping[str, object]) -> tuple[str, ...]:
    seed = str(candidate.get("seed") or "").casefold()
    if "+" not in seed:
        return ()
    return tuple(part.strip() for part in seed.split("+") if part.strip())


def _negative_label(label: str) -> bool:
    return label in _negative_connotations()


def _clamp(value: float, low: int = 0, high: int = 100) -> int:
    return max(low, min(high, int(round(value))))


def _label(candidate: Mapping[str, object]) -> str:
    label = str(candidate.get("domain_label") or candidate.get("label") or "")
    return label.strip().casefold()


def _tags(candidate: Mapping[str, object]) -> set[str]:
    raw = str(candidate.get("tags") or "")
    return {tag.strip().casefold() for tag in raw.split(";") if tag.strip()}


def _quality(candidate: Mapping[str, object]) -> int:
    try:
        return _clamp(float(str(candidate.get("quality_score", "50"))))
    except (TypeError, ValueError):
        return 50


def _seed_terms(candidate: Mapping[str, object]) -> set[str]:
    """Return exact recorded seed components, including plus-joined roots."""

    seed = str(candidate.get("seed") or "").casefold()
    return set(re.findall(r"[a-z0-9]+", seed))


def _hack_seed_adjustment(candidate: Mapping[str, object]) -> tuple[int, int, int]:
    method = str(candidate.get("method") or "").casefold()
    if method not in {"hack-suffix", "hack-phrase"}:
        return 0, 0, 0
    seed = str(candidate.get("seed") or "").strip().casefold()
    return _HACK_SEED_ADJUSTMENTS.get(seed, (0, 0, 0))


def _length_score(length: int) -> int:
    if length <= 2:
        return 62
    if length == 3:
        return 90
    if length == 4:
        return 96
    if 5 <= length <= 7:
        return 100
    if length <= 9:
        return 91
    if length == 10:
        return 78
    if length == 11:
        return 63
    return max(20, 52 - 4 * (length - 12))


def _pronounceability(label: str) -> int:
    if not label:
        return 0
    letters = [char for char in label if char.isalpha()]
    if not letters:
        return 15

    vowels = sum(char in _VOWELS for char in letters)
    score = 48
    if vowels:
        ratio = vowels / len(letters)
        score += 20 if 0.25 <= ratio <= 0.60 else 9
    else:
        score -= 28

    if len(letters) > 1:
        transitions = sum(
            (left in _VOWELS) != (right in _VOWELS)
            for left, right in zip(letters, letters[1:])
        )
        transition_ratio = transitions / (len(letters) - 1)
        score += 16 if 0.35 <= transition_ratio <= 0.85 else 5

    if re.search(r"[^aeiouy]{3}", label):
        score -= 22
    if re.search(r"[^aeiouy]{4,}", label):
        score -= 12
    if re.search(r"q(?!u)", label):
        score -= 16
    if any(pair in label for pair in ("jj", "ww", "vv", "qx", "xq")):
        score -= 10
    return _clamp(score)


def _spelling(label: str) -> int:
    if not label:
        return 0
    score = 100
    score -= 18 * sum(char.isdigit() for char in label)
    repeated_letters = sum(max(0, label.count(char) - 1) for char in set(label) if char.isalpha())
    score -= 5 * repeated_letters
    score -= 7 * sum(pair in label for pair in _AMBIGUOUS_PAIRS)
    return _clamp(score)


def _shape_score(label: str) -> int:
    """Score vowel balance, sound transitions, letter reuse, and familiar edges."""

    letters = [char for char in label if char.isalpha()]
    if not letters:
        return 0
    vowel_ratio = sum(char in _VOWELS for char in letters) / len(letters)
    vowel_balance = _clamp(100 - abs(vowel_ratio - 0.42) * 150)
    transitions = sum(
        (left in _VOWELS) != (right in _VOWELS)
        for left, right in zip(letters, letters[1:])
    )
    transition_ratio = transitions / max(1, len(letters) - 1)
    transition_balance = _clamp(100 - abs(transition_ratio - 0.65) * 80)
    unique_ratio = len(set(letters)) / len(letters)
    distinctness = _clamp(unique_ratio * 100)
    value = round(
        vowel_balance * 0.25
        + transition_balance * 0.20
        + distinctness * 0.15
        + _pronounceability(label) * 0.20
        + _phonetic_profile(label) * 0.20
    )
    if label[:2] in _COMMON_ONSETS:
        value += 3
    if any(label.endswith(ending) for ending in _COMMON_ENDINGS):
        value += 2
    clarity = sum(_LETTER_CLARITY.get(char, 5) for char in letters) / len(letters)
    value += round((clarity - 6.5) * 2)
    if label.startswith(("c", "g")) and len(label) > 1 and label[1] in "eiy":
        value -= 4
    value -= 5 * sum(pair in label for pair in _AMBIGUOUS_PAIRS)
    return _clamp(value)


def _shape_dimensions(label: str) -> tuple[int, int, int, int]:
    """Return distinct vowel, transition, letter-variety, and edge scores."""

    letters = [char for char in label if char.isalpha()]
    if not letters:
        return 0, 0, 0, 0
    vowel_ratio = sum(char in _VOWELS for char in letters) / len(letters)
    vowel_balance = _clamp(100 - abs(vowel_ratio - 0.42) * 150)
    transitions = sum(
        (left in _VOWELS) != (right in _VOWELS)
        for left, right in zip(letters, letters[1:])
    )
    transition_balance = _clamp(
        100 - abs(transitions / max(1, len(letters) - 1) - 0.65) * 80
    )
    distinctness = _clamp(len(set(letters)) / len(letters) * 100)
    onset = _ONSET_CLARITY.get(letters[0], 0)
    ending = _ENDING_CLARITY.get(letters[-1], 0)
    edge_quality = _clamp(55 + 7 * onset + 8 * ending)
    return vowel_balance, transition_balance, distinctness, edge_quality


def _phonetic_profile(label: str) -> int:
    """Estimate how easily the ordered letters form a memorable spoken label."""

    letters = [char for char in label if char.isalpha()]
    if not letters:
        return 0
    score = 50
    clarity = sum(_LETTER_CLARITY.get(char, 5) for char in letters) / len(letters)
    score += round((clarity - 6.5) * 5)
    score += _ONSET_CLARITY.get(letters[0], 0)
    score += _ENDING_CLARITY.get(letters[-1], 0)
    for left, right in zip(letters, letters[1:]):
        pair = left + right
        left_vowel = left in _VOWELS
        right_vowel = right in _VOWELS
        if left_vowel != right_vowel:
            score += 2
        elif left_vowel and right_vowel:
            score += 2 if pair in _COMMON_VOWEL_PAIRS else -1
        else:
            score += 2 if pair in _CLEAR_CONSONANT_PAIRS else -2
    if label.startswith(("c", "g")) and len(label) > 1 and label[1] in "eiy":
        score -= 5
    return _clamp(score)


def _brandability(candidate: Mapping[str, object], label: str) -> int:
    length = _length_score(len(label))
    pronunciation = _pronounceability(label)
    spelling = _spelling(label)
    quality = _quality(candidate)
    shape = _shape_score(label)
    vowel_balance, transition_balance, distinctness, edge_quality = _shape_dimensions(label)
    base = _clamp(
        length * 0.25
        + pronunciation * 0.22
        + spelling * 0.15
        + quality * 0.15
        + shape * 0.10
        + vowel_balance * 0.04
        + transition_balance * 0.03
        + distinctness * 0.03
        + edge_quality * 0.03
    )
    brand_adjustment, _commercial_adjustment, _resale_adjustment = _hack_seed_adjustment(
        candidate
    )
    penalty = _NEGATIVE_PENALTY if _negative_label(label) else 0
    return _clamp(base + brand_adjustment - penalty)


def _commercial(candidate: Mapping[str, object], label: str) -> int:
    category = str(candidate.get("category") or "").casefold()
    method = str(candidate.get("method") or "").casefold()
    tags = _tags(candidate)
    roots = _matched_roots(candidate, label)
    parts = _compound_seed_parts(candidate)
    if len(parts) > 1:
        values = [COMMERCIAL_ROOTS.get(part, (0, _UNKNOWN_ROOT_DEMAND, _UNKNOWN_ROOT_BREADTH, ""))[1] for part in parts]
        base = sum(values) / len(values)
        if len(roots) >= 2:
            base += 6
    elif roots:
        base = max(COMMERCIAL_ROOTS[root][1] for root in roots)
        if len(roots) >= 2:
            base += 3
    elif category == "dictionary" and method == "dictionary":
        base = 55
    elif category == "short" and len(label) <= 4:
        base = 49
    else:
        base = 46
        if category == "invented" or "given_name" in tags:
            base -= 4

    vowel_balance, transition_balance, distinctness, edge_quality = _shape_dimensions(label)
    shape_adjustment = round((_shape_score(label) - 55) / 3)
    shape_adjustment += round((vowel_balance - 60) / 12)
    shape_adjustment += round((transition_balance - 60) / 12)
    shape_adjustment += round((distinctness - 70) / 12)
    shape_adjustment += round((edge_quality - 60) / 12)
    shape_adjustment += 3 if len(label) <= 6 else -min(6, len(label) - 9) if len(label) > 9 else 0
    if "given_name" in tags:
        shape_adjustment -= 3
    _brand_adjustment, commercial_adjustment, _resale_adjustment = _hack_seed_adjustment(
        candidate
    )
    negative_penalty = _NEGATIVE_PENALTY if _negative_label(label) else 0
    return _clamp(base + shape_adjustment + commercial_adjustment - negative_penalty)


def _syllable_estimate(label: str) -> int:
    groups = re.findall(r"[aeiouy]+", label)
    return max(1, len(groups)) if label else 0


def _shortness(label: str) -> int:
    length = len(label)
    if length <= 2:
        base = 100
    elif length == 3:
        base = 100
    elif length == 4:
        base = 96
    elif length == 5:
        base = 91
    elif length == 6:
        base = 86
    elif length == 7:
        base = 81
    elif length == 8:
        base = 76
    elif length == 9:
        base = 71
    elif length == 10:
        base = 66
    elif length == 11:
        base = 61
    elif length == 12:
        base = 46
    else:
        base = max(0, 36 - 8 * (length - 13))
    bonus = 2 if label.isalpha() else 0
    bonus += 2 if 1 <= _syllable_estimate(label) <= 2 else 0
    vowel_balance, transition_balance, distinctness, edge_quality = _shape_dimensions(label)
    bonus += max(-4, min(5, round((_shape_score(label) - 60) / 8)))
    bonus += round((distinctness - 70) / 25)
    bonus += round((edge_quality - 60) / 25)
    return _clamp(base + bonus)


def _hack(candidate: Mapping[str, object]) -> int:
    category = str(candidate.get("category") or "").casefold()
    method = str(candidate.get("method") or "").casefold()
    tags = _tags(candidate)
    seed = str(candidate.get("seed") or "").strip()
    quality = _quality(candidate)
    phonetic_bonus = round(_pronounceability(_label(candidate)) / 12)
    if method == "hack-suffix" and seed:
        return _clamp(67 + quality * 0.22 + phonetic_bonus)
    if method == "hack-phrase" and seed:
        return _clamp(64 + quality * 0.22 + phonetic_bonus)
    if category == "domain_hacks" or "domain_hacks" in tags:
        return _clamp(55 + quality * 0.20 + phonetic_bonus)
    return 12


def _resale(candidate: Mapping[str, object], label: str) -> int:
    category = str(candidate.get("category") or "").casefold()
    method = str(candidate.get("method") or "").casefold()
    tags = _tags(candidate)
    roots = _matched_roots(candidate, label)
    length = len(label)
    score = 40
    if length <= 3:
        score += 28
    elif length == 4:
        score += 26
    elif length == 5:
        score += 22
    elif length == 6:
        score += 18
    elif length == 7:
        score += 14
    elif length == 8:
        score += 10
    elif length == 9:
        score += 6
    elif length <= 11:
        score += 1
    else:
        score -= min(20, (length - 11) * 3)

    syllables = _syllable_estimate(label)
    score += {1: 10, 2: 7, 3: 2}.get(syllables, -5)
    pronunciation = _pronounceability(label)
    score += round((pronunciation - 55) / 8)
    vowel_balance, transition_balance, distinctness, edge_quality = _shape_dimensions(label)
    score += round((_shape_score(label) - 55) / 4)
    score += round((vowel_balance - 60) / 10)
    score += round((transition_balance - 60) / 12)
    score += round((distinctness - 70) / 12)
    score += round((edge_quality - 60) / 10)

    if roots:
        root_demand = max(COMMERCIAL_ROOTS[root][1] for root in roots)
        root_breadth = max(COMMERCIAL_ROOTS[root][2] for root in roots)
        score += round((root_demand - _UNKNOWN_ROOT_DEMAND) * 0.18)
        score += round(root_breadth / 3)
        if label in roots:
            score += 7
        if len(roots) >= 2:
            score += 4

    if category == "dictionary" and method == "dictionary":
        score += 10
    elif "real_word" in tags and "given_name" not in tags:
        score += 5
    if category == "short" and length <= 4:
        score += 7
    if method in {"hack-suffix", "hack-phrase"}:
        score += 8
    if "given_name" in tags:
        score -= 14
    if label in _BROAD_BUYER_NOUNS:
        score += 8
    elif label in _LOW_BREADTH_DICTIONARY_WORDS:
        score -= 10

    score -= 9 * sum(pair in label for pair in _AMBIGUOUS_PAIRS)
    if any(label.count(char) > 1 for char in set(label)):
        score -= 3
    _brand_adjustment, _commercial_adjustment, resale_adjustment = _hack_seed_adjustment(
        candidate
    )
    negative_penalty = _NEGATIVE_PENALTY if _negative_label(label) else 0
    return _clamp(score + resale_adjustment - negative_penalty, high=95)


def _rationale(
    candidate: Mapping[str, object],
    label: str,
    scores: Mapping[str, int],
    *,
    trademark_override: int | None,
    trademark_status: str | None = None,
) -> str:
    category = str(candidate.get("category") or "").casefold()
    method = str(candidate.get("method") or "").casefold()
    tags = _tags(candidate)
    roots = _matched_roots(candidate, label)
    if label in _AWKWARD_LABELS:
        rationale = f"Awkward or truncated label '{label}'; {len(label)} letters; quality penalty."
    elif "technical_term" in tags:
        rationale = f"Niche technical term '{label}'; {len(label)} letters; not a common word."
    elif _negative_label(label):
        rationale = f"Negative or medical term '{label}'; {len(label)} letters; buyer-fit penalty."
    elif roots:
        strongest = max(roots, key=lambda root: COMMERCIAL_ROOTS[root][1])
        buyer = COMMERCIAL_ROOTS[strongest][3]
        if len(roots) > 1:
            root_text = "+".join(f"'{root}'" for root in roots)
            rationale = f"Commercial roots {root_text}; {len(label)} letters; {buyer} buyers."
        else:
            rationale = f"Strong root '{strongest}'; {len(label)} letters; {buyer} buyers."
    elif method in {"hack-suffix", "hack-phrase"}:
        seed = str(candidate.get("seed") or "").replace("+", " ").strip()
        rationale = f"Readable wordplay from '{seed[:22]}'; {len(label)} letters; pronounceable form."
    elif category == "dictionary" and method == "dictionary":
        rationale = f"Common word '{label}'; {len(label)} letters; {_syllable_estimate(label)} syllables."
    elif "given_name" in tags:
        rationale = f"Name-like label '{label}'; {len(label)} letters; pronounceable form."
    else:
        rationale = f"{len(label)} letters; {_syllable_estimate(label)} syllables; pronounceable brandable shape."

    if trademark_status == "limited_screen_no_obvious_match":
        rationale += " TM limited screen, no obvious match; no clearance implied."
    elif trademark_status == "needs legal review":
        rationale += " TM needs legal review."
    elif trademark_status in {"blocked", "unverified", "not yet screened", None}:
        rationale += " TM unverified (no clearance implied)."
    else:
        rationale += f" TM score {trademark_override}."
    return rationale.encode("ascii", "ignore").decode("ascii")[:140]


def weighted_total(components: Mapping[str, int]) -> Decimal:
    """Return the exact one-decimal weighted total with ties rounded to even."""

    total = sum(
        Decimal(components[name]) * Decimal(str(weight))
        for name, weight in SCORE_WEIGHTS.items()
    )
    return total.quantize(Decimal("0.1"), rounding=ROUND_HALF_EVEN)


def score_domain(
    candidate: Mapping[str, object],
    *,
    trademark_override: int | None = None,
    trademark_status: str | None = None,
) -> dict[str, str | int | Decimal]:
    """Score one candidate row without network access or hidden state."""

    label = _label(candidate)
    category = str(candidate.get("category") or "").strip()
    if not label:
        raise ValueError("candidate must include a domain label")
    if trademark_status is None:
        trademark_status = "not yet screened"
    mapped_trademark_score = trademark_score_for_status(trademark_status)
    if trademark_override is not None and trademark_override != mapped_trademark_score:
        raise ValueError("trademark_override does not match the screening-state mapping")

    components = {
        "brandability": _brandability(candidate, label),
        "commercial": _commercial(candidate, label),
        "shortness": _shortness(label),
        "hack": _hack(candidate),
        "resale": _resale(candidate, label),
        "trademark": mapped_trademark_score,
    }
    total = weighted_total(components)
    return {
        "domain": f"{label}.si",
        "category": category,
        **components,
        "total": total,
        "rationale": _rationale(
            candidate,
            label,
            components,
            trademark_override=mapped_trademark_score,
            trademark_status=trademark_status,
        ),
    }


def _read_candidates(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        required = {"domain_label", "category", "method", "seed", "tags", "quality_score"}
        if not reader.fieldnames or not required.issubset(reader.fieldnames):
            raise ValueError("candidate CSV is missing required scoring columns")
        return [dict(row) for row in reader]


def _read_latest(path: Path) -> dict[str, dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        required = {"domain", "classification"}
        if not reader.fieldnames or not required.issubset(reader.fieldnames):
            raise ValueError("RDAP evidence CSV must include domain and classification")
        latest: dict[str, dict[str, str]] = {}
        for row in reader:
            domain = (row.get("domain") or "").strip().casefold()
            if domain:
                latest[domain] = {key: value or "" for key, value in row.items()}
        return latest


def write_scores(
    candidates_path: str | Path,
    rdap_path: str | Path,
    output_path: str | Path,
    *,
    trademark_evidence_path: str | Path | None = None,
    trademark_source_evidence_path: str | Path | None = None,
) -> int:
    """Write scores for the latest RDAP-404 rows in stable domain order."""

    candidates = _read_candidates(Path(candidates_path))
    rdap_latest = _read_latest(Path(rdap_path))
    trademark_summaries: dict[str, dict[str, str]] = {}
    if trademark_evidence_path is not None:
        from .trademarks import read_trademark_summary

        source_path = trademark_source_evidence_path or (
            Path(trademark_evidence_path).parent / "trademark_evidence.csv"
        )
        candidate_domains = {
            f"{_label(candidate)}.si"
            for candidate in candidates
            if rdap_latest.get(f"{_label(candidate)}.si", {}).get("classification")
            == "potentially_unregistered"
        }
        trademark_summaries = read_trademark_summary(
            trademark_evidence_path,
            evidence_path=source_path,
            candidate_domains=candidate_domains,
            candidates_path=candidates_path,
        )
    scored: dict[str, dict[str, str | int | Decimal]] = {}
    for candidate in candidates:
        label = _label(candidate)
        domain = f"{label}.si"
        if rdap_latest.get(domain, {}).get("classification") != "potentially_unregistered":
            continue
        summary = trademark_summaries.get(domain)
        scored[domain] = score_domain(
            candidate,
            trademark_override=int(summary["trademark_score"]) if summary else None,
            trademark_status=summary["status"] if summary else "not yet screened",
        )

    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=SCORE_FIELDS, lineterminator="\n")
        writer.writeheader()
        for domain in sorted(scored):
            row = scored[domain]
            writer.writerow(
                {
                    **row,
                    "total": f"{row['total']:.1f}",
                }
            )
    return len(scored)
