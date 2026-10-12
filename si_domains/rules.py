"""Data-driven .si registry name rules used before network lookups."""

from __future__ import annotations

import csv
from pathlib import Path

from .config import DATA_DIR
from .validation import ascii_label


GENERAL_TERMS_URL = "https://www.register.si/en/general-terms/"
TARIFF_URL = "https://www.register.si/en/tariff-for-registrars/"
_CSV_FIELDS = ("label", "class", "source_url", "note")


def _load_csv(path: Path, expected_class: str) -> dict[str, dict[str, str]]:
    entries: dict[str, dict[str, str]] = {}
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames is None or not set(_CSV_FIELDS).issubset(reader.fieldnames):
            raise ValueError(f"{path} must include columns: {', '.join(_CSV_FIELDS)}")
        for row in reader:
            label = (row.get("label") or "").strip()
            source_url = (row.get("source_url") or "").strip()
            rule_class = (row.get("class") or "").strip().casefold()
            if not label or not source_url:
                raise ValueError(f"{path} contains a row without label or source_url")
            if rule_class != expected_class:
                raise ValueError(f"{path} contains class {rule_class!r}; expected {expected_class!r}")
            canonical_label = ascii_label(label)
            if canonical_label is None:
                raise ValueError(f"{path} contains invalid label {label!r}")
            if canonical_label in entries:
                raise ValueError(f"{path} contains duplicate label {canonical_label!r}")
            entries[canonical_label] = {
                "label": canonical_label,
                "class": rule_class,
                "source_url": source_url,
                "note": (row.get("note") or "").strip(),
            }
    return entries


def load_name_rules(
    reserved_path: str | Path | None = None,
    restricted_path: str | Path | None = None,
) -> tuple[dict[str, dict[str, str]], dict[str, dict[str, str]]]:
    """Load the evidence-backed reserved and restricted labels from CSV files."""

    reserved_file = Path(reserved_path) if reserved_path is not None else DATA_DIR / "reserved_names.csv"
    restricted_file = Path(restricted_path) if restricted_path is not None else DATA_DIR / "restricted_names.csv"
    return _load_csv(reserved_file, "reserved"), _load_csv(restricted_file, "restricted")


_RESERVED_NAMES, _RESTRICTED_NAMES = load_name_rules()
_PREMIUM_NAMES: dict[str, dict[str, str]] = {}


def _find_name_rule(canonical_label: str) -> dict[str, str] | None:
    for name_rules in (_RESERVED_NAMES, _RESTRICTED_NAMES, _PREMIUM_NAMES):
        entry = name_rules.get(canonical_label)
        if entry:
            return entry
    return None


def classify(label: str) -> str:
    """Classify a label under known registry rules, before network lookup.

    ``ok`` only means that the label passes known syntax and name lists; it
    makes no claim about availability.
    """

    canonical_label = ascii_label(label)
    if canonical_label is None:
        return "invalid_syntax"
    entry = _find_name_rule(canonical_label)
    return entry["class"] if entry else "ok"


def explain(label: str) -> tuple[str, str, str]:
    """Return ``(classification, rule_id, source_url)`` for a label."""

    classification = classify(label)
    canonical_label = ascii_label(label)
    if classification in {"reserved", "restricted", "premium"} and canonical_label is not None:
        entry = _find_name_rule(canonical_label)
        if entry:
            return classification, f"{classification}:{canonical_label}", entry["source_url"]

    if classification == "invalid_syntax":
        return classification, "syntax.registry_rules", GENERAL_TERMS_URL
    if classification == "premium":
        return classification, "premium.registry_tier", TARIFF_URL
    return "ok", "syntax.known_rules", GENERAL_TERMS_URL
