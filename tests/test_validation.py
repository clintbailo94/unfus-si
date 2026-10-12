from si_domains.validation import is_valid_label


def test_ldh_validation_accepts_valid_labels():
    assert is_valid_label("ab")
    assert is_valid_label("valid-name9")
    assert is_valid_label("Valid-Name9")
    assert is_valid_label("a" * 63)
    assert is_valid_label("roža")
    assert is_valid_label("xn--roa-d3a")


def test_ldh_validation_rejects_bad_syntax():
    for label in ("", "a", "-start", "end-", "ab--cd", "xn--bea", "a" * 64, "has.dot", "has space", "名詞"):
        assert not is_valid_label(label)

