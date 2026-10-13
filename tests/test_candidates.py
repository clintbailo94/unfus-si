from pathlib import Path

import pytest

from si_domains.candidates.quality import evaluate_candidate
from si_domains.candidates.build import (
    CATEGORIES,
    T3_MIN_CANDIDATES,
    _remove_trivial_plurals,
    generate_all,
)
from si_domains.candidates.generators.domain_hacks import _VOICED_SY, generate as generate_domain_hacks
from si_domains.candidates.schema import Candidate


@pytest.mark.parametrize(
    "label,category,accepted",
    [
        ("novara", "invented", True),
        ("ai", "short", True),
        ("anthropic", "ai", False),
        ("myopenaiidea", "ai", False),
        ("si", "short", False),
        ("rs", "short", False),
        ("112", "short", False),
        ("naïve", "dictionary", False),
        ("muka", "short", False),
        ("two-words", "dictionary", False),
        ("aabbb", "invented", False),
        ("zzzzzz", "invented", False),
        ("123", "dictionary", False),
        ("a9", "short", False),
        ("brrr", "invented", False),
        ("monene", "invented", False),
        ("moronic", "dictionary", False),
        ("cassette", "dictionary", True),
        ("quantum", "dictionary", True),
        ("insulin", "dictionary", True),
        ("dynasty", "dictionary", True),
        ("personality", "dictionary", True),
        ("neuralprocessing", "ai", True),
        ("neuralprocessingx", "ai", False),
    ],
)
def test_quality_gate_accepts_only_safe_ascii_brandable_labels(label, category, accepted):
    score = evaluate_candidate(label, category)

    assert (score is not None) is accepted
    if score is not None:
        assert 0 <= score <= 100
        assert score == evaluate_candidate(label, category)


def test_short_abbreviations_and_brand_components_are_checked():
    assert evaluate_candidate("ml", "short", tags=("abbr",)) is not None
    assert evaluate_candidate("po", "short") is not None
    assert evaluate_candidate("zara", "short", tags=("cvcv",)) is None
    assert evaluate_candidate("agentgpt", "ai", seed="agent+gpt") is None


@pytest.mark.parametrize(
    "label",
    [
        "bestial",
        "bigoted",
        "bigotry",
        "bribery",
        "carnage",
        "carrion",
        "boorish",
        "buffoon",
        "anguish",
        "ailment",
        "amateur",
        "parasite",
        "conceit",
        "cynical",
        "frailty",
        "arsenic",
        "cyanide",
        "macabre",
        "senile",
        "failing",
        "amoral",
        "unarmed",
        "wartime",
        "missile",
        "militia",
        "tobacco",
        "foreleg",
        "toenail",
        "manhole",
        "burial",
        "remains",
        "rueful",
        "libelous",
        "leaden",
        "runaway",
        "undoing",
        "accuser",
        "desolate",
        "evasion",
        "evasive",
        "futility",
        "jealous",
        "tirade",
        "polygamy",
    ],
)
def test_dictionary_gate_rejects_negative_or_weak_standalone_words(label):
    assert evaluate_candidate(label, "dictionary") is None


def test_dictionary_generator_omits_semantically_rejected_terms():
    rejected = {
        "bestial",
        "bigoted",
        "bigotry",
        "bribery",
        "carnage",
        "carrion",
        "boorish",
        "buffoon",
        "anguish",
        "ailment",
        "amateur",
        "parasite",
        "conceit",
        "cynical",
        "frailty",
        "arsenic",
        "cyanide",
        "macabre",
        "senile",
        "failing",
        "amoral",
        "unarmed",
        "wartime",
        "missile",
        "militia",
        "tobacco",
        "foreleg",
        "toenail",
        "manhole",
        "burial",
        "remains",
        "rueful",
        "libelous",
        "leaden",
        "runaway",
        "undoing",
        "accuser",
        "desolate",
        "evasion",
        "evasive",
        "futility",
        "jealous",
        "tirade",
        "polygamy",
    }

    assert not rejected.intersection(row.domain_label for row in generate_all()["dictionary"])


