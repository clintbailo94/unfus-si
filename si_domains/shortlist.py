"""Build a deterministic, WHOIS-confirmed .si shortlist and review sample."""

from __future__ import annotations

import csv
import math
import random
from collections import Counter, defaultdict
from pathlib import Path

from . import rules
from .scoring import SCORE_FIELDS


SHORTLIST_FIELDS = (
    "rank",
    "domain",
    "category",
    "total",
    "brandability",
    "commercial",
    "shortness",
    "hack",
    "resale",
    "trademark",
    "rdap_timestamp",
    "whois_timestamp",
    "rationale",
)
EXCLUDED_FIELDS = (
    "domain",
    "category",
    "reason",
    "rdap_classification",
    "whois_classification",
    "rdap_timestamp",
    "whois_timestamp",
)
SAMPLE_FIELDS = (
    "domain",
    "category",
    "rdap_timestamp",
    "whois_result",
    "whois_timestamp",
)
SHORTLIST_LIMIT = 500
CATEGORY_LIMIT = 125
REVIEW_SAMPLE_SIZE = 30

_SPECIAL_REASONS = {
    "invalid_syntax": "invalid",
    "reserved": "reserved",
    "restricted": "restricted",
    "premium": "premium",
}


def _read_csv(path: Path, required: set[str], description: str) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if not reader.fieldnames or not required.issubset(reader.fieldnames):
            raise ValueError(f"{description} CSV is missing required columns")
        return [
            {key: (value or "") for key, value in row.items() if key}
            for row in reader
        ]


def _latest_by_domain(rows: list[dict[str, str]]) -> dict[str, dict[str, str]]:
    latest: dict[str, dict[str, str]] = {}
    for row in rows:
        domain = (row.get("domain") or "").strip().casefold()
        if domain:
            latest[domain] = row
    return latest


def _reason(
    label: str,
    rdap_row: dict[str, str] | None,
    whois_row: dict[str, str] | None,
) -> str | None:
    rule_class = rules.classify(label)
    if rule_class != "ok":
        return _SPECIAL_REASONS.get(rule_class, "invalid")

    rdap_class = (rdap_row or {}).get("classification", "")
    if rdap_class == "registered":
        return "rdap_registered"
    if rdap_class in _SPECIAL_REASONS:
        return _SPECIAL_REASONS[rdap_class]
    if rdap_class != "potentially_unregistered":
        return "rdap_unchecked" if not rdap_class else "rdap_unverified"

    whois_class = (whois_row or {}).get("classification", "")
    if whois_class == "registered":
        return "whois_registered_conflict"
    if whois_class == "unverified":
        return "whois_unverified"
    if whois_class != "not_registered":
        return "whois_unchecked" if not whois_class else "whois_unverified"
    return None


def _whois_result(row: dict[str, str] | None) -> str:
    classification = (row or {}).get("classification", "")
    if classification in {"not_registered", "registered", "unverified"}:
        return classification
    return "not yet checked"


def _total(row: dict[str, str]) -> float:
    try:
        value = float(row["total"])
    except (KeyError, ValueError) as exc:
        raise ValueError(f"invalid total score for {row.get('domain', 'unknown domain')}") from exc
    if not math.isfinite(value) or not 0 <= value <= 100:
        domain = row.get("domain", "unknown domain")
        raise ValueError(f"score total must be between 0 and 100 for {domain}")
    return value


