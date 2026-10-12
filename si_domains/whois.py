"""RFC 3912 WHOIS client that discards response text after classification."""

from __future__ import annotations

import re
import socket
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Callable

from .config import WHOIS_HOST, WHOIS_MAX_BYTES, WHOIS_PORT, WHOIS_TIMEOUT
from .validation import ascii_label, is_valid_label


_NO_MATCH_PATTERNS = (
    ("no_entries_found", re.compile(r"^\s*(?:%\s*)?no entries found\b", re.I)),
    ("no_match", re.compile(r"^\s*(?:%\s*)?no match(?: for)?\b", re.I)),
    ("no_such_domain", re.compile(r"^\s*(?:%\s*)?no such domain\b", re.I)),
    ("domain_not_found", re.compile(r"^\s*(?:%\s*)?domain not found\b", re.I)),
    ("domain_does_not_exist", re.compile(r"^\s*(?:%\s*)?domain does not exist\b", re.I)),
)
_REGISTRATION_FIELD = re.compile(
    r"^\s*(registrar|created|registered|nserver|nameserver|name\s+server)\s*:\s*\S+",
    re.I,
)


def _timestamp(clock: Callable[[], datetime | float]) -> str:
    value = clock()
    if isinstance(value, datetime):
        if value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)
        else:
            value = value.astimezone(timezone.utc)
    else:
        value = datetime.fromtimestamp(float(value), tz=timezone.utc)
    return value.isoformat(timespec="seconds").replace("+00:00", "Z")


@dataclass(frozen=True)
class WhoisResult:
    domain: str
    classification: str
    utc_timestamp: str
    matched_pattern: str = ""
    error: str = ""


def classify_whois_text(text: str) -> tuple[str, str]:
    """Return a conservative classification and a body-free pattern identifier."""

    for line in text.splitlines():
        for pattern_name, pattern in _NO_MATCH_PATTERNS:
            if pattern.search(line):
                return "not_registered", pattern_name

    for line in text.splitlines():
        if line.lstrip().startswith("%"):
            continue
        match = _REGISTRATION_FIELD.search(line)
        if match:
            return "registered", f"field:{match.group(1).casefold().replace(' ', '_')}"
    return "unverified", "no_recognized_pattern"


def whois_check(
    label: str,
    *,
    connect: Callable = socket.create_connection,
    clock: Callable[[], datetime | float] = lambda: datetime.now(timezone.utc),
) -> WhoisResult:
    """Query the .si WHOIS service once; do not return or persist the response."""

    domain = f"{label}.si" if isinstance(label, str) else f"{label}.si"
    timestamp = _timestamp(clock)
    if not is_valid_label(label):
        return WhoisResult(domain, "unverified", timestamp, "", "invalid_label")

    try:
        with connect((WHOIS_HOST, WHOIS_PORT), timeout=WHOIS_TIMEOUT) as connection:
            connection.settimeout(WHOIS_TIMEOUT)
            query_domain = f"{ascii_label(label)}.si"
            connection.sendall((query_domain + "\r\n").encode("ascii"))
            chunks: list[bytes] = []
            total = 0
            while total < WHOIS_MAX_BYTES:
                chunk = connection.recv(min(4096, WHOIS_MAX_BYTES - total))
                if not chunk:
                    break
                chunks.append(chunk)
                total += len(chunk)
            if total >= WHOIS_MAX_BYTES:
                return WhoisResult(domain, "unverified", timestamp, "response_cap", "response_too_large")
    except socket.timeout:
        return WhoisResult(domain, "unverified", timestamp, "", "timeout")
    except OSError:
        return WhoisResult(domain, "unverified", timestamp, "", "connection_error")

    text = b"".join(chunks).decode("utf-8", errors="replace")
    if not text:
        return WhoisResult(domain, "unverified", timestamp, "", "empty_response")
    classification, matched_pattern = classify_whois_text(text)
    return WhoisResult(domain, classification, timestamp, matched_pattern, "")