def test_dictionary_seeds_are_semantically_pruned_without_losing_technical_words():
    data = Path(__file__).parents[1] / "data"
    words = {
        line.strip().casefold()
        for line in (data / "seeds" / "dictionary.txt").read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    }
    rejected = {
        line.strip().casefold()
        for line in (data / "blocklist_low_quality.txt").read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    }

    assert not words.intersection(rejected)
    assert not {"dealing", "fatigue", "rumored"}.intersection(words)
    assert not {
        "accuser",
        "desolate",
        "evasion",
        "evasive",
        "futility",
        "jealous",
        "tirade",
        "polygamy",
    }.intersection(words)
    assert {"insulin", "quantum", "vaccine"}.issubset(words)


@pytest.mark.parametrize(
    "source",
    [
        "idiocy",
        "lunacy",
        "contumacy",
        "plangency",
        "regeneracy",
        "mendicancy",
        "baronetcy",
        "vehemency",
        "infrequency",
        "inadequacy",
        "antsy",
        "argosy",
        "articulacy",
        "autocracy",
        "belligerency",
        "blatancy",
        "bossy",
        "bureaucracy",
        "codependency",
        "complacency",
        "confederacy",
        "conspiracy",
        "controversy",
        "counterinsurgency",
        "decadency",
        "deficiency",
        "delinquency",
        "deviancy",
        "discourtesy",
        "discrepancy",
        "exigency",
        "expediency",
        "flippancy",
        "flossy",
        "gassy",
        "gypsy",
        "hesitancy",
        "hypocrisy",
        "illiteracy",
        "innumeracy",
        "insolvency",
        "insufficiency",
        "insurgency",
        "inefficacy",
        "inexpediency",
        "intestacy",
        "inveteracy",
        "jealousy",
        "kleptocracy",
        "messy",
        "militancy",
        "minstrelsy",
        "noisy",
        "nosy",
        "pacy",
        "piracy",
        "plutocracy",
        "prissy",
        "profligacy",
        "prosy",
        "queasy",
        "rampancy",
        "redundancy",
        "stridency",
        "supremacy",
        "theocracy",
        "transiency",
        "vagrancy",
        "epilepsy",
        "narcolepsy",
        "chancy",
        "cutesy",
        "curacy",
        "colonelcy",
        "episcopacy",
        "excellency",
        "flamboyancy",
        "immunodeficiency",
        "inarticulacy",
        "inclemency",
        "inconsistency",
        "inconstancy",
        "illegitimacy",
        "lambency",
        "lieutenancy",
        "magistracy",
        "paramountcy",
        "poesy",
        "poignancy",
        "prelacy",
        "stagnancy",
        "succulency",
        "trenchancy",
        "heresy",
        "papacy",
        "lacy",
        "racy",
        "juicy",
        "citrusy",
        "geodesy",
        "primacy",
    ],
)
def test_domain_hacks_exclude_semantically_weak_sources(source):
    assert not any(
        candidate.method == "hack-suffix" and candidate.seed == source
        for candidate in generate_domain_hacks()
    )


@pytest.mark.parametrize("source", ["posy", "newsy", "tansy", "teensy", "outdoorsy", "woodsy"])
def test_domain_hacks_reject_voiced_sy_sources(source):
    assert source in _VOICED_SY
    seeds = {
        line.strip().casefold()
        for line in (Path(__file__).parents[1] / "data" / "seeds" / "domain_hacks.txt")
        .read_text(encoding="utf-8")
        .splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    }
    assert source in seeds
    assert not any(
        candidate.method == "hack-suffix" and candidate.seed == source
        for candidate in generate_domain_hacks()
    )


def test_rejecting_a_hack_source_does_not_globally_block_its_short_label():
    assert evaluate_candidate("la", "short") is not None
    assert evaluate_candidate("luna", "short") is not None
    assert evaluate_candidate("luna", "domain_hacks", seed="lunacy") is None


def test_lunacy_is_pruned_as_a_domain_hack_source():
    seeds = {
        line.strip().casefold()
        for line in (Path(__file__).parents[1] / "data" / "seeds" / "domain_hacks.txt")
        .read_text(encoding="utf-8")
        .splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    }

    assert "lunacy" not in seeds
    assert not any(
        candidate.method == "hack-suffix" and candidate.seed == "lunacy"
        for candidate in generate_domain_hacks()
    )


@pytest.mark.parametrize(
    "label,accepted",
    [("bim", False), ("nava", True), ("malorivae", True), ("malorivana", False)],
)
def test_invented_names_must_be_four_to_nine_characters(label, accepted):
    assert (evaluate_candidate(label, "invented") is not None) is accepted


