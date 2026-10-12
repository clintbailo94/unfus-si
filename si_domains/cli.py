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


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.command == "check":
        return _run_check(args)
    parser.error("unknown command")
    return 2
