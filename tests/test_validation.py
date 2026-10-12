from si_domains.validation import is_valid_label


def test_ldh_validation_accepts_valid_labels():
    assert is_valid_label("a")
    assert is_valid_label("valid-name9")
    assert is_valid_label("a" * 63)


def test_ldh_validation_rejects_bad_syntax():
    for label in ("", "A", "-start", "end-", "ab--cd", "a" * 64, "has.dot", "has space"):
        assert not is_valid_label(label)