def test_trivial_plural_pair_is_removed_across_primary_categories():
    singular = Candidate("rune", "dictionary", "dictionary", "rune", (), 80)
    plural = Candidate("runes", "short", "short", "runes", ("word",), 90)

    assert _remove_trivial_plurals([singular, plural]) == [plural]


def test_trivial_plural_pair_is_removed_within_same_category():
    singular = Candidate("garden", "dictionary", "dictionary", "garden", (), 80)
    plural = Candidate("gardens", "dictionary", "dictionary", "gardens", (), 90)

    assert _remove_trivial_plurals([singular, plural]) == [plural]


def test_trivial_compound_plural_pair_is_removed_across_new_categories():
    singular = Candidate("marketflow", "technology", "compound", "market+flow", (), 78)
    plural = Candidate("marketsflow", "business_finance", "compound", "markets+flow", (), 84)

    assert _remove_trivial_plurals([singular, plural]) == [plural]


def test_trivial_y_plural_pair_is_removed_across_categories():
    singular = Candidate("industrylab", "technology", "compound", "industry+lab", (), 78)
    plural = Candidate("industrieslab", "business_finance", "compound", "industries+lab", (), 84)

    assert _remove_trivial_plurals([singular, plural]) == [plural]


def test_plural_dedup_does_not_strip_s_from_hack_or_invented_sources():
    pairs = [
        (
            Candidate("ches", "domain_hacks", "hack-suffix", "chessy", (), 80),
            Candidate("chess", "domain_hacks", "hack-suffix", "chessy", (), 90),
        ),
        (
            Candidate("chao", "invented", "invented", "cha+o", (), 80),
            Candidate("chaos", "invented", "invented", "cha+os", (), 90),
        ),
    ]

    assert _remove_trivial_plurals([candidate for pair in pairs for candidate in pair]) == [
        candidate for pair in pairs for candidate in pair
    ]


def test_generators_are_deterministic_unique_and_meet_documented_counts():
    first = generate_all()
    second = generate_all()

    assert CATEGORIES == (
        "domain_hacks",
        "ai",
        "short",
        "dictionary",
        "invented",
        "technology",
        "business_finance",
        "health_science",
        "consumer_brands",
        "emerging_industries",
    )
    assert first == second
    assert len({row.domain_label for rows in first.values() for row in rows}) == sum(map(len, first.values()))
    labels = {row.domain_label for rows in first.values() for row in rows}
    assert set(T3_MIN_CANDIDATES) == set(CATEGORIES[:5])
    assert "bird" in labels
    assert "birds" not in labels
    assert "accura" in {row.domain_label for row in first["domain_hacks"]}
    assert "muka" not in labels
    assert len(first["domain_hacks"]) == T3_MIN_CANDIDATES["domain_hacks"]
    assert all(len(first[category]) >= minimum for category, minimum in T3_MIN_CANDIDATES.items())


def test_t4_categories_share_the_compound_length_policy():
    t4_categories = (
        "technology",
        "business_finance",
        "health_science",
        "consumer_brands",
        "emerging_industries",
    )

    assert CATEGORIES == (
        "domain_hacks",
        "ai",
        "short",
        "dictionary",
        "invented",
        *t4_categories,
    )
    assert all(evaluate_candidate("containerstack", category) is not None for category in t4_categories)
    assert all(evaluate_candidate("immunologyworks", category) is None for category in t4_categories)
    assert all(evaluate_candidate("infosecuritymesh", category) is None for category in t4_categories)
    assert all(evaluate_candidate("infosecuritymeshes", category) is None for category in t4_categories)


def test_t4_generators_are_substantive_and_keep_global_pool_above_hard_minimum():
    generated = generate_all()
    labels = [row.domain_label for rows in generated.values() for row in rows]

    assert all(generated[category] for category in CATEGORIES[5:])
    assert all(len(generated[category]) >= 250 for category in CATEGORIES[5:])
    assert len(labels) >= 5_000
    assert len(labels) == len(set(labels))
    assert all(generated[category] for category in CATEGORIES)
    assert all(len(row.domain_label) <= 14 for category in CATEGORIES[5:] for row in generated[category])


