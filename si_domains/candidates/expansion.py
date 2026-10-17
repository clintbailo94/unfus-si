"""Candidate expansion generator creating over 20,000 quality-gated .si domain candidates."""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Sequence

from si_domains.candidates.quality import evaluate_candidate
from si_domains.candidates.schema import Candidate, CSV_FIELDS
from si_domains.config import DATA_DIR, OUTPUT_DIR


EXPANDED_CANDIDATES_PATH = DATA_DIR / "candidates_expanded.csv"


# 1. Fintech & Financial Services Terms
FINTECH_PREFIXES = (
    "pay", "cash", "coin", "fund", "flow", "lend", "yield", "mint", "vault",
    "fiat", "swap", "fin", "asset", "stake", "hedge", "trade", "vest", "wealth",
    "credit", "apex", "prime", "micro", "omni", "trust", "loan", "settle", "remit",
    "spend", "wallet", "ledger", "bank", "risk", "cap", "rate", "bond", "forex",
)
FINTECH_SUFFIXES = (
    "hub", "desk", "flow", "pay", "link", "port", "base", "grid", "wire",
    "gate", "pass", "loop", "mesh", "pool", "node", "core", "line", "spot",
    "path", "zone", "nest", "mark", "view", "byte", "stack", "vault", "cast",
    "wave", "sync", "mint", "dock", "yard", "lift", "beam", "rail", "pace",
)

# 2. SaaS Action Verbs & Verifiable Cloud Concepts
SAAS_VERBS = (
    "deploy", "scale", "launch", "automate", "sync", "trace", "monitor", "parse",
    "track", "notify", "stream", "index", "route", "route", "render", "compile",
    "verify", "audit", "scrape", "search", "cache", "store", "fetch", "patch",
    "debug", "backup", "assert", "mutate", "format", "scaffold", "bundle", "host",
    "publish", "ingest", "resolve", "trigger", "filter", "query", "pipe",
)
SAAS_NOUNS = (
    "app", "box", "kit", "lab", "hub", "flow", "ops", "api", "bot", "run",
    "dev", "log", "pro", "sys", "net", "dot", "pod", "cli", "sdk", "env",
    "stack", "core", "node", "tool", "work", "grid", "gate", "view", "mesh",
)

# 3. Health, Wellness & Biotech Terms
HEALTH_ROOTS = (
    "bio", "vita", "care", "cure", "heal", "medi", "gene", "cell", "nano",
    "pulse", "thera", "soma", "dent", "derm", "opti", "diet", "fit", "pure",
    "mind", "calm", "zen", "well", "glow", "life", "aura", "vibe", "vital",
    "meta", "physio", "synap", "flora", "cardio", "spine", "sleep", "soothe",
)
HEALTH_SUFFIXES = (
    "lab", "care", "hub", "fit", "well", "glow", "med", "cure", "life",
    "pure", "zone", "nest", "spa", "form", "path", "line", "wave", "sync",
    "box", "base", "root", "feed", "view", "link", "post", "room", "yard",
)

# 4. Slovenian Business & Innovation Keywords
SLOVENIAN_WORDS = (
    "posel", "uspeh", "znanje", "hitro", "pamet", "svet", "delo", "vizija",
    "tocka", "mreza", "prostor", "resitev", "oblaki", "zagon", "napredek", "prihodnost",
    "ideja", "vrednost", "kapital", "pretok", "trgovina", "uprava", "sodelovanje", "trg",
    "vodstvo", "sola", "akademija", "institut", "center", "vozlisce", "odprto", "pametno",
    "novost", "ustvarjalno", "napredno", "skupnost", "povezava", "domace", "lokalno", "globalno",
    "zdravje", "okus", "lepota", "narava", "energija", "okolje", "zeleno", "cisto",
)

# 5. Two-Word Modern Brandables
BRANDABLE_A = (
    "alpha", "beta", "meta", "omni", "hyper", "ultra", "cyber", "synapse", "strata",
    "vortex", "nexus", "prism", "vector", "apex", "orbit", "zenith", "stellar", "polar",
    "flux", "quantum", "solaris", "aegis", "lumina", "spectra", "chrono", "aero", "terra",
    "krypto", "helios", "ignis", "zephyr", "titan", "hydra", "orion", "nova", "pulsar",
)
BRANDABLE_B = (
    "mind", "logic", "craft", "forge", "works", "shift", "wave", "space", "field",
    "scale", "stack", "point", "realm", "pulse", "drive", "stride", "spark", "track",
    "phase", "surge", "trend", "stride", "forge", "scout", "pilot", "guide", "guard",
)

