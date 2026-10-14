"""Curated ownership input for the ranked domain report."""

from __future__ import annotations

import csv
import re
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Collection


_DOMAIN_PATTERN = re.compile(r"[a-z0-9](?:[a-z0-9-]*[a-z0-9])?\.si\Z")


@dataclass(frozen=True)
class OwnedDomain:
    domain: str
    purchase_date: str

    @property
    def availability_text(self) -> str:
        return f"owned by you (bought {self.purchase_date})"


def load_owned_domains(
    path: str | Path,
    *,
    candidate_domains: Collection[str],
    shortlist_domains: Collection[str],
) -> tuple[OwnedDomain, ...]:
    """Read ownership rows and require each one to be a candidate in the shortlist."""

    source = Path(path)
    if not source.is_file():
        raise FileNotFoundError(f"owned domains file not found: {source}")

    candidates = {domain.strip().casefold() for domain in candidate_domains}
    shortlisted = {domain.strip().casefold() for domain in shortlist_domains}
    owned: list[OwnedDomain] = []
    seen: set[str] = set()

    with source.open("r", encoding="utf-8-sig", newline="") as handle:
        rows = csv.reader(
            line for line in handle if line.strip() and not line.lstrip().startswith("#")
        )
        for line_number, row in enumerate(rows, start=1):
            if line_number == 1 and [field.strip().casefold() for field in row] == [
                "domain",
                "purchase_date",
            ]:
                continue
            if len(row) != 2:
                raise ValueError(
                    f"owned domains line {line_number} must contain domain,purchase_date"
                )
            raw_domain, raw_purchase_date = row
            domain = raw_domain.strip().casefold()
            if not _DOMAIN_PATTERN.fullmatch(domain):
                raise ValueError(
                    f"invalid .si domain in owned domains line {line_number}: {raw_domain!r}"
                )
            if domain in seen:
                raise ValueError(f"duplicate owned domain in owned domains line {line_number}: {domain}")
            seen.add(domain)
            purchase_date = raw_purchase_date.strip()
            try:
                parsed_date = date.fromisoformat(purchase_date)
            except ValueError as exc:
                raise ValueError(
                    f"invalid purchase date in owned domains line {line_number}: {raw_purchase_date!r}"
                ) from exc
            if parsed_date.isoformat() != purchase_date:
                raise ValueError(
                    f"purchase date must be YYYY-MM-DD in owned domains line {line_number}: {raw_purchase_date!r}"
                )
            if domain not in candidates:
                raise ValueError(f"owned domain is not in data/candidates.csv: {domain}")
            if domain not in shortlisted:
                raise ValueError(f"owned domain is not in the 500-row shortlist: {domain}")
            owned.append(OwnedDomain(domain, purchase_date))

    return tuple(owned)