def test_t4_reviewed_pairs_exclude_tautologies_and_use_short_sector_roots():
    from si_domains.candidates.generators.common import read_reviewed_compounds

    generated = generate_all()
    labels = {row.domain_label for rows in generated.values() for row in rows}
    reviewed_pairs = {
        (category, f"{root}+{suffix}")
        for category in CATEGORIES[5:]
        for root, suffix in read_reviewed_compounds(
            f"{category}_roots.txt",
            f"{category}_suffixes.txt",
            f"{category}_compounds.txt",
        )
    }
    rejected_pairs = {
        ("emerging_industries", "propulsion+engine"),
        ("emerging_industries", "agriculture+lab"),
        ("emerging_industries", "agriculture+hub"),
        ("emerging_industries", "agriculture+grid"),
        ("emerging_industries", "desalination+ops"),
        ("health_science", "tumor+assay"),
        ("health_science", "tumor+clinic"),
        ("health_science", "tumor+therapy"),
        ("health_science", "rehab+therapy"),
        ("health_science", "neuro+therapy"),
        ("health_science", "neuron+therapy"),
        ("health_science", "pharma+therapy"),
        ("health_science", "pharma+clinic"),
        ("health_science", "dosage+therapy"),
        ("health_science", "dosage+clinic"),
        ("health_science", "antigen+trial"),
        ("health_science", "stroma+trial"),
        ("health_science", "chromatin+cell"),
        ("health_science", "dermatology+works"),
        ("health_science", "derma+works"),
        ("health_science", "gynecology+atlas"),
        ("health_science", "gyn+atlas"),
        ("health_science", "nephrology+track"),
        ("health_science", "nephro+track"),
        ("business_finance", "bookkeeping+works"),
        ("business_finance", "bookkeeping+tax"),
        ("business_finance", "underwriting+ops"),
        ("consumer_brands", "academy+class"),
        ("consumer_brands", "academy+school"),
        ("consumer_brands", "campus+course"),
        ("consumer_brands", "tutoring+course"),
        ("consumer_brands", "cruise+stay"),
        ("technology", "index+hub"),
        ("emerging_industries", "agri+ops"),
        ("emerging_industries", "agri+works"),
        ("emerging_industries", "desal+ops"),
        ("emerging_industries", "aerospace+grid"),
        ("emerging_industries", "hydro+hub"),
        ("emerging_industries", "additive+grid"),
        ("emerging_industries", "cellulose+grid"),
        ("emerging_industries", "autopilot+drive"),
        ("emerging_industries", "fission+engine"),
    }
    reviewed_short_roots = {
        ("health_science", "nephro+lab"),
        ("health_science", "derma+lab"),
        ("health_science", "hemo+scan"),
        ("health_science", "physio+lab"),
        ("health_science", "gyn+clinic"),
        ("emerging_industries", "agri+lab"),
        ("emerging_industries", "desal+grid"),
    }

    assert not rejected_pairs.intersection(reviewed_pairs)
    assert reviewed_short_roots <= reviewed_pairs
    assert {"nephrolab", "dermalab", "hemoscan", "physiolab", "gynclinic", "agrilab", "desalgrid"} <= labels
    assert not {
        "propulsionengine",
        "agriculturelab",
        "agriculturehub",
        "tumorassay",
        "rehabtherapy",
        "dermatologyworks",
        "dermaworks",
        "gynecologyatlas",
        "gynatlas",
        "nephrologytrack",
        "nephrotrack",
        "bookkeepingworks",
        "underwritingops",
        "desalinationops",
        "pharmatherapy",
        "dosagetherapy",
        "antigentrial",
        "stromatrial",
        "chromatincell",
        "tumorclinic",
        "tutoringcourse",
        "campuscourse",
        "academyclass",
        "academyschool",
        "aerospacegrid",
        "hydrohub",
        "additivegrid",
        "cellulosegrid",
        "dosageclinic",
        "pharmaclinic",
        "tumortherapy",
        "neurotherapy",
        "neurontherapy",
        "cruisestay",
        "indexhub",
        "autopilotdrive",
        "fissionengine",
    }.intersection(labels)


def test_global_dedup_keeps_the_first_primary_category_and_other_category_tags(monkeypatch):
    import si_domains.candidates.build as build

    primary = Candidate("precisionlab", "health_science", "compound", "precision+lab", (), 82)
    secondary = Candidate("precisionlab", "emerging_industries", "compound", "precision+lab", (), 79)
    generators = {category: (lambda: []) for category in CATEGORIES}
    generators["health_science"] = lambda: [primary]
    generators["emerging_industries"] = lambda: [secondary]
    monkeypatch.setattr(build, "_GENERATORS", generators)

    generated = build.generate_all()
    rows = {row.domain_label: row for values in generated.values() for row in values}

    precision_lab = rows["precisionlab"]
    assert precision_lab.category == "health_science"
    assert "emerging_industries" in precision_lab.tags
    assert precision_lab.tags == tuple(sorted(set(precision_lab.tags)))
    assert len(rows) == sum(map(len, generated.values()))


