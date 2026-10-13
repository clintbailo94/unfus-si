"""Robotics, quantum, energy storage, advanced materials, and autonomy compounds."""

from __future__ import annotations

from .common import generate_root_suffix_pool
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
    return generate_root_suffix_pool(
        "emerging_industries",
        "emerging_industries_roots.txt",
        "emerging_industries_suffixes.txt",
        "emerging_industries_compounds.txt",
        "emerging_industries_standalone.txt",
        blends=_BLENDS,
    )