# 6. .si Domain Hacks (English words ending in -cy, -sy, -see, -si sounds)
HACK_WORDS = (
    # Words ending in -cy -> label ends in c (or dropped cy with hack)
    ("accura", "accuracy", "hack-suffix"),
    ("adequa", "adequacy", "hack-suffix"),
    ("advoca", "advocacy", "hack-suffix"),
    ("agen", "agency", "hack-suffix"),
    ("automa", "automacy", "hack-suffix"),
    ("bankrupt", "bankruptcy", "hack-suffix"),
    ("clemen", "clemency", "hack-suffix"),
    ("competen", "competency", "hack-suffix"),
    ("consisten", "consistency", "hack-suffix"),
    ("curren", "currency", "hack-suffix"),
    ("decen", "decency", "hack-suffix"),
    ("delica", "delicacy", "hack-suffix"),
    ("efficien", "efficiency", "hack-suffix"),
    ("emergen", "emergency", "hack-suffix"),
    ("frequen", "frequency", "hack-suffix"),
    ("illitera", "illiteracy", "hack-suffix"),
    ("infan", "infancy", "hack-suffix"),
    ("invalida", "invalidacy", "hack-suffix"),
    ("legita", "legitimacy", "hack-suffix"),
    ("litera", "literacy", "hack-suffix"),
    ("luna", "lunacy", "hack-suffix"),
    ("norma", "normalcy", "hack-suffix"),
    ("occupan", "occupancy", "hack-suffix"),
    ("politi", "policy", "hack-suffix"),
    ("poten", "potency", "hack-suffix"),
    ("priva", "privacy", "hack-suffix"),
    ("secres", "secrecy", "hack-suffix"),
    ("tenden", "tendency", "hack-suffix"),
    ("urgency", "urgency", "hack-suffix"),
    ("vacan", "vacancy", "hack-suffix"),
    # Additional sound hacks
    ("easie", "easies", "hack-suffix"),
    ("fantas", "fantasy", "hack-suffix"),
    ("courtes", "courtesy", "hack-suffix"),
    ("ecstas", "ecstasy", "hack-suffix"),
    ("jealous", "jealousy", "hack-suffix"),
    ("lepros", "leprosy", "hack-suffix"),
    ("pleuris", "pleurisy", "hack-suffix"),
    ("hypocris", "hypocrisy", "hack-suffix"),
    ("idiosyncras", "idiosyncrasy", "hack-suffix"),
)


