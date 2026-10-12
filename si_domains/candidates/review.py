"""Deterministic random samples for human review of generated labels."""

from __future__ import annotations

import random
from collections.abc import Mapping

from .build import CATEGORIES, generate_all
from .schema import Candidate


def sample_by_category(
    count: int = 40,
    seed: int = 1,
    candidates: Mapping[str, list[Candidate]] | None = None,
) -> dict[str, list[Candidate]]:
    if count < 1:
        raise ValueError("sample count must be positive")
    generated = candidates if candidates is not None else generate_all()
    rng = random.Random(seed)
    return {
        category: rng.sample(generated[category], min(count, len(generated[category])))
        for category in CATEGORIES
    }


def render_sample(count: int = 40, seed: int = 1) -> str:
    generated = generate_all()
    samples = sample_by_category(count, seed, generated)
    sections: list[str] = []
    for category in CATEGORIES:
        sections.append(f"## {category} ({len(samples[category])} of {len(generated[category])})")
        sections.append("| domain | method | seed | tags | quality_score |")
        sections.append("| --- | --- | --- | --- | ---: |")
        for candidate in samples[category]:
            sections.append(
                f"| {candidate.domain_label}.si | {candidate.method} | {candidate.seed} | "
                f"{';'.join(candidate.tags)} | {candidate.quality_score} |"
            )
        sections.append("")
    return "\n".join(sections).rstrip() + "\n"
