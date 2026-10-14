"""Bounded query helpers for the public USPTO trademark JSON search."""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from typing import Mapping

import requests


USPTO_API_URL = "https://tmsearch.uspto.gov/prod-stage-v1-0-0/tmsearch"
USPTO_RESULTS_URL = "https://tmsearch.uspto.gov/search/search-results"
USPTO_HEADERS = {
    "Content-Type": "application/json",
    "Accept": "application/json",
    "User-Agent": "si-domain-research/1.0 (public trademark research)",
}
RESULT_LIMIT = 10


@dataclass(frozen=True)
class MarkHit:
    """Only the non-personal result fields needed for a limited screen."""

    serial_number: str
    wordmark: str
    alive: bool | None
    status: str
    classes: tuple[str, ...]


@dataclass(frozen=True)
class SearchResult:
    query: str
    mode: str
    total: int
    hits: tuple[MarkHit, ...]


def build_search_payload(label: str, *, near: bool = False) -> dict[str, object]:
    """Build an exact phrase or one bounded near-match query."""

    query = label.strip()
    if not query:
        raise ValueError("USPTO query label must not be blank")
    if near:
        wordmark_query: dict[str, object] = {"query": query, "operator": "and"}
        if len(query) >= 5:
            wordmark_query["fuzziness"] = 1
        clause: dict[str, object] = {"match": {"wordmark": wordmark_query}}
    else:
        clause = {"match_phrase": {"wordmark": query}}
    return {"query": {"bool": {"must": [clause]}}, "size": RESULT_LIMIT}


def parse_search_response(payload: object, *, query: str, mode: str) -> SearchResult:
    """Distill observed USPTO JSON fields, without retaining the source payload."""

    if not isinstance(payload, Mapping):
        raise ValueError("USPTO response is not a JSON object")
    hit_block = payload.get("hits")
    if not isinstance(hit_block, Mapping) or not isinstance(hit_block.get("hits"), list):
        raise ValueError("USPTO JSON is missing hits.hits")
    try:
        total = int(hit_block.get("totalValue"))
    except (TypeError, ValueError) as exc:
        raise ValueError("USPTO JSON is missing hits.totalValue") from exc
    parsed: list[MarkHit] = []
    for hit in hit_block["hits"]:
        if not isinstance(hit, Mapping) or not isinstance(hit.get("source"), Mapping):
            raise ValueError("USPTO result is missing its source object")
        source = hit["source"]
        classes = _classes(source.get("internationalClass"))
        alive_value = source.get("alive")
        parsed.append(
            MarkHit(
                serial_number=_ascii_evidence_text(source.get("id") or "").strip(),
                wordmark=_ascii_evidence_text(source.get("wordmark") or "").strip(),
                alive=alive_value if isinstance(alive_value, bool) else None,
                status=_ascii_evidence_text(source.get("statusDescription") or "").strip(),
                classes=classes,
            )
        )
    return SearchResult(
        query=_ascii_evidence_text(query),
        mode=_ascii_evidence_text(mode),
        total=total,
        hits=tuple(parsed),
    )


def _ascii_evidence_text(value: object) -> str:
    """Keep evidence facts ASCII while preserving readable accents and other code points."""

    normalized = unicodedata.normalize("NFKD", str(value))
    without_diacritics = "".join(character for character in normalized if not unicodedata.combining(character))
    return without_diacritics.encode("ascii", errors="backslashreplace").decode("ascii")


def _classes(value: object) -> tuple[str, ...]:
    values = value if isinstance(value, list) else [value]
    normalized: list[str] = []
    for item in values:
        match = re.search(r"\d+", str(item or ""))
        if match:
            number = str(int(match.group()))
            if number not in normalized:
                normalized.append(number)
    return tuple(normalized)


def search_uspto_json(
    session: requests.Session | object,
    label: str,
    *,
    near: bool = False,
) -> SearchResult:
    """Issue one JSON request. The caller paces requests and handles retry policy."""

    response = session.post(  # type: ignore[attr-defined]
        USPTO_API_URL,
        headers=USPTO_HEADERS,
        json=build_search_payload(label, near=near),
        timeout=30,
    )
    if response.status_code != 200:
        raise RuntimeError(f"USPTO returned HTTP {response.status_code}")
    if "json" not in response.headers.get("content-type", "").casefold():
        raise RuntimeError("USPTO returned a non-JSON response")
    mode = "near-fuzzy-1" if near and len(label) >= 5 else "whole-word" if near else "exact"
    return parse_search_response(response.json(), query=label, mode=mode)


def probe_uspto_controls(session: requests.Session | object) -> dict[str, SearchResult]:
    """Check a known mark and nonsense control before per-name requests."""

    google = search_uspto_json(session, "google")
    nonsense = search_uspto_json(session, "qzxwvk")
    if google.total <= 0:
        raise RuntimeError("USPTO known-mark control returned no results")
    if nonsense.total != 0:
        raise RuntimeError("USPTO nonsense control returned unexpected results")
    return {"google": google, "qzxwvk": nonsense}


def search_uspto_label(
    session: requests.Session | object,
    label: str,
) -> tuple[SearchResult, SearchResult]:
    """Run the exact and one fuzzy/whole-word query for a candidate label."""

    return search_uspto_json(session, label), search_uspto_json(session, label, near=True)


def is_similar_wordmark(label: str, wordmark: str) -> bool:
    """Apply the conservative exact, whole-word, light-stem, and edit rule."""

    target = _normalized(label)
    words = re.findall(r"[a-z0-9]+", wordmark.casefold())
    normalized_mark = "".join(words)
    if not target or not words:
        return False
    if target == normalized_mark or target in words or any(
        "".join(words[start:end]) == target
        for start in range(len(words))
        for end in range(start + 1, len(words) + 1)
    ):
        return True
    target_stem = _light_stem(target)
    if target_stem and any(_light_stem(word) == target_stem for word in words):
        return True
    if len(target) >= 5:
        if _edit_distance_at_most_one(target, normalized_mark):
            return True
        if any(len(word) >= len(target) - 1 and _edit_distance_at_most_one(target, word) for word in words):
            return True
    return False


def _normalized(value: str) -> str:
    return "".join(re.findall(r"[a-z0-9]+", value.casefold()))


def _light_stem(value: str) -> str:
    """Remove common English inflection endings for a deliberately small stem check."""

    for suffix in ("ies", "ing", "ed", "es", "s"):
        if len(value) > len(suffix) + 3 and value.endswith(suffix):
            return value[: -len(suffix)] + ("y" if suffix == "ies" else "")
    return value


def _edit_distance_at_most_one(left: str, right: str) -> bool:
    if abs(len(left) - len(right)) > 1:
        return False
    if left == right:
        return True
    if len(left) > len(right):
        left, right = right, left
    i = j = differences = 0
    while i < len(left) and j < len(right):
        if left[i] == right[j]:
            i += 1
            j += 1
            continue
        differences += 1
        if differences > 1:
            return False
        if len(left) == len(right):
            i += 1
        j += 1
    differences += int(j < len(right) or i < len(left))
    return differences <= 1