def generate_expanded_candidates(target_count: int = 21000) -> list[Candidate]:
    """Generate clean, unique, quality-evaluated candidates to expand candidate pool."""
    candidates: list[Candidate] = []
    seen: set[str] = set()

    # Load existing candidates first
    existing_file = DATA_DIR / "candidates.csv"
    if existing_file.is_file():
        with existing_file.open("r", encoding="utf-8-sig") as f:
            for row in csv.DictReader(f):
                lbl = row.get("domain_label", "").strip().lower()
                if lbl and lbl not in seen:
                    seen.add(lbl)
                    candidates.append(
                        Candidate(
                            domain_label=lbl,
                            category=row.get("category", "dictionary"),
                            method=row.get("method", "existing"),
                            seed=row.get("seed", lbl),
                            tags=tuple(sorted(t.strip() for t in row.get("tags", "").split(",") if t.strip())),
                            quality_score=int(row.get("quality_score", 75)),
                        )
                    )

    # 1. Fintech & Financial
    for p in FINTECH_PREFIXES:
        for s in FINTECH_SUFFIXES:
            lbl = f"{p}{s}"
            if lbl in seen:
                continue
            score = evaluate_candidate(lbl, "business_finance")
            if score is not None:
                seen.add(lbl)
                candidates.append(Candidate(lbl, "business_finance", "compound", f"{p}+{s}", ("fintech",), score))

    # 2. SaaS Verbs & Tech Action
    for v in SAAS_VERBS:
        for n in SAAS_NOUNS:
            lbl = f"{v}{n}"
            if lbl in seen:
                continue
            score = evaluate_candidate(lbl, "technology")
            if score is not None:
                seen.add(lbl)
                candidates.append(Candidate(lbl, "technology", "compound", f"{v}+{n}", ("saas",), score))

    # 3. Health, Wellness & Biotech
    for r in HEALTH_ROOTS:
        for s in HEALTH_SUFFIXES:
            lbl = f"{r}{s}"
            if lbl in seen:
                continue
            score = evaluate_candidate(lbl, "health_science")
            if score is not None:
                seen.add(lbl)
                candidates.append(Candidate(lbl, "health_science", "compound", f"{r}+{s}", ("health",), score))

    # 4. Slovenian Business & Innovation Keywords
    for w in SLOVENIAN_WORDS:
        if w not in seen:
            score = evaluate_candidate(w, "dictionary")
            if score is not None:
                seen.add(w)
                candidates.append(Candidate(w, "dictionary", "dictionary", w, ("slovenian",), score))
        # Slovenian compound brandables
        for suf in ("hub", "pro", "lab", "net", "box", "dom", "vrh"):
            lbl = f"{w}{suf}"
            if lbl not in seen:
                score = evaluate_candidate(lbl, "business_finance")
                if score is not None:
                    seen.add(lbl)
                    candidates.append(Candidate(lbl, "business_finance", "compound", f"{w}+{suf}", ("slovenian",), score))

    # 5. Two-Word Brandables
    for a in BRANDABLE_A:
        for b in BRANDABLE_B:
            lbl = f"{a}{b}"
            if lbl in seen:
                continue
            score = evaluate_candidate(lbl, "invented")
            if score is not None:
                seen.add(lbl)
                candidates.append(Candidate(lbl, "invented", "compound", f"{a}+{b}", ("brandable",), score))

    # 6. .si Domain Hacks
    for lbl, seed, method in HACK_WORDS:
        if lbl in seen:
            continue
        score = evaluate_candidate(lbl, "domain_hacks", seed=seed)
        if score is not None:
            seen.add(lbl)
            candidates.append(Candidate(lbl, "domain_hacks", method, seed, ("hack",), score))

    # 7. Additional Systematic AI & Tech Combinations to ensure >= target_count
    ai_tech_heads = (
        "ai", "ml", "bot", "auto", "cog", "deep", "algo", "meta", "syn", "neo",
        "hyper", "tensor", "prompt", "model", "logic", "agent", "flow", "core",
        "byte", "bit", "data", "cloud", "pixel", "mesh", "graph", "stream",
        "cyber", "vector", "signal", "stat", "math", "optic", "sonar", "laser",
    )
    ai_tech_tails = (
        "mind", "lab", "hub", "flow", "craft", "work", "base", "grid", "wire",
        "port", "link", "gate", "node", "path", "zone", "nest", "view", "byte",
        "stack", "mark", "pulse", "line", "spot", "shift", "scale", "track",
        "scan", "desk", "room", "sync", "mint", "dock", "yard", "loop", "mesh",
    )
    for h in ai_tech_heads:
        for t in ai_tech_tails:
            lbl = f"{h}{t}"
            if lbl in seen:
                continue
            score = evaluate_candidate(lbl, "ai")
            if score is not None:
                seen.add(lbl)
                candidates.append(Candidate(lbl, "ai", "compound", f"{h}+{t}", ("ai_tech",), score))

    # 8. Modern Verbs and Nouns
    modern_stems = (
        "build", "stack", "ship", "launch", "craft", "mint", "host", "test",
        "code", "push", "pull", "ping", "post", "link", "chat", "talk", "vote",
        "rank", "rate", "sort", "find", "seek", "peek", "look", "meet", "join",
        "share", "send", "give", "earn", "save", "spend", "plan", "book", "rent",
    )
    for stem in modern_stems:
        for suf in ("hub", "app", "box", "kit", "lab", "flow", "ops", "pro", "sys", "net", "ly", "io"):
            lbl = f"{stem}{suf}"
            if lbl in seen:
                continue
            score = evaluate_candidate(lbl, "technology")
            if score is not None:
                seen.add(lbl)
                candidates.append(Candidate(lbl, "technology", "compound", f"{stem}+{suf}", ("modern_saas",), score))

    # 9. Syllable combinations for pronounceable brandables
    onsets = ("ba", "be", "bi", "bo", "bu", "ca", "co", "cu", "da", "de", "di", "do", "du",
              "fa", "fe", "fi", "fo", "fu", "ga", "ge", "gi", "go", "gu", "ha", "he", "hi", "ho",
              "ka", "ke", "ki", "ko", "ku", "la", "le", "li", "lo", "lu", "ma", "me", "mi", "mo", "mu",
              "na", "ne", "ni", "no", "nu", "pa", "pe", "pi", "po", "pu", "ra", "re", "ri", "ro", "ru",
              "sa", "se", "si", "so", "su", "ta", "te", "ti", "to", "tu", "va", "ve", "vi", "vo", "vu",
              "za", "ze", "zi", "zo", "zu")
    codas = ("ba", "da", "fa", "ga", "ka", "la", "ma", "na", "pa", "ra", "sa", "ta", "va", "za",
             "bo", "do", "fo", "go", "ko", "lo", "mo", "no", "po", "ro", "so", "to", "vo", "zo",
             "be", "de", "fe", "ge", "ke", "le", "me", "ne", "pe", "re", "se", "te", "ve", "ze")
    for o in onsets:
        for c in codas:
            for s in ("x", "r", "n", "m", "s", "t", "l", ""):
                lbl = f"{o}{c}{s}"
                if lbl in seen:
                    continue
                score = evaluate_candidate(lbl, "invented")
                if score is not None:
                    seen.add(lbl)
                    candidates.append(Candidate(lbl, "invented", "blend", f"{o}+{c}", ("pronounceable",), score))
                if len(candidates) >= target_count + 500:
                    break
            if len(candidates) >= target_count + 500:
                break
        if len(candidates) >= target_count + 500:
            break

    return sorted(candidates, key=lambda c: c.domain_label)


def write_expanded_candidates(
    output_path: Path | str = EXPANDED_CANDIDATES_PATH,
    target_count: int = 21000,
) -> int:
    """Write generated expanded candidates to CSV."""
    candidates = generate_expanded_candidates(target_count=target_count)
    p = Path(output_path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(c.to_row() for c in candidates)
    return len(candidates)
