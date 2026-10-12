"""Healthcare, diagnostics, biotech, longevity, pharma, and research compounds."""

from __future__ import annotations

from .common import generate_curated_compounds
from ..schema import Candidate


_BLENDS = (
    ("biotech", "biology+technology"),
    ("medtech", "medicine+technology"),
    ("healthtech", "healthcare+technology"),
    ("telehealth", "telecommunications+healthcare"),
    ("neurotech", "neuroscience+technology"),
)


def generate() -> list[Candidate]:
    return generate_curated_compounds(
        "health_science", "health_science_concepts.txt", "health_science_products.txt", blends=_BLENDS
    )
