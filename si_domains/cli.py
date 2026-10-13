"""Command-line entry point for checking candidate .si domain labels."""

from __future__ import annotations

import argparse
import csv
import math
import sys
import time
from collections import Counter
from pathlib import Path
from typing import Sequence

import requests

from . import rdap, rules, whois
from .config import DATA_DIR, EVIDENCE_PATH, OUTPUT_DIR, WHOIS_EVIDENCE_PATH
from .evidence import EvidenceStore, WhoisEvidenceStore
from .rdap import RegistryInaccessible, check_domain
from .candidates.build import CATEGORIES, default_output, generate_all, write_csv


MONOTONIC = time.monotonic
SLEEP = time.sleep
_RULE_CLASSIFICATIONS = frozenset(
    {"invalid_syntax", "reserved", "restricted", "premium"}
)
_WHOIS_RETRY_ERRORS = frozenset({"connection_error", "timeout", "empty_response"})


def _positive_limit(value: str) -> int:
    try:
        limit = int(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("limit must be a positive integer") from exc
    if limit < 1:
        raise argparse.ArgumentTypeError("limit must be a positive integer")
    return limit


def _positive_minutes(value: str) -> float:
    try:
        minutes = float(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("max-minutes must be a positive number") from exc
    if not math.isfinite(minutes) or minutes <= 0:
        raise argparse.ArgumentTypeError("max-minutes must be a positive number")
    return minutes


def _nonnegative_seconds(value: str) -> float:
    try:
        seconds = float(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("cooldown-seconds must be non-negative") from exc
    if not math.isfinite(seconds) or seconds < 0:
        raise argparse.ArgumentTypeError("cooldown-seconds must be non-negative")
    return seconds


def _minimum_interval(value: str) -> float:
    try:
        seconds = float(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(
            "min-interval must be a finite number of at least 1 second"
        ) from exc
    if not math.isfinite(seconds) or seconds < 1.0:
        raise argparse.ArgumentTypeError(
            "min-interval must be a finite number of at least 1 second"
        )
    return seconds


def _load_candidates(input_path: Path) -> list[tuple[str, str]] | None:
    if not input_path.is_file():
        print(f"Input CSV not found: {input_path}", file=sys.stderr)
        return None

    candidates: list[tuple[str, str]] = []
    seen: set[str] = set()
    with input_path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        required = {"domain_label", "category"}
        if not reader.fieldnames or not required.issubset(reader.fieldnames):
            print("Input CSV must include domain_label and category columns", file=sys.stderr)
            return None
        for row in reader:
            label = (row.get("domain_label") or "").strip()
            if not label:
                continue
            domain = f"{label}.si"
            if domain in seen:
                continue
            seen.add(domain)
            candidates.append((label, (row.get("category") or "").strip()))
    return candidates


def _remaining_unverified(candidates: list[tuple[str, str]], store: EvidenceStore) -> int:
    latest = store.load_latest()
    count = 0
    for label, _category in candidates:
        if rules.classify(label) != "ok":
            continue
        row = latest.get(f"{label}.si")
        if row is None or row.get("classification") not in {
            "registered",
            "potentially_unregistered",
        }:
            count += 1
    return count


def _progress_line(
    checked: int,
    skipped: int,
    total: int,
    requests_started: int,
    started: float,
) -> str:
    elapsed = max(0.0, MONOTONIC() - started)
    requests_per_minute = requests_started * 60 / elapsed if elapsed else 0.0
    remaining = max(0, total - checked - skipped)
    if requests_per_minute and checked:
        average_attempts = requests_started / checked
        eta_minutes = remaining * average_attempts / requests_per_minute
        eta = f"{eta_minutes * 60:.0f} sec" if eta_minutes < 1 else f"{eta_minutes:.1f} min"
    else:
        eta = "unknown"
    return (
        f"Checked {checked} domains; {requests_per_minute:.1f} requests/min; "
        f"ETA {eta}"
    )


def _time_budget_expired(args: argparse.Namespace, started: float) -> bool:
    return (
        args.max_minutes is not None
        and MONOTONIC() - started >= args.max_minutes * 60
    )


class WhoisRateLimiter:
    """Serialize WHOIS query starts and adapt to sustained failures."""

    def __init__(self, min_interval: float) -> None:
        self.configured_min_interval = float(min_interval)
        if (
            not math.isfinite(self.configured_min_interval)
            or self.configured_min_interval < 1.0
        ):
            raise ValueError("min_interval must be a finite number of at least 1 second")
        self.min_interval = self.configured_min_interval
        self._last_start: float | None = None
        self._consecutive_failures = 0
        self._consecutive_successes = 0

    def wait(self, *, deadline: float | None = None) -> bool:
        now = MONOTONIC()
        while self._last_start is not None:
            remaining = self.min_interval - (now - self._last_start)
            if remaining <= 0:
                break
            if deadline is not None:
                budget_remaining = deadline - now
                if budget_remaining <= 0:
                    return False
                if remaining >= budget_remaining:
                    SLEEP(budget_remaining)
                    return False
            SLEEP(remaining)
            now = MONOTONIC()
        now = MONOTONIC()
        if deadline is not None and now >= deadline:
            return False
        self._last_start = now
        return True

    def increase_after_failure(self) -> None:
        self.min_interval = max(
            self.configured_min_interval,
            min(6.0, self.min_interval * 1.5),
        )

    def record_failure(self, *, rate_limited: bool = False) -> None:
        self._consecutive_failures += 1
        self._consecutive_successes = 0
        if rate_limited or self._consecutive_failures >= 2:
            self.increase_after_failure()

    def record_success(self) -> None:
        self._consecutive_failures = 0
        self._consecutive_successes += 1
        if self._consecutive_successes % 50 == 0:
            self.min_interval = max(
                self.configured_min_interval,
                self.min_interval / 1.5,
            )


def _print_time_budget(checked: int, skipped: int) -> None:
    print(
        f"Time budget reached after checking {checked} domains; "
        f"skipped {skipped} previously recorded domains"
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="python -m si_domains")
    subparsers = parser.add_subparsers(dest="command", required=True)
    check = subparsers.add_parser("check", help="check candidate labels against RDAP")
    check.add_argument("--input", required=True, help="CSV with domain_label and category columns")
    check.add_argument("--limit", type=_positive_limit)
    check.add_argument("--max-minutes", type=_positive_minutes)
    check.add_argument("--min-interval", type=_minimum_interval, default=1.0)
    check.add_argument("--cooldown-seconds", type=_nonnegative_seconds, default=300)
    check.add_argument("--retry-unverified", action="store_true")
    check.add_argument(
        "--stop-on-unverified",
        action="store_true",
        help="stop after the first unverified result (useful for a bounded live smoke check)",
    )

    whois_check = subparsers.add_parser(
        "whois-check", help="second-check RDAP 404 domains through WHOIS"
    )
    whois_check.add_argument(
        "--input",
        default=str(DATA_DIR / "candidates.csv"),
        help="CSV with domain_label and category columns",
    )
    whois_check.add_argument(
        "--rdap-evidence",
        default=str(EVIDENCE_PATH),
        help="latest-row RDAP evidence CSV used to select domains",
    )
    whois_check.add_argument(
        "--evidence",
        default=str(WHOIS_EVIDENCE_PATH),
        help="append-only WHOIS evidence CSV",
    )
    whois_check.add_argument("--limit", type=_positive_limit)
    whois_check.add_argument("--max-minutes", type=_positive_minutes)
    whois_check.add_argument("--min-interval", type=_minimum_interval, default=2.0)
    whois_check.add_argument("--cooldown-seconds", type=_nonnegative_seconds, default=300)
    whois_check.add_argument("--retry-unverified", action="store_true")

    status = subparsers.add_parser("status", help="summarize local candidates and RDAP evidence")
    status.add_argument(
        "--input",
        default=str(DATA_DIR / "candidates.csv"),
        help="CSV with domain_label and category columns",
    )
    status.add_argument(
        "--rdap-evidence", default=str(EVIDENCE_PATH), help="RDAP evidence CSV"
    )
    status.add_argument(
        "--whois-evidence",
        default=str(WHOIS_EVIDENCE_PATH),
        help="optional WHOIS evidence CSV",
    )

    score = subparsers.add_parser("score", help="score latest RDAP-404 candidates offline")
    score.add_argument(
        "--input",
        default=str(DATA_DIR / "candidates.csv"),
        help="candidate feature CSV",
    )
    score.add_argument(
        "--rdap-evidence",
        default=str(EVIDENCE_PATH),
        help="latest-row RDAP evidence CSV",
    )
    score.add_argument(
        "--out",
        default=str(OUTPUT_DIR / "scores.csv"),
        help="score output CSV",
    )
    score.add_argument(
        "--trademark-evidence",
        help="optional researched trademark summary CSV; omit to retain baseline scoring",
    )
    score.add_argument(
        "--trademark-source-evidence",
        default=str(OUTPUT_DIR / "trademark_evidence.csv"),
        help="raw trademark evidence CSV used to validate summary evidence IDs",
    )

    shortlist = subparsers.add_parser(
        "shortlist", help="rank WHOIS-confirmed RDAP-404 domains offline"
    )
    shortlist.add_argument(
        "--input",
        default=str(DATA_DIR / "candidates.csv"),
        help="candidate feature CSV",
    )
    shortlist.add_argument(
        "--rdap-evidence",
        default=str(EVIDENCE_PATH),
        help="latest-row RDAP evidence CSV",
    )
    shortlist.add_argument(
        "--whois-evidence",
        default=str(WHOIS_EVIDENCE_PATH),
        help="latest-row WHOIS evidence CSV",
    )
    shortlist.add_argument(
        "--scores",
        default=str(OUTPUT_DIR / "scores.csv"),
        help="score CSV produced by the score command",
    )
    shortlist.add_argument(
        "--out",
        default=str(OUTPUT_DIR / "shortlist.csv"),
        help="shortlist CSV",
    )
    shortlist.add_argument(
        "--excluded",
        default=str(OUTPUT_DIR / "excluded.csv"),
        help="excluded-domain CSV",
    )
    shortlist.add_argument(
        "--sample-out",
        default=str(OUTPUT_DIR / "sample_404_for_review.csv"),
        help="seeded RDAP-404 review sample CSV",
    )
    shortlist.add_argument(
        "--seed", type=int, default=20261013, help="deterministic sample seed"
    )

    valuations = subparsers.add_parser(
        "valuations", help="write cautious valuation rows from curated sale evidence offline"
    )
    valuations.add_argument("--shortlist", default=str(OUTPUT_DIR / "shortlist.csv"))
    valuations.add_argument("--evidence", default=str(OUTPUT_DIR / "valuation_evidence.csv"))
    valuations.add_argument("--out", default=str(OUTPUT_DIR / "valuations.csv"))

    trademark_summary = subparsers.add_parser(
        "trademark-summary", help="aggregate curated public trademark query evidence offline"
    )
    trademark_summary.add_argument("--shortlist", default=str(OUTPUT_DIR / "shortlist.csv"))
    trademark_summary.add_argument("--candidates", default=str(DATA_DIR / "candidates.csv"))
    trademark_summary.add_argument("--evidence", default=str(OUTPUT_DIR / "trademark_evidence.csv"))
    trademark_summary.add_argument("--out", default=str(OUTPUT_DIR / "trademark_summary.csv"))
    trademark_summary.add_argument("--top-n", type=_positive_limit, default=100)

    opportunities = subparsers.add_parser(
        "opportunities", help="join shortlist, valuation, and trademark provenance offline"
    )
    opportunities.add_argument("--shortlist", default=str(OUTPUT_DIR / "shortlist.csv"))
    opportunities.add_argument("--scores", default=str(OUTPUT_DIR / "scores.csv"))
    opportunities.add_argument("--valuations", default=str(OUTPUT_DIR / "valuations.csv"))
    opportunities.add_argument("--trademark-summary", default=str(OUTPUT_DIR / "trademark_summary.csv"))
    opportunities.add_argument("--out", default=str(OUTPUT_DIR / "opportunities.csv"))

    validate_research = subparsers.add_parser(
        "validate-research", help="validate research artifacts and top shortlist trademark coverage"
    )
    validate_research.add_argument("--shortlist", default=str(OUTPUT_DIR / "shortlist.csv"))
    validate_research.add_argument("--scores", default=str(OUTPUT_DIR / "scores.csv"))
    validate_research.add_argument("--valuations", default=str(OUTPUT_DIR / "valuations.csv"))
    validate_research.add_argument("--valuation-evidence", default=str(OUTPUT_DIR / "valuation_evidence.csv"))
    validate_research.add_argument("--trademark-evidence", default=str(OUTPUT_DIR / "trademark_evidence.csv"))
    validate_research.add_argument("--trademark-summary", default=str(OUTPUT_DIR / "trademark_summary.csv"))
    validate_research.add_argument("--opportunities", default=str(OUTPUT_DIR / "opportunities.csv"))
    validate_research.add_argument("--candidates", default=str(DATA_DIR / "candidates.csv"))
    validate_research.add_argument("--top-n", type=_positive_limit, default=100)
    validate_research.add_argument(
        "--completion-mode",
        action="store_true",
        help="validate complete, evidence-backed outcomes without requiring every source search to finish",
    )

    delivery_inputs = {
        "candidates": DATA_DIR / "candidates.csv",
        "reserved_names": DATA_DIR / "reserved_names.csv",
        "restricted_names": DATA_DIR / "restricted_names.csv",
        "rdap_evidence": OUTPUT_DIR / "rdap_evidence.csv",
        "whois_evidence": OUTPUT_DIR / "whois_evidence.csv",
        "scores": OUTPUT_DIR / "scores.csv",
        "shortlist": OUTPUT_DIR / "shortlist.csv",
        "excluded": OUTPUT_DIR / "excluded.csv",
        "opportunities": OUTPUT_DIR / "opportunities.csv",
        "valuations": OUTPUT_DIR / "valuations.csv",
        "valuation_evidence": OUTPUT_DIR / "valuation_evidence.csv",
        "trademark_summary": OUTPUT_DIR / "trademark_summary.csv",
        "trademark_evidence": OUTPUT_DIR / "trademark_evidence.csv",
        "sample": OUTPUT_DIR / "sample_404_for_review.csv",
    }
    export = subparsers.add_parser(
        "export", help="build the ranked owner-readable XLSX from local CSV snapshots"
    )
    export.add_argument("--out", default=str(OUTPUT_DIR / "si_domains_ranked.xlsx"))
    for name, default in delivery_inputs.items():
        export.add_argument(f"--{name.replace('_', '-')}", dest=f"delivery_{name}", default=str(default))

    validate_delivery = subparsers.add_parser(
        "validate-delivery", help="check an XLSX against every current local source row"
    )
    validate_delivery.add_argument(
        "--workbook", default=str(OUTPUT_DIR / "si_domains_ranked.xlsx")
    )
    for name, default in delivery_inputs.items():
        validate_delivery.add_argument(f"--{name.replace('_', '-')}", dest=f"delivery_{name}", default=str(default))

    candidates = subparsers.add_parser("candidates", help="build or review offline .si label candidates")
    selection = candidates.add_mutually_exclusive_group()
    selection.add_argument("--category", choices=CATEGORIES, help="write one candidate category")
    selection.add_argument("--all", action="store_true", help="write every category")
    candidates.add_argument("--out", help="output CSV; with --all, combine categories in one file")
    candidates.add_argument("--sample", type=_positive_limit, help="print a random sample from each category")
    candidates.add_argument("--seed", type=int, default=1, help="deterministic review sample seed")
    return parser


def _run_check(args: argparse.Namespace) -> int:
    input_path = Path(args.input)
    started = MONOTONIC()
    candidates = _load_candidates(input_path)
    if candidates is None:
        return 2

    store = EvidenceStore()
    checked = 0
    skipped = 0
    requests_started = 0
    cooldown_cycles = 0
    cooldown_waits = 0
    awaiting_cooldown_result = False
    rate_limiter = rdap.RateLimiter(min_interval=args.min_interval)
    try:
        with requests.Session() as session:
            for label, category in candidates:
                if _time_budget_expired(args, started):
                    _print_time_budget(checked, skipped)
                    return 0

                domain = f"{label}.si"
                if store.should_skip(domain, retry_unverified=args.retry_unverified):
                    skipped += 1
                    continue
                if args.limit is not None and checked >= args.limit:
                    break

                try:
                    result = check_domain(
                        label,
                        session=session,
                        rate_limiter=rate_limiter,
                    )
                except RegistryInaccessible as exc:
                    result = exc.result
                    if result is not None:
                        store.append(category, result)
                        checked += 1
                        requests_started += result.attempts
                    if args.stop_on_unverified:
                        print(
                            f"Stopped on unverified result for {domain}; evidence is flushed",
                            file=sys.stderr,
                        )
                        return 2

                    if awaiting_cooldown_result:
                        cooldown_cycles += 1
                        awaiting_cooldown_result = False
                    if cooldown_cycles >= 3:
                        unverified = _remaining_unverified(candidates, store)
                        print(
                            f"Registry inaccessible after {cooldown_cycles} consecutive "
                            f"outage cycles; {unverified} domains unverified",
                            file=sys.stderr,
                        )
                        return 2

                    print(
                        f"RDAP circuit breaker opened; cooling down for "
                        f"{args.cooldown_seconds:g} seconds "
                        f"(cycle {cooldown_cycles + 1}/3)",
                        file=sys.stderr,
                    )
                    cooldown_wait = args.cooldown_seconds
                    if args.max_minutes is not None:
                        remaining_budget = (
                            args.max_minutes * 60 - (MONOTONIC() - started)
                        )
                        if remaining_budget <= 0:
                            rdap.CIRCUIT_BREAKER.reset()
                            _print_time_budget(checked, skipped)
                            return 0
                        cooldown_wait = min(cooldown_wait, remaining_budget)
                    cooldown_waits += 1
                    SLEEP(cooldown_wait)
                    rdap.CIRCUIT_BREAKER.reset()
                    if _time_budget_expired(args, started):
                        _print_time_budget(checked, skipped)
                        return 0
                    awaiting_cooldown_result = True
                    continue

                store.append(category, result)
                checked += 1
                requests_started += result.attempts
                if result.classification in {"registered", "potentially_unregistered"}:
                    cooldown_cycles = 0
                    awaiting_cooldown_result = False
                if args.stop_on_unverified and result.classification == "unverified":
                    print(
                        f"Stopped on unverified result for {domain}: {result.error or 'unknown'}; "
                        "evidence is flushed",
                        file=sys.stderr,
                    )
                    return 2
                if checked and checked % 50 == 0:
                    print(
                        _progress_line(
                            checked,
                            skipped,
                            len(candidates),
                            requests_started,
                            started,
                        ),
                        file=sys.stderr,
                    )
    except KeyboardInterrupt:
        print(f"Interrupted after {checked} checked domains; evidence is flushed", file=sys.stderr)
        return 130
    finally:
        elapsed = max(0.0, MONOTONIC() - started)
        requests_per_minute = requests_started * 60 / elapsed if elapsed else 0.0
        print(
            f"Run totals: {requests_started} requests; {requests_per_minute:.1f} requests/min; "
            f"{rate_limiter.rate_limited_responses} HTTP 429 responses; "
            f"{cooldown_waits} cooldown cycles"
        )

    print(f"Checked {checked} domains; skipped {skipped} previously recorded domains")
    return 0


def _run_whois_check(args: argparse.Namespace) -> int:
    input_path = Path(args.input)
    rdap_path = Path(args.rdap_evidence)
    evidence_path = Path(args.evidence)
    started = MONOTONIC()
    candidates = _load_candidates(input_path)
    if candidates is None:
        return 2
    if not rdap_path.is_file():
        print(f"RDAP evidence CSV not found: {rdap_path}", file=sys.stderr)
        return 2

    rdap_latest = EvidenceStore(rdap_path).load_latest()
    eligible = [
        (label, category)
        for label, category in candidates
        if rdap_latest.get(f"{label}.si", {}).get("classification")
        == "potentially_unregistered"
    ]
    store = WhoisEvidenceStore(evidence_path)
    checked = 0
    skipped = 0
    requests_started = 0
    retries = 0
    cooldown_cycles = 0
    cooldown_waits = 0
    awaiting_cooldown_result = False
    consecutive_unverified = 0
    results: Counter[str] = Counter()
    attempt_errors: Counter[str] = Counter()
    final_errors: Counter[str] = Counter()
    limiter = WhoisRateLimiter(args.min_interval)
    deadline = (
        started + args.max_minutes * 60 if args.max_minutes is not None else None
    )

    try:
        for label, category in eligible:
            if _time_budget_expired(args, started):
                _print_time_budget(checked, skipped)
                return 0

            domain = f"{label}.si"
            if store.should_skip(domain, retry_unverified=args.retry_unverified):
                skipped += 1
                continue
            if args.limit is not None and checked >= args.limit:
                break
            attempt = 0
            while True:
                if not limiter.wait(deadline=deadline):
                    _print_time_budget(checked, skipped)
                    return 0

                if attempt:
                    retries += 1
                result = whois.whois_check(
                    label,
                    connect=whois.socket.create_connection,
                )
                attempt += 1
                requests_started += 1
                if result.error:
                    attempt_errors[result.error] += 1

                if result.error not in _WHOIS_RETRY_ERRORS or attempt >= 3:
                    break

                backoff = (10.0, 30.0)[attempt - 1]
                if deadline is not None:
                    remaining_budget = deadline - MONOTONIC()
                    if remaining_budget <= 0:
                        _print_time_budget(checked, skipped)
                        return 0
                    if remaining_budget <= backoff:
                        SLEEP(remaining_budget)
                        _print_time_budget(checked, skipped)
                        return 0
                SLEEP(backoff)

            store.append(category, result)
            checked += 1
            results[result.classification] += 1
            if result.error:
                final_errors[result.error] += 1

            if result.classification in {"not_registered", "registered"}:
                limiter.record_success()
                consecutive_unverified = 0
                cooldown_cycles = 0
                awaiting_cooldown_result = False
            else:
                limiter.record_failure(rate_limited=result.error == "rate_limited")
                consecutive_unverified += 1

            if checked and checked % 50 == 0:
                print(
                    _progress_line(
                        checked,
                        skipped,
                        len(eligible),
                        requests_started,
                        started,
                    ),
                    file=sys.stderr,
                )

            rate_limited = result.error == "rate_limited"
            if not rate_limited and consecutive_unverified < 3:
                continue

            if awaiting_cooldown_result:
                cooldown_cycles += 1
                awaiting_cooldown_result = False
            if cooldown_cycles >= 3:
                print(
                    "WHOIS server remained unavailable after 3 consecutive "
                    "cooldown cycles without a successful result; stopping",
                    file=sys.stderr,
                )
                return 2

            reason = (
                "rate-limited notice"
                if rate_limited
                else "3 consecutive domains finished unverified"
            )
            print(
                f"WHOIS circuit breaker opened after {reason}; cooling down for "
                f"{args.cooldown_seconds:g} seconds "
                f"(cycle {cooldown_cycles + 1}/3)",
                file=sys.stderr,
            )
            cooldown_wait = args.cooldown_seconds
            if deadline is not None:
                remaining_budget = deadline - MONOTONIC()
                if remaining_budget <= 0:
                    _print_time_budget(checked, skipped)
                    return 0
                cooldown_wait = min(cooldown_wait, remaining_budget)
            cooldown_waits += 1
            SLEEP(cooldown_wait)
            if _time_budget_expired(args, started):
                _print_time_budget(checked, skipped)
                return 0
            consecutive_unverified = 0
            awaiting_cooldown_result = True
    except KeyboardInterrupt:
        print(
            f"Interrupted after {checked} WHOIS checks; evidence is flushed",
            file=sys.stderr,
        )
        return 130
    finally:
        elapsed = max(0.0, MONOTONIC() - started)
        requests_per_minute = requests_started * 60 / elapsed if elapsed else 0.0
        print(
            f"Run totals: {requests_started} WHOIS requests; {retries} retries; "
            f"{requests_per_minute:.1f} requests/min; {cooldown_waits} cooldown cycles; "
            f"adaptive interval {limiter.min_interval:g} seconds"
        )
        print(
            "Run results: "
            f"not_registered={results['not_registered']}, "
            f"registered={results['registered']}, "
            f"unverified={results['unverified']}"
        )
        if attempt_errors:
            print(
                "WHOIS attempt error codes: "
                + ", ".join(
                    f"{error}={count}" for error, count in sorted(attempt_errors.items())
                )
            )
        if final_errors:
            print(
                "WHOIS final error codes: "
                + ", ".join(
                    f"{error}={count}" for error, count in sorted(final_errors.items())
                )
            )

    print(
        f"Checked {checked} WHOIS domains; skipped {skipped} previously recorded "
        "RDAP-404 domains"
    )
    return 0


def _run_status(args: argparse.Namespace) -> int:
    candidates = _load_candidates(Path(args.input))
    if candidates is None:
        return 2

    latest = EvidenceStore(Path(args.rdap_evidence)).load_latest()
    counts: Counter[str] = Counter()
    unverified: Counter[str] = Counter()
    timestamps: list[str] = []
    unchecked = 0
    for label, _category in candidates:
        domain = f"{label}.si"
        row = latest.get(domain)
        if row is not None:
            timestamp = row.get("utc_timestamp", "")
            if timestamp:
                timestamps.append(timestamp)
        rule_class = rules.classify(label)
        if rule_class in _RULE_CLASSIFICATIONS:
            counts[rule_class] += 1
            continue

        if row is None:
            unchecked += 1
            continue
        classification = row.get("classification", "")
        if classification == "registered":
            counts["registered"] += 1
        elif classification == "potentially_unregistered":
            counts["potentially_unregistered"] += 1
        elif classification in _RULE_CLASSIFICATIONS:
            counts[classification] += 1
        elif classification == "unverified":
            unverified[row.get("error") or "unspecified_error"] += 1
        else:
            unchecked += 1

    print(f"Candidates: {len(candidates)}")
    print(f"Registered: {counts['registered']}")
    print(f"Potentially unregistered: {counts['potentially_unregistered']}")
    if unverified:
        for error, count in sorted(unverified.items()):
            print(f"Unverified {error}: {count}")
    else:
        print("Unverified: 0")
    print(f"Invalid: {counts['invalid_syntax']}")
    print(f"Reserved: {counts['reserved']}")
    print(f"Restricted: {counts['restricted']}")
    print(f"Premium: {counts['premium']}")
    print(f"Candidates unchecked: {unchecked}")
    print(f"Oldest evidence timestamp: {min(timestamps) if timestamps else 'none'}")
    print(f"Newest evidence timestamp: {max(timestamps) if timestamps else 'none'}")
    whois_path = Path(args.whois_evidence)
    if whois_path.is_file():
        whois_latest = WhoisEvidenceStore(whois_path).load_latest()
        rdap_404_domains = [
            f"{label}.si"
            for label, _category in candidates
            if latest.get(f"{label}.si", {}).get("classification")
            == "potentially_unregistered"
        ]
        whois_counts: Counter[str] = Counter()
        cross_counts: Counter[str] = Counter()
        for domain in rdap_404_domains:
            row = whois_latest.get(domain)
            classification = row.get("classification", "") if row else ""
            if classification not in {"not_registered", "registered", "unverified"}:
                classification = "not yet checked"
            whois_counts[classification] += 1
            if classification == "not_registered":
                cross_counts["confirmed"] += 1
            elif classification == "registered":
                cross_counts["conflict"] += 1
            else:
                cross_counts["pending"] += 1

        print("WHOIS second check (RDAP-404 domains):")
        print(f"WHOIS not_registered: {whois_counts['not_registered']}")
        print(f"WHOIS registered: {whois_counts['registered']}")
        print(f"WHOIS unverified: {whois_counts['unverified']}")
        print(f"WHOIS not yet checked: {whois_counts['not yet checked']}")
        print(
            "Confirmed available (two channels): "
            f"{cross_counts['confirmed']}"
        )
        print(f"Conflicts (RDAP 404 but WHOIS registered): {cross_counts['conflict']}")
        print(f"Pending/unverified: {cross_counts['pending']}")
    return 0


def _run_candidates(args: argparse.Namespace, parser: argparse.ArgumentParser) -> int:
    if args.sample is not None:
        if args.category is not None or args.all or args.out:
            parser.error("--sample cannot be combined with --category, --all, or --out")
        from .candidates.review import render_sample

        print(render_sample(args.sample, args.seed), end="")
        return 0

    if args.category is None and not args.all:
        parser.error("candidates requires --category <name>, --all, or --sample <count>")

    generated = generate_all()
    if args.all:
        if args.out:
            rows = [candidate for category in CATEGORIES for candidate in generated[category]]
            count = write_csv(args.out, rows)
            print(f"Wrote {count} candidates to {args.out}")
        else:
            for category in CATEGORIES:
                output = default_output(category)
                count = write_csv(output, generated[category])
                print(f"Wrote {count} {category} candidates to {output}")
        return 0

    category = args.category
    output = args.out if args.out else default_output(category)
    count = write_csv(output, generated[category])
    print(f"Wrote {count} {category} candidates to {output}")
    return 0


def _run_score(args: argparse.Namespace) -> int:
    from .scoring import write_scores

    try:
        count = write_scores(
            args.input,
            args.rdap_evidence,
            args.out,
            trademark_evidence_path=args.trademark_evidence,
            trademark_source_evidence_path=args.trademark_source_evidence,
        )
    except (OSError, ValueError) as exc:
        print(f"Score failed: {exc}", file=sys.stderr)
        return 2
    print(f"Wrote scores for {count} RDAP-404 domains to {args.out}")
    return 0


def _run_shortlist(args: argparse.Namespace) -> int:
    from .shortlist import build_outputs

    try:
        shortlisted, excluded, sampled = build_outputs(
            args.input,
            args.rdap_evidence,
            args.whois_evidence,
            args.scores,
            args.out,
            args.excluded,
            args.sample_out,
            seed=args.seed,
        )
    except (OSError, ValueError) as exc:
        print(f"Shortlist failed: {exc}", file=sys.stderr)
        return 2
    print(
        f"Wrote {shortlisted} shortlist domains, {excluded} exclusions, "
        f"and {sampled} review sample rows"
    )
    return 0


def _run_valuations(args: argparse.Namespace) -> int:
    from .valuation import write_valuations

    try:
        count = write_valuations(args.shortlist, args.evidence, args.out)
    except (OSError, ValueError) as exc:
        print(f"Valuations failed: {exc}", file=sys.stderr)
        return 2
    print(f"Wrote {count} valuation rows to {args.out}")
    return 0


def _run_trademark_summary(args: argparse.Namespace) -> int:
    from .trademarks import write_trademark_summary

    try:
        count = write_trademark_summary(
            args.evidence,
            args.shortlist,
            args.out,
            top_n=args.top_n,
            candidates_path=args.candidates,
        )
    except (OSError, ValueError) as exc:
        print(f"Trademark summary failed: {exc}", file=sys.stderr)
        return 2
    print(f"Wrote {count} trademark summary rows to {args.out}")
    return 0


def _run_opportunities(args: argparse.Namespace) -> int:
    from .research import write_opportunities

    try:
        count = write_opportunities(
            args.shortlist, args.scores, args.valuations, args.trademark_summary, args.out
        )
    except (OSError, ValueError) as exc:
        print(f"Opportunities build failed: {exc}", file=sys.stderr)
        return 2
    print(f"Wrote {count} joined opportunity rows to {args.out}")
    return 0


def _run_validate_research(args: argparse.Namespace) -> int:
    from .research import validate_research

    return validate_research(
        shortlist_path=args.shortlist,
        scores_path=args.scores,
        valuation_path=args.valuations,
        valuation_evidence_path=args.valuation_evidence,
        trademark_evidence_path=args.trademark_evidence,
        trademark_summary_path=args.trademark_summary,
        opportunities_path=args.opportunities,
        top_n=args.top_n,
        candidates_path=args.candidates,
        completion_mode=args.completion_mode,
    )


def _delivery_paths(args: argparse.Namespace) -> dict[str, str]:
    return {
        name: getattr(args, f"delivery_{name}")
        for name in (
            "candidates", "reserved_names", "restricted_names", "rdap_evidence",
            "whois_evidence", "scores", "shortlist", "excluded", "opportunities",
            "valuations", "valuation_evidence", "trademark_summary", "trademark_evidence",
            "sample",
        )
    }


def _run_export(args: argparse.Namespace) -> int:
    from .workbook import build_workbook_model, export_workbook

    try:
        model = build_workbook_model(_delivery_paths(args))
        export_workbook(model, args.out)
    except (OSError, ValueError) as exc:
        print(f"Workbook export failed: {exc}", file=sys.stderr)
        return 2
    counts = ", ".join(f"{name}={len(sheet.rows)}" for name, sheet in model.sheets.items())
    print(f"Wrote offline workbook to {args.out}; snapshot sha256:{model.snapshot_digest}")
    print(f"Sheet rows: {counts}")
    print("XLSX reopened in normal, read-only, and data-only modes.")
    return 0


def _run_validate_delivery(args: argparse.Namespace) -> int:
    from .delivery import validate_delivery

    try:
        report = validate_delivery(args.workbook, _delivery_paths(args))
    except (OSError, ValueError) as exc:
        print(f"Delivery validation failed: {exc}", file=sys.stderr)
        return 2
    print(
        f"Structural delivery PASS: {report.candidate_count} candidates; "
        f"{report.shortlist_count} ranked opportunities; snapshot sha256:{report.snapshot_digest}."
    )
    if report.research_unresolved:
        details = "; ".join(
            f"{source} {values['completed']} completed, "
            f"{values['sourcewide_blocked']} source-wide blocked, "
            f"{values['query_blocked']} query blocked, {values['unverified']} unverified/missing"
            for source, values in report.screening_counts.items()
        )
        print(f"Research screening BLOCKED: {details}.")
    else:
        print("Research screening coverage PASS for the specified query scope.")
    print("Project completion not certified; the separate Trio owner gate remains authoritative.")
    print("Sheet rows: " + ", ".join(f"{name}={count}" for name, count in report.sheet_rows.items()))
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.command == "check":
        return _run_check(args)
    if args.command == "whois-check":
        return _run_whois_check(args)
    if args.command == "status":
        return _run_status(args)
    if args.command == "score":
        return _run_score(args)
    if args.command == "shortlist":
        return _run_shortlist(args)
    if args.command == "valuations":
        return _run_valuations(args)
    if args.command == "trademark-summary":
        return _run_trademark_summary(args)
    if args.command == "opportunities":
        return _run_opportunities(args)
    if args.command == "validate-research":
        return _run_validate_research(args)
    if args.command == "export":
        return _run_export(args)
    if args.command == "validate-delivery":
        return _run_validate_delivery(args)
    if args.command == "candidates":
        return _run_candidates(args, parser)
    parser.error("unknown command")
    return 2
