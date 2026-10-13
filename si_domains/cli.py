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
from .config import DATA_DIR, EVIDENCE_PATH, WHOIS_EVIDENCE_PATH
from .evidence import EvidenceStore, WhoisEvidenceStore
from .rdap import RegistryInaccessible, check_domain
from .candidates.build import CATEGORIES, default_output, generate_all, write_csv


MONOTONIC = time.monotonic
SLEEP = time.sleep
_RULE_CLASSIFICATIONS = frozenset(
    {"invalid_syntax", "reserved", "restricted", "premium"}
)
_WHOIS_COOLDOWN_ERRORS = frozenset(
    {"connection_error", "timeout", "empty_response", "rate_limited"}
)


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
    """Serialize WHOIS query starts and adapt after transport failures."""

    def __init__(self, min_interval: float) -> None:
        self.configured_min_interval = float(min_interval)
        if (
            not math.isfinite(self.configured_min_interval)
            or self.configured_min_interval < 1.0
        ):
            raise ValueError("min_interval must be a finite number of at least 1 second")
        self.min_interval = self.configured_min_interval
        self._last_start: float | None = None

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
    cooldown_cycles = 0
    cooldown_waits = 0
    awaiting_cooldown_result = False
    results: Counter[str] = Counter()
    errors: Counter[str] = Counter()
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
            if not limiter.wait(deadline=deadline):
                _print_time_budget(checked, skipped)
                return 0

            result = whois.whois_check(
                label,
                connect=whois.socket.create_connection,
            )
            store.append(category, result)
            checked += 1
            requests_started += 1
            results[result.classification] += 1
            if result.error:
                errors[result.error] += 1
            if result.error in _WHOIS_COOLDOWN_ERRORS:
                limiter.increase_after_failure()

            if result.classification in {"not_registered", "registered"}:
                cooldown_cycles = 0
                awaiting_cooldown_result = False

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

            if result.error not in _WHOIS_COOLDOWN_ERRORS:
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

            print(
                f"WHOIS circuit breaker opened; cooling down for "
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
            f"Run totals: {requests_started} WHOIS requests; "
            f"{requests_per_minute:.1f} requests/min; {cooldown_waits} cooldown cycles; "
            f"adaptive interval {limiter.min_interval:g} seconds"
        )
        print(
            "Run results: "
            f"not_registered={results['not_registered']}, "
            f"registered={results['registered']}, "
            f"unverified={results['unverified']}"
        )
        if errors:
            print(
                "WHOIS error codes: "
                + ", ".join(f"{error}={count}" for error, count in sorted(errors.items()))
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


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.command == "check":
        return _run_check(args)
    if args.command == "whois-check":
        return _run_whois_check(args)
    if args.command == "status":
        return _run_status(args)
    if args.command == "candidates":
        return _run_candidates(args, parser)
    parser.error("unknown command")
    return 2
