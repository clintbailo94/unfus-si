"""Transparent compounds and blends from curated AI vocabulary."""

from __future__ import annotations

from .common import make_candidate, read_terms, unique_candidates
from ..schema import Candidate


_BLEND_STEMS = {
    "neural": "neura",
    "cognitive": "cogni",
    "synthetic": "synth",
    "robotic": "robo",
    "autonomous": "auto",
    "inference": "infer",
    "sentient": "senti",
    "semantic": "sema",
    "synapse": "synap",
    "memory": "memo",
    "language": "lingua",
    "vision": "visi",
    "quantum": "quanta",
    "attention": "attenti",
    "embedding": "embed",
    "algorithm": "algo",
    "intelligent": "intelli",
    "transformer": "transfor",
}


def generate() -> list[Candidate]:
    concepts = read_terms("ai.txt")
    products = read_terms("ai_products.txt")
    candidates: list[Candidate] = []
    for concept in concepts:
        for product in products:
            label = concept + product
            candidate = make_candidate(
                label,
                "ai",
                "compound",
                f"{concept}+{product}",
                seed_quality=84,
            )
            if candidate is not None:
                candidates.append(candidate)

    for concept, stem in sorted(_BLEND_STEMS.items()):
        for product in products:
            label = stem + product
            candidate = make_candidate(
                label,
                "ai",
                "blend",
                f"{concept}+{product}",
                seed_quality=86,
            )
            if candidate is not None:
                candidates.append(candidate)
    return unique_candidates(candidates)
