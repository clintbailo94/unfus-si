"""Continuous refresh logic for .si domain availability and pipeline rebuilding."""

from __future__ import annotations

import csv
import logging
import sys
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Iterable, Sequence

import requests

from . import rdap, whois, scoring, shortlist
from .config import (
    DATA_DIR,
    EVIDENCE_PATH,
    OUTPUT_DIR,
    WHOIS_EVIDENCE_PATH,
)
from .evidence import EvidenceStore, WhoisEvidenceStore
from .rdap import RegistryInaccessible, check_domain
from .whois import whois_check


logger = logging.getLogger(__name__)

DEFAULT_CANDIDATES_PATH = DATA_DIR / "candidates.csv"
DEFAULT_RDAP_PATH = EVIDENCE_PATH
DEFAULT_WHOIS_PATH = WHOIS_EVIDENCE_PATH
DEFAULT_SCORES_PATH = OUTPUT_DIR / "scores.csv"
DEFAULT_SHORTLIST_PATH = OUTPUT_DIR / "shortlist.csv"
DEFAULT_EXCLUDED_PATH = OUTPUT_DIR / "excluded.csv"
DEFAULT_SAMPLE_PATH = OUTPUT_DIR / "sample_404_for_review.csv"
DEFAULT_OWNED_PATH = DATA_DIR / "owned_domains.txt"


@dataclass(frozen=True)
class RefreshResult:
    total_candidates: int
    checked_rdap: int
    rdap_404_count: int
    rdap_200_count: int
    whois_checked: int
    whois_available_count: int
    whois_registered_count: int
    shortlist_count: int
    rescore_count: int
    stopped_reason: str = ""


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def load_candidate_pool(candidates_path: Path | str = DEFAULT_CANDIDATES_PATH) -> list[tuple[str, str]]:
    p = Path(candidates_path)
    if not p.is_file():
        raise FileNotFoundError(f"Candidate file not found: {p}")
    candidates: list[tuple[str, str]] = []
    seen: set[str] = set()
    with p.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            label = (row.get("domain_label") or "").strip().lower()
            cat = (row.get("category") or "").strip()
            if not label or label in seen:
                continue
            seen.add(label)
            candidates.append((label, cat))
    return candidates


def run_refresh(
    *,
    candidates_path: Path | str = DEFAULT_CANDIDATES_PATH,
    rdap_path: Path | str = DEFAULT_RDAP_PATH,
    whois_path: Path | str = DEFAULT_WHOIS_PATH,
    scores_path: Path | str = DEFAULT_SCORES_PATH,
    shortlist_path: Path | str = DEFAULT_SHORTLIST_PATH,
    excluded_path: Path | str = DEFAULT_EXCLUDED_PATH,
    sample_path: Path | str = DEFAULT_SAMPLE_PATH,
    limit: int | None = None,
    min_interval: float = 1.1,
    whois_check_fn: Callable[..., whois.WhoisResult] | None = None,
    rdap_check_fn: Callable[..., rdap.Result] | None = None,
    stop_on_refusal: bool = True,
) -> RefreshResult:
    """Continuously refresh availability against the registry.
    
    1. Re-checks availability via RDAP first.
    2. Rate limit: at least 1.1s between registry requests, backing off on errors, stopping on refusal.
    3. Confirms RDAP-404s with WHOIS.
    4. Removes names that became registered, updates 'last checked', rescores, and rebuilds shortlist.
    """
    candidates = load_candidate_pool(candidates_path)
    if limit is not None and limit > 0:
        candidates = candidates[:limit]

    rdap_store = EvidenceStore(rdap_path)
    whois_store = WhoisEvidenceStore(whois_path)

    rate_limiter = rdap.RateLimiter(min_interval=max(1.1, min_interval))
    rdap_limiter_state = rate_limiter

    checked_rdap = 0
    rdap_404 = 0
    rdap_200 = 0
    whois_checked = 0
    whois_avail = 0
    whois_reg = 0
    stopped_reason = ""

    # RDAP Pass
    with requests.Session() as session:
        for label, category in candidates:
            domain = f"{label}.si"
            try:
                if rdap_check_fn:
                    result = rdap_check_fn(label, category)
                else:
                    result = check_domain(label, session=session, rate_limiter=rate_limiter)
            except RegistryInaccessible as exc:
                stopped_reason = f"Registry inaccessible / refused on {domain}"
                if stop_on_refusal:
                    break
                continue
            except Exception as exc:
                stopped_reason = f"Error querying {domain}: {exc}"
                if stop_on_refusal:
                    break
                continue

            rdap_store.append(category, result)
            checked_rdap += 1
            if result.classification == "potentially_unregistered":
                rdap_404 += 1
            elif result.classification == "registered":
                rdap_200 += 1
            elif result.classification == "unverified":
                if stop_on_refusal:
                    stopped_reason = f"Unverified/refusal received for {domain}"
                    break

    # WHOIS Pass on 404s
    whois_candidates: list[tuple[str, str]] = []
    rdap_latest = rdap_store.load_latest()
    for label, category in candidates:
        domain = f"{label}.si"
        ev = rdap_latest.get(domain)
        if ev and ev.get("classification") == "potentially_unregistered":
            whois_candidates.append((label, category))

    whois_limiter = rdap.RateLimiter(min_interval=max(1.1, min_interval))

    for label, category in whois_candidates:
        domain = f"{label}.si"
        # Wait rate limit
        whois_limiter.wait()
        try:
            if whois_check_fn:
                w_res = whois_check_fn(label, category)
            else:
                w_res = whois_check(label, connect=whois.socket.create_connection)
        except Exception as exc:
            stopped_reason = f"WHOIS check error on {domain}: {exc}"
            if stop_on_refusal:
                break
            continue

        whois_store.append(category, w_res)
        whois_checked += 1
        if w_res.classification == "not_registered":
            whois_avail += 1
        elif w_res.classification == "registered":
            whois_reg += 1
        else:
            if w_res.error == "rate_limited":
                whois_limiter.increase_after_429()
            if stop_on_refusal and w_res.classification == "unverified":
                stopped_reason = f"WHOIS refusal/rate limit on {domain}"
                break

    # Rescore
    rescore_count = scoring.write_scores(
        candidates_path=candidates_path,
        rdap_path=rdap_path,
        output_path=scores_path,
    )

    # Rebuild shortlist and exclusions
    shortlist_count, _excluded_count, _sample_count = shortlist.build_outputs(
        candidates_path=candidates_path,
        rdap_path=rdap_path,
        whois_path=whois_path,
        scores_path=scores_path,
        shortlist_path=shortlist_path,
        excluded_path=excluded_path,
        sample_path=sample_path,
    )

    return RefreshResult(
        total_candidates=len(candidates),
        checked_rdap=checked_rdap,
        rdap_404_count=rdap_404,
        rdap_200_count=rdap_200,
        whois_checked=whois_checked,
        whois_available_count=whois_avail,
        whois_registered_count=whois_reg,
        shortlist_count=shortlist_count,
        rescore_count=rescore_count,
        stopped_reason=stopped_reason,
    )
