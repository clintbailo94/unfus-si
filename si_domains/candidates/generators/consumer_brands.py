"""Fashion, travel, entertainment, lifestyle, education, and commerce compounds."""

from __future__ import annotations

from .common import generate_curated_compounds
from ..schema import Candidate


_BLENDS = (
    ("edtech", "education+technology"),
    ("ecommerce", "electronic+commerce"),
    ("staycation", "stay+vacation"),
    ("athleisure", "athletic+leisure"),
)


def generate() -> list[Candidate]:
    return generate_curated_compounds(
        "consumer_brands",
        "consumer_brands_concepts.txt",
        "consumer_brands_products.txt",
        "consumer_brands_pairs.txt",
        blends=_BLENDS,
    )