def _write_csv(path: Path, fieldnames: tuple[str, ...], rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def _sample_rows(
    candidates: list[dict[str, str]],
    rdap_latest: dict[str, dict[str, str]],
    whois_latest: dict[str, dict[str, str]],
    *,
    seed: int,
    sample_size: int = REVIEW_SAMPLE_SIZE,
) -> list[dict[str, str]]:
    by_status: dict[str, list[dict[str, str]]] = defaultdict(list)
    seen: set[str] = set()
    for candidate in candidates:
        label = (candidate.get("domain_label") or "").strip().casefold()
        domain = f"{label}.si"
        rdap_row = rdap_latest.get(domain)
        if (
            not label
            or domain in seen
            or (rdap_row or {}).get("classification") != "potentially_unregistered"
        ):
            continue
        seen.add(domain)
        whois_row = whois_latest.get(domain)
        by_status[_whois_result(whois_row)].append(
            {
                "domain": domain,
                "category": candidate.get("category", ""),
                "rdap_timestamp": (rdap_row or {}).get("utc_timestamp", ""),
                "whois_result": _whois_result(whois_row),
                "whois_timestamp": (whois_row or {}).get("utc_timestamp", ""),
            }
        )

    pool = [row for status in sorted(by_status) for row in by_status[status]]
    target = min(sample_size, len(pool))
    if target == 0:
        return []

    rng = random.Random(seed)
    chosen: list[dict[str, str]] = []
    chosen_domains: set[str] = set()
    if target >= len(by_status):
        for status in sorted(by_status):
            row = rng.choice(by_status[status])
            chosen.append(row)
            chosen_domains.add(row["domain"])

    remaining = [row for row in pool if row["domain"] not in chosen_domains]
    chosen.extend(rng.sample(remaining, target - len(chosen)))
    return chosen


def build_outputs(
    candidates_path: str | Path,
    rdap_path: str | Path,
    whois_path: str | Path,
    scores_path: str | Path,
    shortlist_path: str | Path,
    excluded_path: str | Path,
    sample_path: str | Path,
    *,
    seed: int = 20261013,
) -> tuple[int, int, int]:
    """Write the ranked shortlist, exclusions, and a seeded RDAP-404 sample."""

    candidates = _read_csv(
        Path(candidates_path),
        {"domain_label", "category"},
        "candidate",
    )
    rdap_latest = _latest_by_domain(
        _read_csv(Path(rdap_path), {"domain", "classification"}, "RDAP evidence")
    )
    whois_latest = _latest_by_domain(
        _read_csv(Path(whois_path), {"domain", "classification"}, "WHOIS evidence")
    )
    score_rows = _read_csv(Path(scores_path), set(SCORE_FIELDS), "score")
    scores = _latest_by_domain(score_rows)

    eligible: list[tuple[dict[str, str], dict[str, str], dict[str, str], dict[str, str]]] = []
    excluded: list[dict[str, str]] = []
    seen: set[str] = set()
    for candidate in candidates:
        label = (candidate.get("domain_label") or "").strip().casefold()
        if not label:
            continue
        domain = f"{label}.si"
        if domain in seen:
            continue
        seen.add(domain)
        rdap_row = rdap_latest.get(domain)
        whois_row = whois_latest.get(domain)
        reason = _reason(label, rdap_row, whois_row)
        if reason:
            excluded.append(
                {
                    "domain": domain,
                    "category": candidate.get("category", ""),
                    "reason": reason,
                    "rdap_classification": (rdap_row or {}).get("classification", ""),
                    "whois_classification": (whois_row or {}).get("classification", ""),
                    "rdap_timestamp": (rdap_row or {}).get("utc_timestamp", ""),
                    "whois_timestamp": (whois_row or {}).get("utc_timestamp", ""),
                }
            )
            continue
        score_row = scores.get(domain)
        if score_row is None:
            raise ValueError(f"eligible domain {domain} is missing from scores; run score first")
        _total(score_row)
        eligible.append((candidate, rdap_row or {}, whois_row or {}, score_row))

    eligible.sort(
        key=lambda item: (
            -_total(item[3]),
            len(item[0]["domain_label"].strip()),
            item[0]["domain_label"].strip().casefold(),
        )
    )
    selected: list[tuple[dict[str, str], dict[str, str], dict[str, str], dict[str, str]]] = []
    category_counts: Counter[str] = Counter()
    for item in eligible:
        category = item[0].get("category", "")
        if category_counts[category] >= CATEGORY_LIMIT:
            continue
        selected.append(item)
        category_counts[category] += 1
        if len(selected) == SHORTLIST_LIMIT:
            break

    shortlist_rows: list[dict[str, str]] = []
    for rank, (candidate, rdap_row, whois_row, score_row) in enumerate(selected, start=1):
        shortlist_rows.append(
            {
                "rank": str(rank),
                "domain": f"{candidate['domain_label'].strip().casefold()}.si",
                "category": candidate.get("category", ""),
                "total": f"{_total(score_row):.1f}",
                "brandability": score_row["brandability"],
                "commercial": score_row["commercial"],
                "shortness": score_row["shortness"],
                "hack": score_row["hack"],
                "resale": score_row["resale"],
                "trademark": score_row["trademark"],
                "rdap_timestamp": rdap_row.get("utc_timestamp", ""),
                "whois_timestamp": whois_row.get("utc_timestamp", ""),
                "rationale": score_row["rationale"],
            }
        )

    excluded.sort(key=lambda row: row["domain"])
    sample_rows = _sample_rows(candidates, rdap_latest, whois_latest, seed=seed)
    _write_csv(Path(shortlist_path), SHORTLIST_FIELDS, shortlist_rows)
    _write_csv(Path(excluded_path), EXCLUDED_FIELDS, excluded)
    _write_csv(Path(sample_path), SAMPLE_FIELDS, sample_rows)
    return len(shortlist_rows), len(excluded), len(sample_rows)