def test_sample_review_exclusions_remove_specific_root_product_pairs():
    from si_domains.candidates.build import _GENERATORS
    from si_domains.candidates.generators.common import read_candidate_pair_blocks

    blocked = read_candidate_pair_blocks()
    for category in CATEGORIES[5:]:
        seeds = {row.seed for row in _GENERATORS[category]()}
        assert not {seed for blocked_category, seed in blocked if blocked_category == category} & seeds


def test_seed_one_sample_review_excludes_weak_sector_pairings():
    reviewed_pairs = {
        ("technology", "region+harbor"),
        ("technology", "cache+learn"),
        ("technology", "deploy+devops"),
        ("technology", "backup+proof"),
        ("technology", "device+camera"),
        ("business_finance", "service+seed"),
        ("business_finance", "sales+vendor"),
        ("business_finance", "debit+cash"),
        ("business_finance", "estate+auto"),
        ("health_science", "study+group"),
        ("health_science", "brain+vital"),
        ("health_science", "therapy+well"),
        ("consumer_brands", "photo+ticket"),
        ("consumer_brands", "home+travel"),
        ("consumer_brands", "market+cook"),
        ("consumer_brands", "tour+hotel"),
        ("consumer_brands", "hotel+tour"),
        ("emerging_industries", "renewable+crop"),
        ("emerging_industries", "food+harbor"),
        ("emerging_industries", "marine+space"),
        ("emerging_industries", "fuel+energy"),
        ("consumer_brands", "curriculum+course"),
    }
    generated_pairs = {
        (candidate.category, candidate.seed)
        for rows in generate_all().values()
        for candidate in rows
        if candidate.category in CATEGORIES[5:] and candidate.method == "compound"
    }

    assert not reviewed_pairs.intersection(generated_pairs)


def test_t4_generated_compounds_are_explicitly_pair_whitelisted():
    from si_domains.candidates.generators.common import read_reviewed_compounds

    generated_pairs = {
        (candidate.category, candidate.seed)
        for rows in generate_all().values()
        for candidate in rows
        if candidate.category in CATEGORIES[5:] and candidate.method == "compound"
    }
    reviewed_pairs = set()
    for category in CATEGORIES[5:]:
        pairs = read_reviewed_compounds(
            f"{category}_roots.txt",
            f"{category}_suffixes.txt",
            f"{category}_compounds.txt",
        )
        reviewed_pairs.update((category, f"{root}+{suffix}") for root, suffix in pairs)

    assert generated_pairs
    assert generated_pairs <= reviewed_pairs


def test_t4_small_root_suffix_vocabularies_and_explicit_compounds():
    from si_domains.candidates.generators.common import (
        read_reviewed_compounds,
        read_standalone_roots,
        read_terms,
    )

    blocked = {
        line.strip().casefold()
        for line in (Path(__file__).parents[1] / "data" / "blocklist_generic_candidate_terms.txt")
        .read_text(encoding="utf-8")
        .splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    }
    for category in CATEGORIES[5:]:
        roots = read_terms(f"{category}_roots.txt")
        suffixes = read_terms(f"{category}_suffixes.txt")
        compounds = read_reviewed_compounds(
            f"{category}_roots.txt",
            f"{category}_suffixes.txt",
            f"{category}_compounds.txt",
        )
        standalone = read_standalone_roots(
            f"{category}_roots.txt",
            f"{category}_standalone.txt",
        )

        assert 40 <= len(roots) <= 80
        assert 12 <= len(suffixes) <= 20
        assert set(roots).isdisjoint(suffixes)
        assert not blocked.intersection(roots)
        assert not blocked.intersection(suffixes)
        assert set(standalone) <= set(roots)
        assert compounds
        assert all(suffix not in root and root not in suffix for root, suffix in compounds)


