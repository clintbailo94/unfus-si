"""Curated, offline aggregation for public trademark screening evidence."""

from __future__ import annotations

import csv
import re
import unicodedata
from collections import defaultdict
from datetime import datetime
from pathlib import Path, PurePosixPath
from urllib.parse import parse_qsl, urlparse

from .scoring import trademark_score_for_status


DEFAULT_CANDIDATES_PATH = Path(__file__).resolve().parents[1] / "data" / "candidates.csv"


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
    "proof_kind",
    "proof_path",
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
_PROOF_KINDS = frozenset({"screenshot", "official_export"})
_QUERY_PARAMETER_KEYS = frozenset(
    {"q", "query", "search", "searchterm", "searchtext", "term", "text", "word", "input", "mark"}
)
_PHRASE_PREFIXES = {
    "comeand": "come and",
    "lets": "let's",
    "letus": "let us",
    "shallwe": "shall we",
    "tryto": "try to",
    "waitand": "wait and",
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


def normalize_query(value: str) -> str:
    """Normalize case, Unicode width, plus separators, and repeated spaces."""

    normalized = unicodedata.normalize("NFKC", value).casefold().replace("+", " ")
    return " ".join(normalized.split())


def normalize_seed(seed: str) -> str:
    pieces = [normalize_query(piece) for piece in seed.split("+") if normalize_query(piece)]
    if len(pieces) > 1:
        pieces[0] = _PHRASE_PREFIXES.get(pieces[0].replace(" ", ""), pieces[0])
        return normalize_query(" ".join(pieces))
    return normalize_query(seed)


def read_candidate_context(
    path: str | Path = DEFAULT_CANDIDATES_PATH,
) -> tuple[dict[str, dict[str, str]], dict[str, tuple[str, ...]]]:
    """Load candidate metadata and its exact trademark-query manifest."""

    rows = _read_csv(path, {"domain_label", "category", "seed"}, "candidate")
    candidates: dict[str, dict[str, str]] = {}
    queries: dict[str, tuple[str, ...]] = {}
    for row in rows:
        label = normalize_query(row.get("domain_label", ""))
        domain = f"{label}.si"
        if not _DOMAIN.fullmatch(domain) or domain in candidates:
            raise ValueError(f"candidate file has an invalid or duplicate domain label: {label!r}")
        if row.get("category", "").casefold() == "domain_hacks":
            seed = row.get("seed", "").strip()
            if not seed:
                raise ValueError(f"domain-hack candidate has no recorded completion seed: {domain}")
            normalized_seed = normalize_seed(seed)
            if not normalized_seed:
                raise ValueError(f"domain-hack candidate has an invalid completion seed: {domain}")
        candidates[domain] = row
        # The bounded screen covers the exact unspaced domain label only.
        # Recorded completion seeds remain candidate provenance, not an
        # automatic second trademark query or a phonetic variant.
        queries[domain] = (label,)
    return candidates, queries


def _resolve_proof(row: dict[str, str], proof_root: str | Path | None) -> Path | None:
    kind = row.get("proof_kind", "").strip()
    raw_path = row.get("proof_path", "").strip()
    if not kind and not raw_path:
        return None
    evidence_id = row.get("evidence_id", "")
    if not kind or not raw_path:
        raise ValueError(f"trademark proof needs both proof_kind and proof_path: {evidence_id}")
    if kind not in _PROOF_KINDS:
        raise ValueError(f"invalid trademark proof_kind for {evidence_id}")
    if proof_root is None:
        raise ValueError(f"trademark proof cannot be resolved without an output directory: {evidence_id}")
    if "\\" in raw_path or re.match(r"^[a-zA-Z]:", raw_path):
        raise ValueError(f"trademark proof_path must be a relative output path: {evidence_id}")
    relative = PurePosixPath(raw_path)
    if relative.is_absolute() or not relative.parts or any(part in {".", ".."} for part in relative.parts):
        raise ValueError(f"trademark proof_path must stay within the output directory: {evidence_id}")
    root = Path(proof_root).resolve()
    resolved = root.joinpath(*relative.parts).resolve()
    if not resolved.is_relative_to(root) or not resolved.is_file():
        raise ValueError(f"trademark proof file is missing or outside the output directory: {evidence_id}")
    return resolved


def _query_specific_result(row: dict[str, str]) -> bool:
    result_url = row.get("result_url", "").strip()
    if not result_url:
        return False
    source = urlparse(row.get("source_url", ""))
    result = urlparse(result_url)
    source_path = source.path.rstrip("/") or "/"
    result_path = result.path.rstrip("/") or "/"
    if result_path != source_path:
        return True
    expected = normalize_query(row.get("query", ""))
    for key, value in parse_qsl(result.query, keep_blank_values=True):
        normalized_key = re.sub(r"[^a-z]", "", key.casefold())
        if normalized_key in _QUERY_PARAMETER_KEYS and normalize_query(value) == expected:
            return True
    return False


def _has_query_proof(row: dict[str, str]) -> bool:
    return bool(row.get("proof_path", "").strip()) or _query_specific_result(row)


def validate_evidence_rows(
    rows: list[dict[str, str]], proof_root: str | Path | None = None
) -> dict[str, dict[str, str]]:
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
        _resolve_proof(row, proof_root)
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
            if result_url:
                result_host = (urlparse(result_url).hostname or "").casefold()
                if not any(result_host == suffix or result_host.endswith("." + suffix) for suffix in _OFFICIAL_HOSTS[row["source"]]):
                    raise ValueError(f"trademark result URL is not on the official {row['source']} host: {evidence_id}")
            elif not row.get("proof_path", "").strip():
                raise ValueError(f"completed trademark query needs a result URL or proof file: {evidence_id}")
        if row["result_status"] == "possible_conflict" and not (
            row.get("mark_number") or row.get("mark_name")
        ):
            raise ValueError(f"possible-conflict evidence needs an observed mark identifier or name: {evidence_id}")
        indexed[evidence_id] = row
    return indexed


def read_trademark_evidence(path: str | Path) -> tuple[list[dict[str, str]], dict[str, dict[str, str]]]:
    required = set(TRADEMARK_EVIDENCE_FIELDS) - {"proof_kind", "proof_path"}
    rows = _read_csv(path, required, "trademark evidence")
    return rows, validate_evidence_rows(rows, Path(path).parent)


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
        expected = trademark_score_for_status(status)
        if score != expected:
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
    candidates_path: str | Path = DEFAULT_CANDIDATES_PATH,
) -> dict[str, dict[str, str]]:
    rows = _read_csv(path, set(TRADEMARK_SUMMARY_FIELDS), "trademark summary")
    candidates, query_manifest = read_candidate_context(candidates_path)
    evidence_rows: list[dict[str, str]] | None = None
    evidence_index = None
    if evidence_path:
        evidence_rows, evidence_index = read_trademark_evidence(evidence_path)
    known_domains = set(candidates)
    if candidate_domains is not None:
        known_domains &= candidate_domains
    indexed = validate_summary_rows(rows, evidence_index, candidate_domains=known_domains)
    if evidence_rows is not None:
        recomputed = aggregate_trademark_rows(
            evidence_rows,
            list(indexed),
            expected_queries_by_domain=query_manifest,
            proof_root=Path(evidence_path).parent,
        )
        for row in recomputed:
            domain = row["domain"]
            if any(indexed[domain].get(key, "") != row.get(key, "") for key in ("status", "trademark_score", "evidence_ids", "coverage")):
                raise ValueError(f"trademark summary does not match evidence for {domain}")
    return indexed


