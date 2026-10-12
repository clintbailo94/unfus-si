"""Shared candidate data types and CSV schema."""

from __future__ import annotations

from dataclasses import dataclass


CSV_FIELDS = ("domain_label", "category", "method", "seed", "tags", "quality_score")


@dataclass(frozen=True, slots=True)
class Candidate:
    domain_label: str
    category: str
    method: str
    seed: str
    tags: tuple[str, ...]
    quality_score: int

    def to_row(self) -> dict[str, str | int]:
        return {
            "domain_label": self.domain_label,
            "category": self.category,
            "method": self.method,
            "seed": self.seed,
            "tags": ";".join(self.tags),
            "quality_score": self.quality_score,
        }
