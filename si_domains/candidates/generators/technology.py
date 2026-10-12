"""Cloud, security, software, fintech, and infrastructure compounds."""

from __future__ import annotations

from .common import generate_curated_compounds
from ..schema import Candidate


_BLENDS = (
    ("devops", "development+operations"),
    ("netops", "network+operations"),
    ("infosec", "information+security"),
)


def generate() -> list[Candidate]:
    return generate_curated_compounds(
        "technology", "technology_concepts.txt", "technology_products.txt", blends=_BLENDS
    )
