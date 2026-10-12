"""Command-line entry point for checking candidate .si domain labels."""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path
from typing import Sequence

import requests

from .evidence import EvidenceStore
from .rdap import RegistryInaccessible, check_domain
from .candidates.build import CATEGORIES, default_output, generate_all, write_csv


def _positive_limit(value: str) -> int:
    try:
        limit = int(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("limit must be a positive integer") from exc
    if limit < 1:
        raise argparse.ArgumentTypeError("limit must be a positive integer")
    return limit


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="python -m si_domains")
    subparsers = parser.add_subparsers(dest="command", required=True)
    check = subparsers.add_parser("check", help="check candidate labels against RDAP")
    check.add_argument("--input", required=True, help="CSV with domain_label and category columns")
    check.add_argument("--limit", type=_positive_limit)
    check.add_argument("--retry-unverified", action="store_true")

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
    if not input_path.is_file():
        print(f"Input CSV not found: {input_path}", file=sys.stderr)
        return 2

    store = EvidenceStore()
    seen: set[str] = set()
    checked = 0
    skipped = 0
    try:
        with input_path.open("r", encoding="utf-8-sig", newline="") as handle:
            reader = csv.DictReader(handle)
            required = {"domain_label", "category"}
            if not reader.fieldnames or not required.issubset(reader.fieldnames):
                print("Input CSV must include domain_label and category columns", file=sys.stderr)
                return 2

            with requests.Session() as session:
                for row in reader:
                    label = (row.get("domain_label") or "").strip()
                    category = (row.get("category") or "").strip()
                    if not label:
                        continue
                    domain = f"{label}.si"
                    if domain in seen:
                        continue
                    seen.add(domain)
                    if store.should_skip(domain, retry_unverified=args.retry_unverified):
                        skipped += 1
                        continue
                    if args.limit is not None and checked >= args.limit:
                        break

                    try:
                        result = check_domain(label, session=session)
                    except RegistryInaccessible as exc:
                        if exc.result is not None:
                            store.append(category, exc.result)
                            checked += 1
                        print(str(exc), file=sys.stderr)
                        return 2
                    store.append(category, result)
                    checked += 1
                    if checked % 50 == 0:
                        print(f"Checked {checked} domains", file=sys.stderr)
    except KeyboardInterrupt:
        print(f"Interrupted after {checked} checked domains; evidence is flushed", file=sys.stderr)
        return 130

    print(f"Checked {checked} domains; skipped {skipped} previously recorded domains")
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
    if args.command == "candidates":
        return _run_candidates(args, parser)
    parser.error("unknown command")
    return 2
