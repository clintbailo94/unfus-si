"""Join research evidence and validate reproducible PKG-B artifacts."""

from __future__ import annotations

import csv
import sys
from decimal import Decimal, InvalidOperation
from pathlib import Path

from .shortlist import CATEGORY_LIMIT, SHORTLIST_FIELDS, SHORTLIST_LIMIT
from .scoring import SCORE_FIELDS, SCORE_WEIGHTS, weighted_total
from .trademarks import (
    DEFAULT_CANDIDATES_PATH,
    REQUIRED_SOURCES,
    aggregate_trademark_rows,
    query_coverage_by_source,
    read_candidate_context,
    read_trademark_evidence,
    read_trademark_summary,
)
from .valuation import (
    VALUATION_FIELDS,
    eligible_comps,
    read_valuation_evidence,
)


OPPORTUNITY_FIELDS = (
    "rank",
    "domain",
    "category",
    "total",
    "brandability",
    "commercial",
    "shortness",
    "hack",
    "resale",
    "trademark",
    "rdap_timestamp",
    "whois_timestamp",
    "rationale",
    "valuation_status",
    "valuation_currency",
    "valuation_low",
    "valuation_high",
    "valuation_evidence_ids",
    "valuation_rationale",
    "trademark_status",
    "trademark_coverage",
    "trademark_evidence_ids",
)


def _read_csv(path: str | Path, required: set[str], description: str) -> list[dict[str, str]]:
    with Path(path).open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if not reader.fieldnames or not required.issubset(reader.fieldnames):
            raise ValueError(f"{description} CSV is missing required columns")
        return [{key: (value or "").strip() for key, value in row.items() if key} for row in reader]


def _unique_by_domain(rows: list[dict[str, str]], description: str) -> dict[str, dict[str, str]]:
    indexed: dict[str, dict[str, str]] = {}
    for row in rows:
        domain = row.get("domain", "").casefold()
        if not domain or domain in indexed:
            raise ValueError(f"{description} has a blank or duplicate domain: {domain!r}")
        indexed[domain] = row
    return indexed


def _write_csv(path: str | Path, fields: tuple[str, ...], rows: list[dict[str, str]]) -> None:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def write_opportunities(
    shortlist_path: str | Path,
    scores_path: str | Path,
    valuation_path: str | Path,
    trademark_summary_path: str | Path,
    output_path: str | Path,
) -> int:
    shortlist_rows = _read_csv(shortlist_path, {"rank", "domain", "category", "total"}, "shortlist")
    scores_rows = _read_csv(scores_path, set(SCORE_FIELDS), "score")
    valuation_rows = _read_csv(valuation_path, set(VALUATION_FIELDS), "valuation")
    summary_rows = _read_csv(trademark_summary_path, {"domain", "status", "evidence_ids", "coverage"}, "trademark summary")
    scores = _unique_by_domain(scores_rows, "score")
    valuations = _unique_by_domain(valuation_rows, "valuation")
    summaries = _unique_by_domain(summary_rows, "trademark summary")

    shortlist = _unique_by_domain(shortlist_rows, "shortlist")
    if set(shortlist) != set(valuations):
        raise ValueError("valuation domain set does not exactly match final shortlist")
    if not set(shortlist).issubset(scores):
        raise ValueError("final shortlist contains a domain missing from scores")

    output_rows: list[dict[str, str]] = []
    for row in shortlist_rows:
        domain = row["domain"].casefold()
        valuation = valuations[domain]
        score = scores[domain]
        summary = summaries.get(domain)
        if row["rank"] != valuation.get("rank", row["rank"]):
            raise ValueError(f"valuation rank does not match shortlist for {domain}")
        if row["total"] != score["total"] or any(row[name] != score[name] for name in SCORE_WEIGHTS):
            raise ValueError(f"shortlist components do not match score artifact for {domain}")
        output_rows.append(
            {
                **{field: row.get(field, "") for field in OPPORTUNITY_FIELDS[:13]},
                "valuation_status": valuation["status"],
                "valuation_currency": valuation["currency"],
                "valuation_low": valuation["low"],
                "valuation_high": valuation["high"],
                "valuation_evidence_ids": valuation["evidence_ids"],
                "valuation_rationale": valuation["rationale"],
                "trademark_status": summary["status"] if summary else "not yet screened",
                "trademark_coverage": summary.get("coverage", "") if summary else "",
                "trademark_evidence_ids": summary.get("evidence_ids", "") if summary else "",
            }
        )
    _write_csv(output_path, OPPORTUNITY_FIELDS, output_rows)
    return len(output_rows)


