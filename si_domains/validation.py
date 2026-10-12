"""Shared validation for labels sent to registry services."""

import re


_LDH_LABEL = re.compile(r"^[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?$")


def is_valid_label(label: object) -> bool:
    """Return whether *label* is a lowercase LDH label valid for a .si name."""

    if not isinstance(label, str) or not 1 <= len(label) <= 63:
        return False
    if not _LDH_LABEL.fullmatch(label):
        return False
    return label[2:4] != "--"
