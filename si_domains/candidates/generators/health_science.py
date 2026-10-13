"""Healthcare, diagnostics, biotech, longevity, pharma, and research compounds."""

from __future__ import annotations

from .common import generate_root_suffix_pool
from ..schema import Candidate


_BLENDS = (
    ("biotech", "biology+technology"),
    ("medtech", "medicine+technology"),
    ("healthtech", "healthcare+technology"),
    ("telehealth", "telecommunications+healthcare"),
    ("neurotech", "neuroscience+technology"),
)


def generate() -> list[Candidate]:
    return generate_root_suffix_pool(
        "health_science",
        "health_science_roots.txt",
        "health_science_suffixes.txt",
        "health_science_compounds.txt",
        "health_science_standalone.txt",
        blends=_BLENDS,
    )
