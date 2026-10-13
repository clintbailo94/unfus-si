"""Investing, banking, insurance, startup, and business-service compounds."""

from __future__ import annotations

from .common import generate_root_suffix_pool
from ..schema import Candidate


_BLENDS = (
    ("fintech", "finance+technology"),
    ("insurtech", "insurance+technology"),
    ("regtech", "regulation+technology"),
    ("wealthtech", "wealth+technology"),
    ("proptech", "property+technology"),
)


def generate() -> list[Candidate]:
    return generate_root_suffix_pool(
        "business_finance",
        "business_finance_roots.txt",
        "business_finance_suffixes.txt",
        "business_finance_compounds.txt",
        "business_finance_standalone.txt",
        blends=_BLENDS,
    )
