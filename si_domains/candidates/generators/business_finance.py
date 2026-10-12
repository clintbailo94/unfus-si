"""Investing, banking, insurance, startup, and business-service compounds."""

from __future__ import annotations

from .common import generate_curated_compounds
from ..schema import Candidate


_BLENDS = (
    ("fintech", "finance+technology"),
    ("insurtech", "insurance+technology"),
    ("regtech", "regulation+technology"),
    ("wealthtech", "wealth+technology"),
    ("proptech", "property+technology"),
)


def generate() -> list[Candidate]:
    return generate_curated_compounds(
        "business_finance", "business_finance_concepts.txt", "business_finance_products.txt", blends=_BLENDS
    )