def _decimal(value: str, description: str) -> Decimal:
    try:
        result = Decimal(value)
    except InvalidOperation as exc:
        raise ValueError(f"invalid {description}: {value!r}") from exc
    if not result.is_finite():
        raise ValueError(f"non-finite {description}: {value!r}")
    return result


def _screening_counts(
    shortlist_top: list[dict[str, str]],
    evidence_rows: list[dict[str, str]],
    query_manifest: dict[str, tuple[str, ...]],
    proof_root: str | Path,
) -> tuple[dict[str, dict[str, int]], bool]:
    counts = {
        source: {
            "completed": 0,
            "sourcewide_blocked": 0,
            "query_blocked": 0,
            "unverified": 0,
        }
        for source in REQUIRED_SOURCES
    }
    unresolved = False
    for source in REQUIRED_SOURCES:
        for shortlist_row in shortlist_top:
            domain = shortlist_row["domain"].casefold()
            expected = query_manifest.get(domain, ())
            coverage = query_coverage_by_source(
                evidence_rows,
                domain,
                expected,
                proof_root=proof_root,
            )[source]
            if coverage["status"] in {"no_obvious_match", "possible_conflict"} and coverage["completed"] == coverage["required"]:
                counts[source]["completed"] += 1
            elif coverage["status"] == "unverified":
                counts[source]["unverified"] += 1
            elif coverage["query_blocked"]:
                counts[source]["query_blocked"] += 1
            elif coverage["sourcewide_blocked"]:
                counts[source]["sourcewide_blocked"] += 1
            else:
                counts[source]["unverified"] += 1
        source_counts = counts[source]
        if source_counts["unverified"]:
            unresolved = True
        if source_counts["query_blocked"]:
            unresolved = True
        if source_counts["completed"] and source_counts["completed"] < len(shortlist_top):
            unresolved = True
    if shortlist_top and not any(counts[source]["completed"] for source in REQUIRED_SOURCES):
        unresolved = True
    return counts, unresolved


