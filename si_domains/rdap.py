"""Conservative RDAP lookup with retries, shared pacing, and no body storage."""

from __future__ import annotations

import random
import threading
import time
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from typing import Callable, Iterator

import requests

from . import rules
from .config import (
    BACKOFF_BASE_SECONDS,
    BACKOFF_CAP_SECONDS,
    CIRCUIT_BREAKER_THRESHOLD,
    MAX_RETRIES,
    MAX_RETRY_AFTER_SECONDS,
    MIN_REQUEST_INTERVAL,
    RDAP_BASE_URL,
    RDAP_TIMEOUT,
    USER_AGENT,
)
from .validation import ascii_label, is_valid_label


Clock = Callable[[], datetime | float]
Sleep = Callable[[float], None]
Jitter = Callable[[], float]


def _now_utc(clock: Clock) -> datetime:
    value = clock()
    if isinstance(value, datetime):
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc)
    return datetime.fromtimestamp(float(value), tz=timezone.utc)


def _timestamp(clock: Clock) -> str:
    return _now_utc(clock).isoformat(timespec="seconds").replace("+00:00", "Z")


@dataclass(frozen=True)
class Result:
    domain: str
    http_status: int | None
    utc_timestamp: str
    attempts: int
    classification: str
    error: str = ""


class RegistryInaccessible(RuntimeError):
    """Raised after consecutive registry failures; ``result`` preserves the last row."""

    def __init__(self, message: str, result: Result | None = None):
        super().__init__(message)
        self.result = result


class RateLimiter:
    """Serialize request starts so a process never starts requests too quickly."""

    def __init__(
        self,
        min_interval: float = MIN_REQUEST_INTERVAL,
        *,
        clock: Callable[[], float] = time.monotonic,
        sleep: Sleep = time.sleep,
    ) -> None:
        self.min_interval = min_interval
        self._clock = clock
        self._sleep = sleep
        self._last_request: float | None = None
        self._lock = threading.Lock()

    def wait(
        self,
        *,
        clock: Callable[[], float] | None = None,
        sleep: Sleep | None = None,
    ) -> None:
        with self.request(clock=clock, sleep=sleep):
            pass

    @contextmanager
    def request(
        self,
        *,
        clock: Callable[[], float] | None = None,
        sleep: Sleep | None = None,
    ) -> Iterator[None]:
        with self._lock:
            active_clock = clock or self._clock
            active_sleep = sleep or self._sleep
            now = active_clock()
            while self._last_request is not None:
                remaining = self.min_interval - (now - self._last_request)
                if remaining <= 0:
                    break
                active_sleep(remaining)
                now = active_clock()
            self._last_request = now
            yield


class CircuitBreaker:
    """Latch closed after too many consecutive domain-level registry outages."""

    def __init__(self, threshold: int = CIRCUIT_BREAKER_THRESHOLD) -> None:
        self.threshold = threshold
        self.consecutive_outages = 0
        self.is_open = False

    def ensure_available(self) -> None:
        if self.is_open:
            raise RegistryInaccessible("RDAP circuit breaker is open")

    def record(self, result: Result) -> None:
        if result.classification == "unverified" and _is_registry_outage(result):
            self.consecutive_outages += 1
        else:
            self.consecutive_outages = 0

        if self.consecutive_outages >= self.threshold:
            self.is_open = True
            raise RegistryInaccessible(
                f"RDAP circuit breaker opened after {self.consecutive_outages} consecutive outages",
                result=result,
            )


RATE_LIMITER = RateLimiter()
CIRCUIT_BREAKER = CircuitBreaker()


def _is_registry_outage(result: Result) -> bool:
    return (
        result.http_status in (403, 429)
        or (result.http_status is not None and 500 <= result.http_status <= 599)
        or result.error.startswith("network_")
    )


def _is_json_content_type(response: requests.Response) -> bool:
    content_type = ""
    for key, value in getattr(response, "headers", {}).items():
        if key.lower() == "content-type":
            content_type = str(value)
            break
    media_type = content_type.split(";", 1)[0].strip().lower()
    return media_type in {"application/rdap+json", "application/json"}


