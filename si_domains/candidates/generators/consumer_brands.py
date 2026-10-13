"""Fashion, travel, entertainment, lifestyle, education, and commerce compounds."""

from __future__ import annotations

from .common import generate_root_suffix_pool
from ..schema import Candidate


_BLENDS = (
    ("edtech", "education+technology"),
    ("ecommerce", "electronic+commerce"),
    ("staycation", "stay+vacation"),
    ("athleisure", "athletic+leisure"),
)


def generate() -> list[Candidate]:
    return generate_root_suffix_pool(
        "consumer_brands",
        "consumer_brands_roots.txt",
        "consumer_brands_suffixes.txt",
        "consumer_brands_compounds.txt",
        "consumer_brands_standalone.txt",
        blends=_BLENDS,
    )