def test_reviewed_compound_reader_rejects_unknown_and_generic_components(tmp_path, monkeypatch):
    import si_domains.candidates.generators.common as common

    (tmp_path / "roots.txt").write_text("genome\n", encoding="utf-8")
    (tmp_path / "suffixes.txt").write_text("lab\n", encoding="utf-8")
    (tmp_path / "compounds.txt").write_text("genome+lab\n", encoding="utf-8")
    (tmp_path / "standalone.txt").write_text("genome\n", encoding="utf-8")
    (tmp_path / "generic.txt").write_text("zone\n", encoding="utf-8")
    monkeypatch.setattr(common, "SEED_DIR", tmp_path)
    monkeypatch.setattr(common, "_GENERIC_TERMS", tmp_path / "generic.txt", raising=False)

    assert common.read_reviewed_compounds(
        "roots.txt", "suffixes.txt", "compounds.txt"
    ) == (("genome", "lab"),)
    assert common.read_standalone_roots("roots.txt", "standalone.txt") == ("genome",)

    (tmp_path / "compounds.txt").write_text("genome+desk\n", encoding="utf-8")
    with pytest.raises(ValueError, match="unknown root or suffix"):
        common.read_reviewed_compounds("roots.txt", "suffixes.txt", "compounds.txt")

    (tmp_path / "roots.txt").write_text("zone\n", encoding="utf-8")
    (tmp_path / "compounds.txt").write_text("zone+lab\n", encoding="utf-8")
    with pytest.raises(ValueError, match="generic component"):
        common.read_reviewed_compounds("roots.txt", "suffixes.txt", "compounds.txt")


def test_reviewed_compound_reader_rejects_repeated_domain_component(tmp_path, monkeypatch):
    import si_domains.candidates.generators.common as common

    (tmp_path / "roots.txt").write_text("microgrid\nworkflow\n", encoding="utf-8")
    (tmp_path / "suffixes.txt").write_text("grid\nflow\n", encoding="utf-8")
    (tmp_path / "compounds.txt").write_text("microgrid+grid\n", encoding="utf-8")
    (tmp_path / "generic.txt").write_text("zone\n", encoding="utf-8")
    monkeypatch.setattr(common, "SEED_DIR", tmp_path)
    monkeypatch.setattr(common, "_GENERIC_TERMS", tmp_path / "generic.txt")

    with pytest.raises(ValueError, match="repeats a component"):
        common.read_reviewed_compounds("roots.txt", "suffixes.txt", "compounds.txt")


def test_t4_rework2_review_examples_are_not_generated():
    generated_labels = {row.domain_label for rows in generate_all().values() for row in rows}
    weak_labels = {
        "zonehub", "kernelregion", "sourceapp", "sourcemodule", "regionsystem",
        "databasezone", "virtualzone", "privatebase", "voicelearn", "camerafiber",
        "banksystem", "appmodule", "dataindex", "salesfounder", "payaccount",
        "procureguide", "payrolltax", "covercare", "optionmarket", "expensesuite",
        "payablespend", "moneypayment", "taxpurchase", "policyhome", "loanwallet",
        "sharedesk", "investyield", "mindjourney", "treattrack", "vitalhabit",
        "vitalcare", "vitalitycare", "carerecord", "datagroup", "lifeactive",
        "lifewell", "studyfield", "labmeasure", "biopsyimage", "skinrecord",
        "homefriend", "mediamusic", "mediaticket", "photosport", "parentvibe",
        "sailhotel", "homeguide", "tutorquiz", "studytutor", "lessonpath",
        "beautyedit", "labelhouse", "waterocean", "oceanmarine", "solarenergy",
        "tidalenergy", "hydrosolar", "matterfiber", "carbonclean", "agrisystem",
        "agrisensor", "reactorwind", "missionscope", "microscale", "nanoscience",
        "buildops", "enterprisestudio", "basketbox", "basketworks", "basketshop",
        "basketclub", "getawaystay", "agriculturegrid", "soilstorage", "cropops",
        "aerospaceflight",
        "curriculumcourse",
    }

    assert not weak_labels.intersection(generated_labels)


def test_t4_pair_whitelist_terms_must_come_from_curated_vocabularies(tmp_path, monkeypatch):
    import si_domains.candidates.generators.common as common

    (tmp_path / "roots.txt").write_text("genome\n", encoding="utf-8")
    (tmp_path / "suffixes.txt").write_text("lab\n", encoding="utf-8")
    (tmp_path / "pairs.txt").write_text("genome+lab\ngenome+desk\n", encoding="utf-8")
    (tmp_path / "generic.txt").write_text("zone\n", encoding="utf-8")
    monkeypatch.setattr(common, "SEED_DIR", tmp_path)
    monkeypatch.setattr(common, "_GENERIC_TERMS", tmp_path / "generic.txt")

    with pytest.raises(ValueError, match="unknown root or suffix"):
        common.read_reviewed_compounds("roots.txt", "suffixes.txt", "pairs.txt")


