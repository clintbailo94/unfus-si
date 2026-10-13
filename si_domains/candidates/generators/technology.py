"""Cloud, security, software, fintech, and infrastructure compounds."""

from __future__ import annotations

from .common import generate_root_suffix_pool
from ..schema import Candidate


_BLENDS = (
    ("devops", "development+operations"),
    ("netops", "network+operations"),
    ("infosec", "information+security"),
)


def generate() -> list[Candidate]:
    return generate_root_suffix_pool(
        "technology",
        "technology_roots.txt",
        "technology_suffixes.txt",
        "technology_compounds.txt",
        "technology_standalone.txt",
        blends=_BLENDS,
    )
