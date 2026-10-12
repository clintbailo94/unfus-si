"""Validation and ASCII conversion for labels sent to registry services."""

import re
import unicodedata


_ASCII_LDH = re.compile(r"^[a-z0-9-]+$")
_ASCII_LETTERS_AND_DIGITS = set("abcdefghijklmnopqrstuvwxyz0123456789-")
_IDN_LETTERS = set(
    "àáâãäåæçèéêëìíîïðñòóôõöøùúûüýþÿ"
    "āăąćĉċčďđēĕėęěĝğġģĥħĩīĭįıĵķĺļľŀłńņňŉŋōŏőœŕŗřśŝšťŧũūŭůűųŵŷźżž"
    "șț"
)
_UPPER_IDN_LETTERS = {
    uppercase
    for character in _IDN_LETTERS
    if len(uppercase := character.upper()) == 1 and uppercase not in _ASCII_LETTERS_AND_DIGITS
}


def _normalise_u_label(label: str) -> str | None:
    """Normalize explicitly allowed characters without folding lookalikes."""

    if any(
        not (character.isascii() and character.lower() in _ASCII_LETTERS_AND_DIGITS)
        and character not in _IDN_LETTERS
        and character not in _UPPER_IDN_LETTERS
        for character in label
    ):
        return None
    normalised = unicodedata.normalize("NFC", label)
    result: list[str] = []
    for character in normalised:
        if character.isascii():
            folded = character.lower()
            if folded not in _ASCII_LETTERS_AND_DIGITS:
                return None
            result.append(folded)
        elif character in _IDN_LETTERS:
            result.append(character)
        elif character in _UPPER_IDN_LETTERS:
            folded = character.lower()
            if folded not in _IDN_LETTERS:
                return None
            result.append(folded)
        else:
            return None
    return unicodedata.normalize("NFC", "".join(result))


def _valid_u_label(label: str) -> bool:
    if len(label) < 2 or label.startswith("-") or label.endswith("-"):
        return False
    if label[2:4] == "--":
        return False
    return all(character in _ASCII_LETTERS_AND_DIGITS or character in _IDN_LETTERS for character in label)


def ascii_label(label: object) -> str | None:
    """Return the lowercase ASCII label (ACE for an IDN), or ``None`` if invalid.

    .si permits the published Latin-script IDN characters. Registry network
    requests use the ASCII ACE form so transport clients never send Unicode.
    """

    if not isinstance(label, str):
        return None

    raw_label = label
    normalised = raw_label.lower() if raw_label.isascii() else _normalise_u_label(raw_label)
    if not normalised:
        return None

    if normalised.isascii():
        if not 2 <= len(normalised) <= 63 or not _ASCII_LDH.fullmatch(normalised):
            return None
        if normalised.startswith("-") or normalised.endswith("-"):
            return None

        if normalised.startswith("xn--"):
            try:
                decoded = _normalise_u_label(normalised[4:].encode("ascii").decode("punycode"))
            except (UnicodeError, ValueError):
                return None
            if decoded is None or not any(not character.isascii() for character in decoded):
                return None
            if not _valid_u_label(decoded):
                return None
            try:
                canonical = "xn--" + decoded.encode("punycode").decode("ascii").lower()
            except UnicodeError:
                return None
            return normalised if canonical == normalised else None

        if normalised[2:4] == "--":
            return None
        return normalised

    if not _valid_u_label(normalised):
        return None
    try:
        ace = "xn--" + normalised.encode("punycode").decode("ascii").lower()
    except UnicodeError:
        return None
    return ace if len(ace) <= 63 else None


def is_valid_label(label: object) -> bool:
    """Return whether *label* meets known .si label syntax rules."""

    return ascii_label(label) is not None