def validate_research(
    *,
    shortlist_path: str | Path,
    scores_path: str | Path,
    valuation_path: str | Path,
    valuation_evidence_path: str | Path,
    trademark_evidence_path: str | Path,
    trademark_summary_path: str | Path,
    opportunities_path: str | Path,
    top_n: int = 100,
    candidates_path: str | Path = DEFAULT_CANDIDATES_PATH,
) -> int:
    """Validate artifact structure and flag unresolved live-search coverage."""

    try:
        shortlist_rows = _read_csv(shortlist_path, set(SHORTLIST_FIELDS), "shortlist")
        scores_rows = _read_csv(scores_path, set(SCORE_FIELDS), "score")
        valuation_rows = _read_csv(valuation_path, set(VALUATION_FIELDS), "valuation")
        valuation_evidence_rows, valuation_evidence = read_valuation_evidence(valuation_evidence_path)
        trademark_evidence_rows, trademark_evidence = read_trademark_evidence(trademark_evidence_path)
        candidate_map, query_manifest = read_candidate_context(candidates_path)
        summary_map = read_trademark_summary(
            trademark_summary_path,
            evidence_path=trademark_evidence_path,
            candidate_domains=set(candidate_map),
            candidates_path=candidates_path,
        )
        opportunities_rows = _read_csv(opportunities_path, set(OPPORTUNITY_FIELDS), "opportunities")

        shortlist = _unique_by_domain(shortlist_rows, "shortlist")
        scores = _unique_by_domain(scores_rows, "score")
        valuations = _unique_by_domain(valuation_rows, "valuation")
        opportunities = _unique_by_domain(opportunities_rows, "opportunities")
        expected_domains = set(shortlist)
        if set(valuations) != expected_domains or set(opportunities) != expected_domains:
            raise ValueError("final shortlist, valuations, and opportunities domain sets differ")
        ranks = {row["domain"].casefold(): int(row["rank"]) for row in shortlist_rows}
        if sorted(ranks.values()) != list(range(1, len(shortlist_rows) + 1)):
            raise ValueError("shortlist ranks must be unique and contiguous from 1")
        if any(int(row["rank"]) != index for index, row in enumerate(shortlist_rows, start=1)):
            raise ValueError("shortlist row order does not match its rank column")
        if len(shortlist_rows) > SHORTLIST_LIMIT:
            raise ValueError(f"shortlist exceeds the {SHORTLIST_LIMIT}-domain cap")
        category_counts: dict[str, int] = {}
        for row in shortlist_rows:
            category_counts[row["category"]] = category_counts.get(row["category"], 0) + 1
        if any(count > CATEGORY_LIMIT for count in category_counts.values()):
            raise ValueError(f"shortlist exceeds the {CATEGORY_LIMIT}-domain category cap")

        ordered_by_score = sorted(
            shortlist_rows,
            key=lambda row: (
                -_decimal(row["total"], "shortlist total"),
                len(row["domain"].casefold().removesuffix(".si")),
                row["domain"].casefold(),
            ),
        )
        if [row["domain"].casefold() for row in shortlist_rows] != [
            row["domain"].casefold() for row in ordered_by_score
        ]:
            raise ValueError("shortlist order does not match score, label length, and domain ranking")

        for domain, shortlist_row in shortlist.items():
            score_row = scores.get(domain)
            if score_row is None:
                raise ValueError(f"shortlist domain is missing a score row: {domain}")
            candidate = candidate_map.get(domain)
            if candidate is None:
                raise ValueError(f"shortlist domain is missing candidate metadata: {domain}")
            if score_row["category"] != candidate["category"] or shortlist_row["category"] != candidate["category"]:
                raise ValueError(f"shortlist category does not match candidate and score rows for {domain}")
            for field in ("category", "total", "rationale", *SCORE_WEIGHTS):
                if shortlist_row.get(field, "") != score_row.get(field, ""):
                    raise ValueError(f"shortlist {field} does not match score row for {domain}")
        if not set(summary_map).issubset(scores):
            raise ValueError("trademark summary contains a domain missing from scores")

        for row in scores_rows:
            components: dict[str, int] = {}
            for name in SCORE_WEIGHTS:
                try:
                    components[name] = int(row[name])
                except ValueError as exc:
                    raise ValueError(f"invalid {name} score for {row['domain']}") from exc
                if not 0 <= components[name] <= 100:
                    raise ValueError(f"{name} score is out of bounds for {row['domain']}")
            domain = row["domain"].casefold()
            summary = summary_map.get(domain)
            expected_trademark = int(summary["trademark_score"]) if summary else 70
            if components["trademark"] != expected_trademark:
                expected_state = summary["status"] if summary else "not yet screened"
                raise ValueError(
                    f"trademark score for {domain} does not match {expected_state} evidence ({expected_trademark})"
                )
            expected_total = weighted_total(components)
            if _decimal(row["total"], "score total") != expected_total:
                raise ValueError(f"weighted score total mismatch for {row['domain']}")

        eligible_ids_by_domain: dict[str, set[str]] = {}
        shortlist_category = {row["domain"].casefold(): row["category"] for row in shortlist_rows}
        for domain in expected_domains:
            eligible_ids_by_domain[domain] = {
                row["evidence_id"]
                for row in eligible_comps(domain, shortlist_category[domain], valuation_evidence_rows)
            }
        for row in valuation_rows:
            domain = row["domain"].casefold()
            if row.get("rank") != str(ranks[domain]):
                raise ValueError(f"valuation rank does not match shortlist for {domain}")
            refs = [item for item in row.get("evidence_ids", "").split(";") if item]
            if any(ref not in valuation_evidence for ref in refs):
                raise ValueError(f"unknown valuation evidence reference for {domain}")
            if row["status"] == "supported_speculative_range":
                if not row["currency"] or row["currency"] not in {"GBP", "USD"} or not refs:
                    raise ValueError(f"supported valuation lacks currency or evidence for {domain}")
                if not set(refs).issubset(eligible_ids_by_domain[domain]):
                    raise ValueError(f"supported valuation cites an ineligible comparable for {domain}")
                comp_rows = [valuation_evidence[ref] for ref in refs]
                if any(item["evidence_type"] != "completed_sale" or item["currency"] != row["currency"] for item in comp_rows):
                    raise ValueError(f"supported valuation cites a non-sale or mixed currency for {domain}")
                if len({item["sold_domain"] for item in comp_rows}) < 2:
                    raise ValueError(f"supported valuation needs two distinct completed sales for {domain}")
                low = _decimal(row["low"], "valuation low")
                high = _decimal(row["high"], "valuation high")
                if low <= 0 or high < low:
                    raise ValueError(f"invalid numeric valuation range for {domain}")
            elif row["status"] == "insufficiently supported":
                if row["currency"] or row["low"] or row["high"]:
                    raise ValueError(f"unsupported valuation must not contain a numeric range for {domain}")
            else:
                raise ValueError(f"invalid valuation status for {domain}")

        recomputed = aggregate_trademark_rows(
            trademark_evidence_rows,
            list(summary_map),
            expected_queries_by_domain=query_manifest,
            proof_root=Path(trademark_evidence_path).parent,
        )
        for row in recomputed:
            domain = row["domain"]
            if any(summary_map[domain].get(key, "") != row.get(key, "") for key in ("status", "trademark_score", "evidence_ids", "coverage")):
                raise ValueError(f"trademark summary does not match evidence for {domain}")

        for domain, row in opportunities.items():
            shortlist_row = shortlist[domain]
            for field in SHORTLIST_FIELDS:
                if row.get(field, "") != shortlist_row.get(field, ""):
                    raise ValueError(f"opportunity {field} does not match shortlist for {domain}")
            valuation = valuations[domain]
            if any(row[f"valuation_{name}"] != valuation[name] for name in ("status", "currency", "low", "high", "evidence_ids", "rationale")):
                raise ValueError(f"opportunity valuation provenance does not match valuation artifact for {domain}")
            summary = summary_map.get(domain)
            expected_status = summary["status"] if summary else "not yet screened"
            if row["trademark_status"] != expected_status:
                raise ValueError(f"opportunity trademark status does not match summary for {domain}")
            if summary and (row["trademark_coverage"] != summary["coverage"] or row["trademark_evidence_ids"] != summary["evidence_ids"]):
                raise ValueError(f"opportunity trademark provenance does not match summary for {domain}")
            if summary is None and (row["trademark_coverage"] or row["trademark_evidence_ids"]):
                raise ValueError(f"unscreened opportunity has fabricated trademark provenance for {domain}")

        top_rows = sorted(shortlist_rows, key=lambda row: int(row["rank"]))[: min(top_n, len(shortlist_rows))]
        missing = [row["domain"] for row in top_rows if row["domain"].casefold() not in summary_map]
        counts, unresolved = _screening_counts(
            top_rows,
            trademark_evidence_rows,
            query_manifest,
            Path(trademark_evidence_path).parent,
        )
        count_text = "; ".join(
            f"{source}: completed_queries={counts[source]['completed']}, "
            f"sourcewide_blocked_domains={counts[source]['sourcewide_blocked']}, "
            f"query_blocked_domains={counts[source]['query_blocked']}, "
            f"unverified_or_missing_domains={counts[source]['unverified']}"
            for source in REQUIRED_SOURCES
        )
        print(f"Research structure PASS: {len(shortlist_rows)} shortlist rows; {len(valuation_rows)} valuations; {len(opportunities_rows)} joined rows.")
        print(f"Final top-{len(top_rows)} trademark query coverage: {count_text}")
        if missing:
            unresolved = True
            print(f"Unresolved top-{len(top_rows)} domains without a trademark summary: {', '.join(missing[:10])}")
        if unresolved:
            print("BLOCKED: required trademark query coverage is unresolved; blocked attempts do not count as completed per-domain searches.", file=sys.stderr)
            return 2
        print("Research validation PASS: top shortlist screen coverage is complete for accessible specified sources.")
        return 0
    except (OSError, ValueError) as exc:
        print(f"Research validation failed: {exc}", file=sys.stderr)
        return 2

