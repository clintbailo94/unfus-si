"""Registry policy hook; T2 will add reserved and restricted-name rules."""


def classify(label: str) -> str:
    """Classify a syntactically valid label before network lookup."""

    return "ok"
