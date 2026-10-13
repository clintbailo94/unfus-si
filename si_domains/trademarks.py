"""Curated, offline aggregation for public trademark screening evidence."""

from __future__ import annotations

import csv
import re
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse


TRADEMARK_EVIDENCE_FIELDS = (
    "evidence_id",
    "domain",
    "source",
    "jurisdiction",
    "query",
    "utc_timestamp",
    "result_status",
    "source_url",
    "result_url",
    "mark_number",
    "mark_name",
    "mark_status",
    "classes",
    "notes",
)
TRADEMARK_SUMMARY_FIELDS = (
    "domain",
    "status",
    "trademark_score",
    "evidence_ids",
    "coverage",
    "limitations",
)
REQUIRED_SOURCES = ("TMview", "UKIPO", "USPTO")
RESULT_STATUSES = frozenset(
    {"no_obvious_match", "possible_conflict", "blocked", "unverified"}
)
SUMMARY_STATUSES = frozenset(
    {"limited_screen_no_obvious_match", "needs legal review", "blocked", "unverified"}
)
_DOMAIN = re.compile(r"^[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.si$")
_OFFICIAL_HOSTS = {
    "TMview": ("tmdn.org",),
    "UKIPO": ("ipo.gov.uk",),
    "USPTO": ("uspto.gov",),
}


def _read_csv(path: str | Path, required: set[str], description: str) -> list[dict[str, str]]:
    with Path(path).open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if not reader.fieldnames or not required.issubset(reader.fieldnames):
            raise ValueError(f"{description} CSV is missing required columns")
        return [{key: (value or "").strip() for key, value in row.items() if key} for row in reader]


def _valid_utc_timestamp(value: str) -> bool:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return False
    return parsed.tzinfo is not None and parsed.utcoffset() is not None and parsed.utcoffset().total_seconds() == 0


def validate_evidence_rows(rows: list[dict[str, str]]) -> dict[str, dict[str, str]]:
    """Check a curated evidence file and return its stable-ID index."""

    indexed: dict[str, dict[str, str]] = {}
    for row in rows:
        evidence_id = row.get("evidence_id", "")
        if not evidence_id or evidence_id in indexed:
            raise ValueError(f"trademark evidence has a blank or duplicate evidence_id: {evidence_id!r}")
        if row.get("source") not in REQUIRED_SOURCES:
            raise ValueError(f"unknown trademark source for {evidence_id}")
        domain = row.get("domain", "").casefold()
        if domain != "*" and not _DOMAIN.fullmatch(domain):
            raise ValueError(f"invalid trademark evidence domain for {evidence_id}")
        if row.get("result_status") not in RESULT_STATUSES:
            raise ValueError(f"invalid trademark result_status for {evidence_id}")
        if not row.get("query"):
            raise ValueError(f"trademark evidence query is blank for {evidence_id}")
        if not _valid_utc_timestamp(row.get("utc_timestamp", "")):
            raise ValueError(f"trademark evidence timestamp must be UTC for {evidence_id}")
        for field in ("source_url",):
            parsed = urlparse(row.get(field, ""))
            if parsed.scheme not in {"http", "https"} or not parsed.netloc:
                raise ValueError(f"trademark evidence needs a public {field} for {evidence_id}")
            host = (parsed.hostname or "").casefold()
            if not any(host == suffix or host.endswith("." + suffix) for suffix in _OFFICIAL_HOSTS[row["source"]]):
                raise ValueError(f"trademark evidence URL is not on the official {row['source']} host: {evidence_id}")
        if domain == "*":
            if row["result_status"] not in {"blocked", "unverified"}:
                raise ValueError(f"source-wide trademark attempt cannot assert a search result: {evidence_id}")
            if "no per-domain query ran" not in row.get("notes", "").casefold():
                raise ValueError(f"source-wide trademark attempt must say no per-domain query ran: {evidence_id}")
        elif row["result_status"] in {"no_obvious_match", "possible_conflict"}:
            result_url = row.get("result_url", "").strip()
            if not result_url or result_url == row["source_url"]:
                raise ValueError(f"completed trademark query needs a query-specific result URL: {evidence_id}")
            result_host = (urlparse(result_url).hostname or "").casefold()
            if not any(result_host == suffix or result_host.endswith("." + suffix) for suffix in _OFFICIAL_HOSTS[row["source"]]):
                raise ValueError(f"trademark result URL is not on the official {row['source']} host: {evidence_id}")
        if row["result_status"] == "possible_conflict" and not (
            row.get("mark_number") or row.get("mark_name")
        ):
            raise ValueError(f"possible-conflict evidence needs an observed mark identifier or name: {evidence_id}")
        indexed[evidence_id] = row
    return indexed