def aggregate_trademark_rows(
    evidence_rows: list[dict[str, str]],
    domains: list[str],
    *,
    expected_queries_by_domain: dict[str, tuple[str, ...]] | None = None,
    proof_root: str | Path | None = None,
) -> list[dict[str, str]]:
    """Aggregate only complete, query-matched official screens; retain all conflicts."""

    evidence_index = validate_evidence_rows(evidence_rows, proof_root)
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
        expected_queries = (
            expected_queries_by_domain.get(domain)
            if expected_queries_by_domain is not None
            else None
        ) or (normalize_query(domain.removesuffix(".si")),)
        source_coverage = query_coverage_by_source(
            evidence_rows,
            domain,
            expected_queries,
            proof_root=proof_root,
            evidence_index=evidence_index,
        )
        source_states = {source: source_coverage[source]["status"] for source in REQUIRED_SOURCES}
        evidence_ids: list[str] = []
        conflict = False
        query_blocked = False
        for source in REQUIRED_SOURCES:
            actual = by_source_domain.get((source, domain), [])
            global_rows = by_source_global.get(source, [])
            evidence_ids.extend(row["evidence_id"] for row in actual)
            evidence_ids.extend(row["evidence_id"] for row in global_rows)
            conflict = conflict or any(row["result_status"] == "possible_conflict" for row in actual)
            query_blocked = query_blocked or bool(source_coverage[source]["query_blocked"])

        if conflict:
            status = "needs legal review"
        elif all(value == "no_obvious_match" for value in source_states.values()) and not query_blocked:
            status = "limited_screen_no_obvious_match"
        elif "blocked" in source_states.values() or query_blocked:
            status = "blocked"
        else:
            status = "unverified"
        score = trademark_score_for_status(status)

        query_blocked_sources = [
            source for source in REQUIRED_SOURCES if source_coverage[source]["query_blocked"]
        ]
        sourcewide_blocked_sources = [
            source for source in REQUIRED_SOURCES if source_coverage[source]["sourcewide_blocked"]
        ]
        sourcewide_only_sources = [
            source for source in sourcewide_blocked_sources
            if not source_coverage[source]["domain_query_attempted"]
        ]
        sourcewide_mixed_sources = [
            source for source in sourcewide_blocked_sources
            if source_coverage[source]["domain_query_attempted"]
        ]
        limitations = "Exact-word/public UI screen only; no comprehensive phonetic, class, or global coverage."
        if query_blocked_sources:
            limitations += " Required per-domain queries blocked: " + ", ".join(query_blocked_sources) + "."
        if sourcewide_only_sources:
            limitations += " Blocked sources: " + ", ".join(sourcewide_only_sources) + "; no per-domain query ran there."
        if sourcewide_mixed_sources:
            limitations += " Source-wide refusal also prevented missing required queries for: " + ", ".join(sourcewide_mixed_sources) + "."
        if "unverified" in source_states.values():
            unknown_sources = [source for source in REQUIRED_SOURCES if source_states[source] == "unverified"]
            limitations += " Unverified sources: " + ", ".join(unknown_sources) + "; no no-match conclusion."
        coverage = ";".join(
            f"{source}:{source_states[source]}[{source_coverage[source]['completed']}/{source_coverage[source]['required']}]"
            for source in REQUIRED_SOURCES
        )
        for source in REQUIRED_SOURCES:
            missing_queries = source_coverage[source]["missing_queries"]
            if missing_queries:
                limitations += f" {source} incomplete queries: {', '.join(missing_queries)}."
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


