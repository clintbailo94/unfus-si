from pathlib import Path

import pytest

from si_domains.rules import classify, explain, load_name_rules


ROOT = Path(__file__).parents[1]
RESERVED_SOURCE = "https://www.register.si/en/reserved-domain-names/"


@pytest.mark.parametrize(
    "label,expected",
    [
        ("ai", "ok"),
        ("Valid-Name9", "ok"),
        ("a" * 63, "ok"),
        ("roža", "ok"),
        ("ROŽA", "ok"),
        ("Þorn", "ok"),
        ("xn--roa-d3a", "ok"),
        ("a", "invalid_syntax"),
        ("", "invalid_syntax"),
        ("-start", "invalid_syntax"),
        ("end-", "invalid_syntax"),
        ("ab--cd", "invalid_syntax"),
        ("xn--bea", "invalid_syntax"),  # one-character IDN label
        ("a" * 64, "invalid_syntax"),
        ("has.dot", "invalid_syntax"),
        ("has space", "invalid_syntax"),
        ("ßname", "invalid_syntax"),  # case-folding must not admit unlisted characters
        ("Kk", "invalid_syntax"),  # canonical lookalikes outside the published table stay rejected
        ("名詞", "invalid_syntax"),  # only the published Latin character tables are allowed
    ],
)
def test_classifies_registry_syntax(label, expected):
    assert classify(label) == expected


@pytest.mark.parametrize("label", ["112", "113", "rs", "si", "xeroxdiscoverysupernode1", "xeroxdiscoverysupernode2", "xeroxdiscoverysupernode3"])
def test_reserved_names_are_loaded_and_explained(label):
    assert classify(label) == "reserved"
    classification, rule_id, source_url = explain(label)
    assert classification == "reserved"
    assert rule_id == f"reserved:{label}"
    assert source_url == RESERVED_SOURCE


def test_name_rule_csvs_have_expected_schema_and_known_entries():
    reserved, restricted = load_name_rules()
    assert set(reserved) == {
        "112", "113", "rs", "si", "xeroxdiscoverysupernode1",
        "xeroxdiscoverysupernode2", "xeroxdiscoverysupernode3",
    }
    assert restricted == {}

    for path in (ROOT / "data" / "reserved_names.csv", ROOT / "data" / "restricted_names.csv"):
        header = path.read_text(encoding="utf-8").splitlines()[0]
        assert header == "label,class,source_url,note"


def test_restricted_explanation_uses_the_data_row_source(tmp_path, monkeypatch):
    import si_domains.rules as rules

    reserved_path = tmp_path / "reserved.csv"
    restricted_path = tmp_path / "restricted.csv"
    reserved_path.write_text("label,class,source_url,note\n", encoding="utf-8")
    restricted_path.write_text(
        "label,class,source_url,note\nexample,restricted,https://registry.example/rule,synthetic test row\n",
        encoding="utf-8",
    )
    _reserved, restricted = load_name_rules(reserved_path, restricted_path)
    monkeypatch.setattr(rules, "_RESERVED_NAMES", {})
    monkeypatch.setattr(rules, "_RESTRICTED_NAMES", restricted)

    assert explain("example") == (
        "restricted",
        "restricted:example",
        "https://registry.example/rule",
    )


def test_loader_rejects_malformed_data_files(tmp_path):
    bad_csv = tmp_path / "bad.csv"
    bad_csv.write_text("label,class,note\nexample,reserved,missing source\n", encoding="utf-8")
    with pytest.raises(ValueError, match="source_url"):
        load_name_rules(bad_csv, tmp_path / "restricted.csv")


def test_name_rule_loader_accepts_crlf_csv(tmp_path):
    reserved_path = tmp_path / "reserved.csv"
    restricted_path = tmp_path / "restricted.csv"
    reserved_path.write_bytes(
        b"label,class,source_url,note\r\n"
        b"example,reserved,https://registry.example/rule,synthetic note\r\n"
    )
    restricted_path.write_bytes(
        b"label,class,source_url,note\r\n"
        b"limited,restricted,https://registry.example/restrictions,another note\r\n"
    )

    reserved, restricted = load_name_rules(reserved_path, restricted_path)

    assert reserved["example"]["note"] == "synthetic note"
    assert restricted["limited"]["source_url"] == "https://registry.example/restrictions"


def test_known_rules_do_not_imply_availability_or_premium_pricing():
    assert classify("brandable") == "ok"
    assert classify("premium") == "ok"
    assert explain("brandable")[0] == "ok"

