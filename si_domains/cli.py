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

from . import rdap, rules
from .config import DATA_DIR
from .evidence import EvidenceStore
from .rdap import RegistryInaccessible, check_domain
from .candidates.build import CATEGORIES, default_output, generate_all, write_csv


MONOTONIC = time.monotonic
SLEEP = time.sleep
_RULE_CLASSIFICATIONS = frozenset(
    {"invalid_syntax", "reserved", "restricted", "premium"}
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

    status = subparsers.add_parser("status", help="summarize local candidates and RDAP evidence")
    status.add_argument(
        "--input",
        default=str(DATA_DIR / "candidates.csv"),
        help="CSV with domain_label and category columns",
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


def _run_status(args: argparse.Namespace) -> int:
    candidates = _load_candidates(Path(args.input))
    if candidates is None:
        return 2

    latest = EvidenceStore().load_latest()
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
    if args.command == "status":
        return _run_status(args)
    if args.command == "candidates":
        return _run_candidates(args, parser)
    parser.error("unknown command")
    return 2