def query_coverage_by_source(
    evidence_rows: list[dict[str, str]],
    domain: str,
    expected_queries: tuple[str, ...],
    *,
    proof_root: str | Path | None = None,
    evidence_index: dict[str, dict[str, str]] | None = None,
) -> dict[str, dict[str, object]]:
    """Return required-query completion counts using aggregation's exact rules."""

    indexed = evidence_index or validate_evidence_rows(evidence_rows, proof_root)
    normalized_domain = domain.casefold()
    global_rows: dict[str, list[dict[str, str]]] = defaultdict(list)
    domain_rows: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in indexed.values():
        if row["domain"] == "*":
            global_rows[row["source"]].append(row)
        elif row["domain"].casefold() == normalized_domain:
            domain_rows[row["source"]].append(row)

    required = tuple(dict.fromkeys(normalize_query(query) for query in expected_queries if normalize_query(query)))
    coverage: dict[str, dict[str, object]] = {}
    for source in REQUIRED_SOURCES:
        source_global = sorted(global_rows[source], key=lambda row: (row["utc_timestamp"], row["evidence_id"]))
        global_status = source_global[-1]["result_status"] if source_global else "unverified"
        query_states: dict[str, str] = {}
        sourcewide_blocked = False
        query_blocked = False
        for query in required:
            matches = [row for row in domain_rows[source] if normalize_query(row["query"]) == query]
            if matches:
                latest = max(matches, key=lambda row: (row["utc_timestamp"], row["evidence_id"]))
                state = latest["result_status"]
                query_blocked = query_blocked or state == "blocked"
                if state in {"no_obvious_match", "possible_conflict"} and not _has_query_proof(latest):
                    state = "unverified"
            else:
                state = global_status if global_status in {"blocked", "unverified"} else "unverified"
                sourcewide_blocked = sourcewide_blocked or state == "blocked"
            query_states[query] = state

        completed = sum(
            state in {"no_obvious_match", "possible_conflict"}
            for state in query_states.values()
        )
        missing_queries = [
            query for query, state in query_states.items()
            if state not in {"no_obvious_match", "possible_conflict"}
        ]
        if not required or any(state == "unverified" for state in query_states.values()):
            status = "unverified"
        elif any(state == "blocked" for state in query_states.values()):
            status = "blocked"
        elif any(state == "possible_conflict" for state in query_states.values()):
            status = "possible_conflict"
        elif completed == len(required):
            status = "no_obvious_match"
        else:
            status = "unverified"
        coverage[source] = {
            "status": status,
            "completed": completed,
            "required": len(required),
            "missing_queries": missing_queries,
            "sourcewide_blocked": sourcewide_blocked,
            "query_blocked": query_blocked,
            "domain_query_attempted": bool(domain_rows[source]),
        }
    return coverage


def write_trademark_summary(
    evidence_path: str | Path,
    domains_path: str | Path,
    output_path: str | Path,
    *,
    top_n: int | None = None,
    candidates_path: str | Path = DEFAULT_CANDIDATES_PATH,
) -> int:
    evidence_rows, _index = read_trademark_evidence(evidence_path)
    domain_rows = _read_csv(domains_path, {"domain"}, "domain list")
    candidate_map, query_manifest = read_candidate_context(candidates_path)
    if top_n is not None:
        if top_n < 1:
            raise ValueError("top_n must be positive")
        if all("rank" in row for row in domain_rows):
            domain_rows = sorted(domain_rows, key=lambda row: int(row["rank"]))[:top_n]
        else:
            domain_rows = domain_rows[:top_n]
    domains = [normalize_query(row["domain"]) for row in domain_rows]
    unknown = sorted(set(domains) - set(candidate_map))
    if unknown:
        raise ValueError(f"trademark summary domain is missing candidate metadata: {unknown[0]}")
    summaries = aggregate_trademark_rows(
        evidence_rows,
        domains,
        expected_queries_by_domain=query_manifest,
        proof_root=Path(evidence_path).parent,
    )
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=TRADEMARK_SUMMARY_FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(summaries)
    return len(summaries)