def _response_classification(response: requests.Response, status: int) -> tuple[str, str]:
    if status not in (200, 404):
        if status == 403:
            return "unverified", "http_403"
        if status == 429:
            return "unverified", "http_429"
        if 500 <= status <= 599:
            return "unverified", f"http_{status}"
        if 300 <= status <= 399:
            return "unverified", "redirect_not_followed"
        return "unverified", f"http_{status}"

    if not _is_json_content_type(response):
        return "unverified", "unexpected_content_type"
    try:
        payload = response.json()
    except (ValueError, requests.JSONDecodeError):
        return "unverified", "invalid_json"
    if not isinstance(payload, dict):
        return "unverified", "unexpected_json_shape"

    if status == 200:
        if str(payload.get("objectClassName", "")).casefold() == "domain":
            return "registered", ""
        return "unverified", "unexpected_rdap_object"

    if payload.get("errorCode") == 404:
        return "potentially_unregistered", ""
    return "unverified", "ambiguous_404_response"


def _header(response: requests.Response, name: str) -> str | None:
    for key, value in getattr(response, "headers", {}).items():
        if key.lower() == name.lower():
            return str(value).strip()
    return None


def _retry_after_seconds(value: str | None, clock: Clock) -> float | None:
    if not value:
        return None
    try:
        seconds = float(value)
        return max(0.0, seconds)
    except ValueError:
        pass
    try:
        retry_at = parsedate_to_datetime(value)
    except (TypeError, ValueError, OverflowError):
        return None
    if retry_at.tzinfo is None:
        retry_at = retry_at.replace(tzinfo=timezone.utc)
    return max(0.0, (retry_at.astimezone(timezone.utc) - _now_utc(clock)).total_seconds())


def _backoff_seconds(retry_number: int, jitter: Jitter) -> float:
    base = min(BACKOFF_BASE_SECONDS * (2 ** retry_number), BACKOFF_CAP_SECONDS)
    try:
        extra = max(0.0, float(jitter()))
    except (TypeError, ValueError):
        extra = 0.0
    return min(base + extra, BACKOFF_CAP_SECONDS)


def check_domain(
    label: str,
    *,
    session: requests.Session,
    clock: Clock = lambda: datetime.now(timezone.utc),
    sleep: Sleep = time.sleep,
    jitter: Jitter | None = None,
) -> Result:
    """Check one label, returning only status metadata and a short error code."""

    domain = f"{label}.si" if isinstance(label, str) else f"{label}.si"
    if not is_valid_label(label):
        return Result(domain, None, _timestamp(clock), 0, "invalid_syntax", "invalid_label")

    rule_classification = rules.classify(label)
    if rule_classification != "ok":
        return Result(domain, None, _timestamp(clock), 0, str(rule_classification), "")

    CIRCUIT_BREAKER.ensure_available()
    jitter_fn = jitter or JITTER
    final_status: int | None = None
    final_error = ""
    final_timestamp = _timestamp(clock)
    attempts = 0

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            with RATE_LIMITER.request():
                final_timestamp = _timestamp(clock)
                attempts = attempt
                response = session.get(
                    f"{RDAP_BASE_URL}{ascii_label(label)}.si",
                    headers={"User-Agent": USER_AGENT},
                    timeout=RDAP_TIMEOUT,
                    allow_redirects=False,
                )
        except requests.Timeout:
            final_status = None
            final_error = "network_timeout"
            retry_after = None
            retryable = True
        except requests.ConnectionError:
            final_status = None
            final_error = "network_connection_error"
            retry_after = None
            retryable = True
        except requests.RequestException:
            final_status = None
            final_error = "network_request_error"
            retry_after = None
            retryable = True
        else:
            final_status = int(response.status_code)
            classification, final_error = _response_classification(response, final_status)
            retryable = final_status == 429 or 500 <= final_status <= 599
            retry_after = _retry_after_seconds(_header(response, "Retry-After"), clock) if retryable else None
            if not retryable:
                result = Result(domain, final_status, final_timestamp, attempts, classification, final_error)
                CIRCUIT_BREAKER.record(result)
                return result

        if retry_after is not None and retry_after > MAX_RETRY_AFTER_SECONDS:
            final_error = "retry_after_exceeds_limit"
            break
        if attempt >= MAX_RETRIES:
            break

        delay = _backoff_seconds(attempt - 1, jitter_fn)
        if retry_after is not None:
            delay = max(delay, retry_after)
        sleep(delay)

    result = Result(domain, final_status, final_timestamp, attempts, "unverified", final_error)
    CIRCUIT_BREAKER.record(result)
    return result


def _default_jitter() -> float:
    return random.uniform(0.0, 1.0)


JITTER: Jitter = _default_jitter
