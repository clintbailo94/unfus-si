"""Deterministic, explainable heuristic scores for RDAP-404 candidates."""

from __future__ import annotations

import csv
import re
from pathlib import Path
from typing import Mapping


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

_CATEGORY_DEMAND = {
    "domain_hacks": 70,
    "ai": 88,
    "short": 76,
    "dictionary": 73,
    "invented": 68,
    "technology": 86,
    "business_finance": 86,
    "health_science": 82,
    "consumer_brands": 81,
    "emerging_industries": 84,
}
_TAG_DEMAND = {
    "ai": 10,
    "technology": 9,
    "business_finance": 9,
    "health_science": 8,
    "emerging_industries": 8,
    "consumer_brands": 7,
    "short": 3,
    "dictionary": 3,
    "domain_hacks": 3,
    "invented": 2,
}
_INDUSTRY_TERMS = (
    "ai",
    "agent",
    "auto",
    "bank",
    "bio",
    "business",
    "care",
    "cloud",
    "crypto",
    "data",
    "finance",
    "health",
    "invest",
    "market",
    "med",
    "pay",
    "robot",
    "science",
    "security",
    "software",
    "tech",
    "trade",
)
_AMBIGUOUS_PAIRS = ("cl", "rn", "vv", "ii", "0o", "1l")
_VOWELS = frozenset("aeiouy")
_FACTOR_LABELS = {
    "brandability": "brand",
    "commercial": "demand",
    "shortness": "shortness",
    "hack": "hack",
    "resale": "resale",
    "trademark": "trademark",
}


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


def _length_score(length: int) -> int:
    if length <= 2:
        return 62
    if length == 3:
        return 76
    if length == 4:
        return 90
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


def _brandability(candidate: Mapping[str, object], label: str) -> int:
    length = _length_score(len(label))
    pronunciation = _pronounceability(label)
    spelling = _spelling(label)
    quality = _quality(candidate)
    return _clamp(length * 0.30 + pronunciation * 0.30 + spelling * 0.20 + quality * 0.20)


def _commercial(candidate: Mapping[str, object], label: str) -> int:
    category = str(candidate.get("category") or "").casefold()
    method = str(candidate.get("method") or "").casefold()
    tags = _tags(candidate)
    category_score = _CATEGORY_DEMAND.get(category, 65)
    if method == "invented-reclassified":
        category_score -= 5
    tag_score = max((_TAG_DEMAND.get(tag, 0) for tag in tags), default=0)
    searchable = f"{label} {' '.join(tags)}".replace("_", " ")
    keyword_bonus = min(10, 3 * sum(term in searchable for term in _INDUSTRY_TERMS))
    return _clamp(category_score + tag_score + keyword_bonus)


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
    return _clamp(base + bonus)


def _hack(candidate: Mapping[str, object]) -> int:
    category = str(candidate.get("category") or "").casefold()
    method = str(candidate.get("method") or "").casefold()
    tags = _tags(candidate)
    seed = str(candidate.get("seed") or "").strip()
    quality_bonus = max(0, _quality(candidate) - 80)
    if method == "hack-suffix" and seed:
        return _clamp(78 + quality_bonus * 0.4)
    if method == "hack-phrase" and seed:
        return _clamp(74 + quality_bonus * 0.3)
    if category == "domain_hacks" or "domain_hacks" in tags:
        return 70
    return 12


def _resale(candidate: Mapping[str, object], label: str) -> int:
    category = str(candidate.get("category") or "").casefold()
    method = str(candidate.get("method") or "").casefold()
    tags = _tags(candidate)
    base = {
        "dictionary": 72,
        "short": 69,
        "consumer_brands": 67,
        "domain_hacks": 62,
        "ai": 66,
        "technology": 64,
        "business_finance": 65,
        "health_science": 60,
        "emerging_industries": 61,
        "invented": 58,
    }.get(category, 56)
    if method == "invented-reclassified":
        base -= 8
        if "real_word" in tags:
            base += 2
    elif method == "dictionary":
        base += 10
    if len(label) <= 5:
        base += 8
    elif len(label) <= 8:
        base += 5
    if _pronounceability(label) >= 72:
        base += 5
    if "dictionary" in tags:
        base += 3
    if len(label) >= 12:
        base -= 15
    return _clamp(base, high=85)


def _rationale(scores: Mapping[str, int], *, trademark_override: int | None) -> str:
    weighted = sorted(
        SCORE_WEIGHTS,
        key=lambda name: (scores[name] * SCORE_WEIGHTS[name], scores[name], name),
        reverse=True,
    )
    strengths = weighted[:2]
    weakness = min(
        (name for name in SCORE_WEIGHTS if name not in strengths),
        key=lambda name: (scores[name], name),
    )
    rationale = (
        f"Strengths: {_FACTOR_LABELS[strengths[0]]} {scores[strengths[0]]}, "
        f"{_FACTOR_LABELS[strengths[1]]} {scores[strengths[1]]}; "
        f"weakness: {_FACTOR_LABELS[weakness]} {scores[weakness]}."
    )
    if trademark_override is None:
        rationale += " TM not yet screened."
    else:
        rationale += f" TM override {trademark_override}."
    return rationale[:140]


def score_domain(
    candidate: Mapping[str, object], *, trademark_override: int | None = None
) -> dict[str, str | int | float]:
    """Score one candidate row without network access or hidden state."""

    label = _label(candidate)
    category = str(candidate.get("category") or "").strip()
    if not label:
        raise ValueError("candidate must include a domain label")
    if trademark_override is not None:
        if not isinstance(trademark_override, int) or not 0 <= trademark_override <= 100:
            raise ValueError("trademark_override must be an integer from 0 to 100")

    components = {
        "brandability": _brandability(candidate, label),
        "commercial": _commercial(candidate, label),
        "shortness": _shortness(label),
        "hack": _hack(candidate),
        "resale": _resale(candidate, label),
        "trademark": 70 if trademark_override is None else trademark_override,
    }
    total = round(sum(components[name] * weight for name, weight in SCORE_WEIGHTS.items()), 1)
    return {
        "domain": f"{label}.si",
        "category": category,
        **components,
        "total": total,
        "rationale": _rationale(components, trademark_override=trademark_override),
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
) -> int:
    """Write scores for the latest RDAP-404 rows in stable domain order."""

    candidates = _read_candidates(Path(candidates_path))
    rdap_latest = _read_latest(Path(rdap_path))
    scored: dict[str, dict[str, str | int | float]] = {}
    for candidate in candidates:
        label = _label(candidate)
        domain = f"{label}.si"
        if rdap_latest.get(domain, {}).get("classification") != "potentially_unregistered":
            continue
        scored[domain] = score_domain(candidate)

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
                    "total": f"{float(row['total']):.1f}",
                }
            )
    return len(scored)