def read_trademark_evidence(path: str | Path) -> tuple[list[dict[str, str]], dict[str, dict[str, str]]]:
    rows = _read_csv(path, set(TRADEMARK_EVIDENCE_FIELDS), "trademark evidence")
    return rows, validate_evidence_rows(rows)


def validate_summary_rows(
    rows: list[dict[str, str]],
    evidence_index: dict[str, dict[str, str]] | None = None,
    *,
    candidate_domains: set[str] | None = None,
) -> dict[str, dict[str, str]]:
    indexed: dict[str, dict[str, str]] = {}
    for row in rows:
        domain = row.get("domain", "").casefold()
        if not _DOMAIN.fullmatch(domain) or domain in indexed:
            raise ValueError(f"trademark summary has invalid or duplicate domain: {domain!r}")
        if candidate_domains is not None and domain not in candidate_domains:
            raise ValueError(f"trademark summary domain is not a candidate: {domain}")
        status = row.get("status", "")
        if status not in SUMMARY_STATUSES:
            raise ValueError(f"invalid trademark summary status for {domain}")
        try:
            score = int(row.get("trademark_score", ""))
        except ValueError as exc:
            raise ValueError(f"invalid trademark score for {domain}") from exc
        if not 0 <= score <= 100:
            raise ValueError(f"trademark score must be between 0 and 100 for {domain}")
        expected = {
            "limited_screen_no_obvious_match": {80},
            "needs legal review": set(range(26)),
            "blocked": {70},
            "unverified": {70},
        }[status]
        if score not in expected:
            raise ValueError(f"trademark score does not match status for {domain}")
        if not row.get("coverage", "").strip():
            raise ValueError(f"trademark coverage is blank for {domain}")
        ids = [item for item in row.get("evidence_ids", "").split(";") if item]
        if status != "unverified" and not ids:
            raise ValueError(f"trademark summary needs evidence references for {domain}")
        if evidence_index is not None:
            for evidence_id in ids:
                evidence = evidence_index.get(evidence_id)
                if evidence is None:
                    raise ValueError(f"unknown trademark evidence_id {evidence_id} for {domain}")
                if evidence["domain"].casefold() not in {domain, "*"}:
                    raise ValueError(f"trademark evidence {evidence_id} belongs to another domain")
        indexed[domain] = row
    return indexed


def read_trademark_summary(
    path: str | Path,
    *,
    evidence_path: str | Path | None = None,
    candidate_domains: set[str] | None = None,
) -> dict[str, dict[str, str]]:
    rows = _read_csv(path, set(TRADEMARK_SUMMARY_FIELDS), "trademark summary")
    evidence_rows: list[dict[str, str]] | None = None
    evidence_index = None
    if evidence_path:
        evidence_rows, evidence_index = read_trademark_evidence(evidence_path)
    indexed = validate_summary_rows(rows, evidence_index, candidate_domains=candidate_domains)
    if evidence_rows is not None:
        recomputed = aggregate_trademark_rows(evidence_rows, list(indexed))
        for row in recomputed:
            domain = row["domain"]
            if any(indexed[domain].get(key, "") != row.get(key, "") for key in ("status", "trademark_score", "evidence_ids", "coverage")):
                raise ValueError(f"trademark summary does not match evidence for {domain}")
    return indexed