def test_t4_seed_vocabularies_exclude_reviewed_generic_filler_terms():
    from si_domains.candidates.generators.common import (
        read_generic_candidate_terms,
        read_terms,
    )

    generic_fillers = read_generic_candidate_terms()
    required_generic_terms = {
        "zone", "region", "source", "data", "app", "system", "module", "base",
        "life", "care", "home", "media", "mind", "water", "energy", "vital",
        "study", "lesson", "policy", "pay", "tax", "money", "guide", "plan",
        "field", "path", "order", "auto", "measure", "safety", "family", "city",
        "healthy", "treat", "invest", "procure", "private", "shared", "build",
    }
    assert required_generic_terms <= generic_fillers

    for category in CATEGORIES[5:]:
        roots = set(read_terms(f"{category}_roots.txt"))
        suffixes = set(read_terms(f"{category}_suffixes.txt"))

        assert generic_fillers.isdisjoint(roots | suffixes)


def test_consumer_brand_suffix_vocabulary_stays_compact():
    seeds_dir = Path(__file__).parents[1] / "data" / "seeds"
    lines = (seeds_dir / "consumer_brands_suffixes.txt").read_text(encoding="utf-8").splitlines()
    heads = [line.strip() for line in lines if line.strip() and not line.lstrip().startswith("#")]

    assert 12 <= len(heads) <= 20


def test_ai_output_omits_generic_filler_product_joins_seen_in_review():
    generated_labels = {row.domain_label for rows in generate_all().values() for row in rows}
    weak_ai_labels = {
        "reasonbase", "imagepath", "logicgarden", "agentfield", "embedbase",
        "memorygarden", "visipath", "deepfield", "recallpath", "roboticbase",
        "modelgarden", "neuraharbor", "visiatelier", "synapharbor", "semantmind",
        "neuraroute",
    }

    assert not weak_ai_labels.intersection(generated_labels)


def test_t4_curated_output_omits_obvious_unreviewed_pairings():
    generated_labels = {
        candidate.domain_label
        for rows in generate_all().values()
        for candidate in rows
    }
    weak_labels = {
        "zoneregion", "regionharbor", "financetrade", "chainfinance",
        "monitoraudit", "configsource", "zeroaccess", "safetylock",
        "camerasignal", "autowatch", "auditguide", "valuefund",
        "orderfinance", "tradeguide", "yieldwealth", "bloodchart",
        "healthycare", "vitalitylife", "lifeguide", "safetylab",
        "measurepath", "wearableplan", "brainfield", "stemfield",
        "retailskin", "coffeesale", "retreatsail", "stagecinema",
        "familylife", "citybooking", "shopgarden", "storeorder",
        "tutorexam", "lessonbook", "watermarket", "routespace",
        "moleculemetal", "alloycarbon", "energycarbon", "chargefuel",
        "elementfiber", "motionorbit", "quantalaser",
        "clinicalworks", "hobbycraft", "underwritehub", "procurestudio",
        "precisionplant", "soilplant", "aquaponicplant", "aquaponiccell",
        "myceliumcell", "harvestcell", "biomaterialcell", "entangleforge",
        "aerialflight", "industrialops", "celebrationcraft", "audiobookvoice",
        "creatorvoice", "podcastvoice", "checkoutcart", "parceldelivery",
        "voyageescape", "voyagetrip", "ecommerceshop", "ecommercecart",
        "scholarshipworks", "socialcraft",
        "genomeomics", "researchomics", "cookwarehouse", "homewarehouse",
        "plantworks", "insurequote", "climateplant", "circularplant",
        "agricultureplant", "hydroponicplant", "aquacultureplant", "cropplant",
        "renewableplant",
        "microbialcell", "microbiomecell", "trialtherapy", "festivalshow",
        "windcell", "navigationdrive", "aquaculturecell",
        "examquiz", "documentaryshow", "checkoutshop", "basketcrate", "pharmacare",
        "musicsound", "decarbonplant", "decarbonops", "decarbonlab",
        "basketcart", "songvoice", "additivecell",
        "musiclive", "catalystcell",
    }

    assert not weak_labels.intersection(generated_labels)


