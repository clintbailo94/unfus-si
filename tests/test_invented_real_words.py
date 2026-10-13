import random
from pathlib import Path

from si_domains.candidates.build import generate_all
from si_domains.candidates.generators import invented


ROOT = Path(__file__).parents[1]


def _known_real_word_sources():
    data = ROOT / "data"
    terms = set()
    for path in (data / "seeds").glob("*.txt"):
        terms.update(
            line.strip().casefold()
            for line in path.read_text(encoding="utf-8").splitlines()
            if line.strip() and not line.lstrip().startswith("#")
        )
    for path in data.glob("blocklist_*.txt"):
        terms.update(
            line.strip().casefold()
            for line in path.read_text(encoding="utf-8").splitlines()
            if line.strip() and not line.lstrip().startswith("#")
        )
    reviewed = data / "invented_real_words.txt"
    terms.update(
        line.strip().casefold()
        for line in reviewed.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    )
    return terms


def test_real_words_from_invented_are_reclassified_as_dictionary_candidates():
    generated = generate_all()
    dictionary = {row.domain_label: row for row in generated["dictionary"]}
    invented_labels = {row.domain_label for row in generated["invented"]}

    assert "final" in dictionary
    assert dictionary["final"].method == "invented-reclassified"
    assert dictionary["final"].seed == "fin+al"
    assert {"real_word", "phonotactic"}.issubset(dictionary["final"].tags)
    assert "final" not in invented_labels
    assert dictionary["palette"].method == "invented-reclassified"


def test_dictionary_quality_gate_drops_reclassified_seed_words(monkeypatch):
    monkeypatch.setattr(
        invented,
        "read_terms",
        lambda filename: ("eva",) if filename == "invented_stems.txt" else ("sion",),
    )

    assert not any(row.domain_label == "evasion" for row in invented.generate())


def test_invented_output_excludes_all_repository_and_reviewed_wordlist_matches():
    generated = generate_all()
    invented_labels = {row.domain_label for row in generated["invented"]}

    assert not invented_labels.intersection(_known_real_word_sources())


def test_fresh_seeded_sample_has_no_known_real_words():
    generated = generate_all()
    labels = [row.domain_label for row in generated["invented"]]
    seed = 20261013
    sample = random.Random(seed).sample(labels, 100)

    assert len(sample) == 100
    assert not set(sample).intersection(_known_real_word_sources())


def test_quality_blocklist_loader_accepts_crlf(tmp_path, monkeypatch):
    from si_domains.candidates import quality

    for filename in (
        "blocklist_brands.txt",
        "blocklist_offensive.txt",
        "blocklist_dictionary.txt",
        "blocklist_domain_hack_sources.txt",
        "blocklist_low_quality.txt",
    ):
        (tmp_path / filename).write_bytes(
            b"acmehouse\r\n" if filename == "blocklist_brands.txt" else b"\r\n"
        )
    monkeypatch.setattr(quality, "DATA_DIR", tmp_path)
    quality._read_terms.cache_clear()

    assert quality.evaluate_candidate("acmehouse", "invented") is None

    quality._read_terms.cache_clear()


def test_generator_seed_loader_accepts_crlf(tmp_path, monkeypatch):
    from si_domains.candidates.generators import common

    (tmp_path / "terms.txt").write_bytes(b"alpha\r\n# comment\r\nbeta\r\n")
    monkeypatch.setattr(common, "SEED_DIR", tmp_path)

    assert common.read_terms("terms.txt") == ("alpha", "beta")
