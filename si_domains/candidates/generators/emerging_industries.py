"""Robotics, quantum, energy storage, advanced materials, and autonomy compounds."""

from __future__ import annotations

from .common import generate_curated_compounds
from ..schema import Candidate


_BLENDS = (
    ("cleantech", "clean+technology"),
    ("greentech", "green+technology"),
    ("climatetech", "climate+technology"),
    ("agritech", "agriculture+technology"),
    ("spacetech", "space+technology"),
    ("foodtech", "food+technology"),
    ("autotech", "automotive+technology"),
)


def generate() -> list[Candidate]:
    return generate_curated_compounds(
        "emerging_industries",
        "emerging_industries_concepts.txt",
        "emerging_industries_products.txt",
        "emerging_industries_pairs.txt",
        blends=_BLENDS,
    )