def aggregate_trademark_rows(
    evidence_rows: list[dict[str, str]], domains: list[str]
) -> list[dict[str, str]]:
    """Aggregate actual per-domain searches without treating access attempts as queries."""

    evidence_index = validate_evidence_rows(evidence_rows)
    by_source_domain: dict[tuple[str, str], list[dict[str, str]]] = defaultdict(list)
    by_source_global: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in evidence_rows:
        if row["domain"] == "*":
            by_source_global[row["source"]].append(row)
        else:
            by_source_domain[(row["source"], row["domain"].casefold())].append(row)

    summaries: list[dict[str, str]] = []
    seen_domains: set[str] = set()
    for raw_domain in domains:
        domain = raw_domain.strip().casefold()
        if not _DOMAIN.fullmatch(domain) or domain in seen_domains:
            raise ValueError(f"invalid or duplicate domain in trademark summary input: {domain!r}")
        seen_domains.add(domain)
        source_states: dict[str, str] = {}
        evidence_ids: list[str] = []
        conflict = False
        for source in REQUIRED_SOURCES:
            actual = by_source_domain.get((source, domain), [])
            actual = sorted(actual, key=lambda item: (item["utc_timestamp"], item["evidence_id"]))
            if actual:
                evidence_ids.extend(row["evidence_id"] for row in actual)
                source_states[source] = actual[-1]["result_status"]
                conflict = conflict or any(row["result_status"] == "possible_conflict" for row in actual)
            else:
                global_rows = sorted(
                    by_source_global.get(source, []),
                    key=lambda item: (item["utc_timestamp"], item["evidence_id"]),
                )
                if global_rows:
                    evidence_ids.extend(row["evidence_id"] for row in global_rows)
                    source_states[source] = global_rows[-1]["result_status"]
                else:
                    source_states[source] = "unverified"

        if conflict:
            status, score = "needs legal review", 25
        elif "unverified" in source_states.values():
            status, score = "unverified", 70
        elif all(value == "blocked" for value in source_states.values()):
            status, score = "blocked", 70
        elif all(value in {"no_obvious_match", "blocked"} for value in source_states.values()) and any(
            value == "no_obvious_match" for value in source_states.values()
        ):
            status, score = "limited_screen_no_obvious_match", 80
        elif any(value == "blocked" for value in source_states.values()):
            status, score = "blocked", 70
        else:
            status, score = "unverified", 70

        blocked_sources = [source for source in REQUIRED_SOURCES if source_states[source] == "blocked"]
        limitations = "Exact-word/public UI screen only; no comprehensive phonetic, class, or global coverage."
        if blocked_sources:
            limitations += " Blocked sources: " + ", ".join(blocked_sources) + "; no per-domain query ran there."
        if "unverified" in source_states.values():
            unknown_sources = [source for source in REQUIRED_SOURCES if source_states[source] == "unverified"]
            limitations += " Unverified sources: " + ", ".join(unknown_sources) + "; no no-match conclusion."
        coverage = ";".join(f"{source}:{source_states[source]}" for source in REQUIRED_SOURCES)
        summaries.append(
            {
                "domain": domain,
                "status": status,
                "trademark_score": str(score),
                "evidence_ids": ";".join(dict.fromkeys(evidence_ids)),
                "coverage": coverage,
                "limitations": limitations,
            }
        )
    validate_summary_rows(summaries, evidence_index)
    return summaries


def write_trademark_summary(
    evidence_path: str | Path,
    domains_path: str | Path,
    output_path: str | Path,
    *,
    top_n: int | None = None,
) -> int:
    evidence_rows, _index = read_trademark_evidence(evidence_path)
    domain_rows = _read_csv(domains_path, {"domain"}, "domain list")
    if top_n is not None:
        if top_n < 1:
            raise ValueError("top_n must be positive")
        if all("rank" in row for row in domain_rows):
            domain_rows = sorted(domain_rows, key=lambda row: int(row["rank"]))[:top_n]
        else:
            domain_rows = domain_rows[:top_n]
    summaries = aggregate_trademark_rows(evidence_rows, [row["domain"] for row in domain_rows])
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=TRADEMARK_SUMMARY_FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(summaries)
    return len(summaries)

