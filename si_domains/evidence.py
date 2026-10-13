"""Append-only, body-free RDAP evidence storage."""

from __future__ import annotations

import csv
import os
import re
from pathlib import Path
from typing import Mapping

from .config import EVIDENCE_PATH
from .rdap import Result


FIELDNAMES = (
    "domain",
    "category",
    "http_status",
    "utc_timestamp",
    "attempts",
    "classification",
    "error",
)
FINAL_CLASSIFICATIONS = frozenset(
    {
        "registered",
        "potentially_unregistered",
        "invalid_syntax",
        "reserved",
        "restricted",
        "premium",
    }
)
_SAFE_ERROR = frozenset(
    {
        "",
        "invalid_label",
        "network_timeout",
        "network_connection_error",
        "network_request_error",
        "unexpected_content_type",
        "invalid_json",
        "unexpected_json_shape",
        "unexpected_rdap_object",
        "ambiguous_404_response",
        "redirect_not_followed",
        "retry_after_exceeds_limit",
    }
)
_HTTP_ERROR = re.compile(r"^http_[1-5]\d\d$")


class EvidenceStore:
    """Read latest rows and durably append one row per completed domain check."""

    def __init__(self, path: str | Path = EVIDENCE_PATH) -> None:
        self.path = Path(path)
        self._latest: dict[str, dict[str, str]] | None = None
        self.load_latest()

    def _repair_torn_final_row(self) -> None:
        if not self.path.exists():
            return
        with self.path.open("rb+") as handle:
            handle.seek(0, os.SEEK_END)
            size = handle.tell()
            if size == 0:
                return
            handle.seek(-1, os.SEEK_END)
            if handle.read(1) == b"\n":
                return
            handle.seek(0)
            contents = handle.read()
            boundary = contents.rfind(b"\n") + 1
            handle.truncate(boundary)
            handle.flush()
            os.fsync(handle.fileno())

    def load_latest(self) -> dict[str, dict[str, str]]:
        latest: dict[str, dict[str, str]] = {}
        if self.path.exists():
            self._repair_torn_final_row()
            with self.path.open("r", encoding="utf-8-sig", newline="") as handle:
                for row in csv.DictReader(handle):
                    domain = (row.get("domain") or "").strip()
                    if domain:
                        latest[domain] = {key: (value or "") for key, value in row.items() if key}
        self._latest = latest
        return latest

    def should_skip(self, domain: str, *, retry_unverified: bool = False) -> bool:
        latest = self._latest if self._latest is not None else self.load_latest()
        row = latest.get(domain)
        if row is None:
            return False
        classification = row.get("classification", "")
        if classification in FINAL_CLASSIFICATIONS:
            return True
        if classification == "unverified":
            return not retry_unverified
        return False

    def append(self, category: str, result: Result) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._repair_torn_final_row()
        error = result.error.replace("\r", " ").replace("\n", " ")
        if error not in _SAFE_ERROR and not _HTTP_ERROR.fullmatch(error):
            error = "unspecified_error"
        row = {
            "domain": result.domain,
            "category": category,
            "http_status": "" if result.http_status is None else str(result.http_status),
            "utc_timestamp": result.utc_timestamp,
            "attempts": str(result.attempts),
            "classification": result.classification,
            "error": error,
        }

        with self.path.open("a+", encoding="utf-8", newline="") as handle:
            handle.seek(0, os.SEEK_END)
            writer = csv.DictWriter(
                handle,
                fieldnames=FIELDNAMES,
                extrasaction="ignore",
                lineterminator="\n",
            )
            if handle.tell() == 0:
                writer.writeheader()
                handle.flush()
                os.fsync(handle.fileno())
            writer.writerow(row)
            handle.flush()
            os.fsync(handle.fileno())

        if self._latest is None:
            self._latest = {}
        self._latest[result.domain] = row


def load_latest(path: str | Path = EVIDENCE_PATH) -> Mapping[str, dict[str, str]]:
    """Convenience function for callers that only need a one-time CSV read."""

    return EvidenceStore(path).load_latest()