def test_t4_generation_does_not_apply_a_per_category_quota(monkeypatch):
    import si_domains.candidates.build as build

    expected = 1_301

    def letters(number):
        chars = []
        for _ in range(5):
            number, remainder = divmod(number, 26)
            chars.append(chr(ord("a") + remainder))
        return "".join(reversed(chars))

    candidates = [
        Candidate(f"x{letters(number)}q", "technology", "blend", f"sample{number}", (), 80)
        for number in range(expected)
    ]
    monkeypatch.setattr(
        build,
        "_GENERATORS",
        {category: (lambda: []) for category in CATEGORIES}
        | {"technology": lambda: candidates},
    )

    generated = build.generate_all()

    assert len(generated["technology"]) == expected


def test_generated_committed_csvs_and_review_sample_match_regeneration(tmp_path):
    from si_domains.candidates.build import write_csv
    from si_domains.candidates.review import render_sample

    generated = generate_all()
    data_dir = Path(__file__).parents[1] / "data"
    for category, rows in generated.items():
        expected = tmp_path / f"{category}.csv"
        write_csv(expected, rows)
        first_bytes = expected.read_bytes()
        write_csv(expected, rows)
        assert expected.read_bytes() == first_bytes
        assert first_bytes == (data_dir / f"candidates_{category}.csv").read_bytes()

    combined = tmp_path / "combined.csv"
    write_csv(combined, [row for category in CATEGORIES for row in generated[category]])
    first_bytes = combined.read_bytes()
    write_csv(combined, [row for category in CATEGORIES for row in generated[category]])
    assert combined.read_bytes() == first_bytes
    assert first_bytes == (data_dir / "candidates.csv").read_bytes()

    sample_bytes = render_sample(40, 1).encode("utf-8")
    assert sample_bytes == (data_dir.parent / "docs" / "candidate_samples.md").read_bytes()


def test_generated_candidates_pass_registry_rules_and_brand_blocks():
    from si_domains.rules import classify

    generated = generate_all()
    labels = {row.domain_label for rows in generated.values() for row in rows}

    assert all(classify(label) == "ok" for label in labels)
    assert not {"si", "rs", "112"}.intersection(labels)
    brands = [
        line.strip().casefold()
        for line in (Path(__file__).parents[1] / "data" / "blocklist_brands.txt").read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    ]

    assert not any(
        brand in label
        for brand in brands
        if len(brand) >= 5
        for label in labels
    )


def test_generated_csv_rows_have_the_required_schema():
    from si_domains.candidates.schema import CSV_FIELDS

    generated = generate_all()
    for category, rows in generated.items():
        assert all(tuple(row.to_row()) == CSV_FIELDS for row in rows)
        assert all(row.category == category for row in rows)
        assert all(row.quality_score <= 100 and row.quality_score >= 0 for row in rows)


def test_category_cli_writes_a_valid_offline_csv(tmp_path):
    import csv

    from si_domains.cli import main

    output = tmp_path / "invented.csv"
    assert main(["candidates", "--category", "invented", "--out", str(output)]) == 0
    first_bytes = output.read_bytes()
    assert main(["candidates", "--category", "invented", "--out", str(output)]) == 0
    assert output.read_bytes() == first_bytes
    with output.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        rows = list(reader)
    assert reader.fieldnames == ["domain_label", "category", "method", "seed", "tags", "quality_score"]
    assert len(rows) >= 1_000
    assert {row["category"] for row in rows} == {"invented"}


def test_sample_cli_is_reproducible_and_includes_each_category(capsys):
    from si_domains.cli import main

    assert main(["candidates", "--sample", "40", "--seed", "1"]) == 0
    first = capsys.readouterr().out
    assert main(["candidates", "--sample", "40", "--seed", "1"]) == 0
    second = capsys.readouterr().out

    assert first == second
    for category in CATEGORIES:
        assert f"## {category} (40 of " in first


def test_all_cli_can_write_one_combined_unique_csv(tmp_path):
    import csv

    from si_domains.cli import main

    output = tmp_path / "all.csv"
    assert main(["candidates", "--all", "--out", str(output)]) == 0
    with output.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        rows = list(reader)
    assert reader.fieldnames == ["domain_label", "category", "method", "seed", "tags", "quality_score"]
    assert len(rows) == len({row["domain_label"] for row in rows})
