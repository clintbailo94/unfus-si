from datetime import datetime, timedelta, timezone
from email.utils import format_datetime

import pytest
import requests

import si_domains.rdap as rdap


class FakeClock:
    def __init__(self, start=None):
        self.now = start or datetime(2026, 10, 12, 12, 0, 0, tzinfo=timezone.utc)
        self.monotonic_now = 0.0
        self.sleeps = []

    def utc(self):
        return self.now

    def monotonic(self):
        return self.monotonic_now

    def sleep(self, seconds):
        self.sleeps.append(seconds)
        self.now += timedelta(seconds=seconds)
        self.monotonic_now += seconds


class Response:
    def __init__(self, status, payload=None, *, content_type="application/rdap+json", headers=None, text=""):
        self.status_code = status
        self._payload = payload
        self.headers = {"Content-Type": content_type, **(headers or {})}
        self.text = text

    def json(self):
        if isinstance(self._payload, Exception):
            raise self._payload
        return self._payload


class FakeSession:
    def __init__(self, outcomes, *, monotonic=None):
        self.outcomes = list(outcomes)
        self.calls = []
        self.monotonic = monotonic
        self.starts = []

    def get(self, url, **kwargs):
        self.calls.append((url, kwargs))
        if self.monotonic is not None:
            self.starts.append(self.monotonic())
        outcome = self.outcomes.pop(0)
        if isinstance(outcome, BaseException):
            raise outcome
        return outcome


@pytest.fixture
def fake_clock(monkeypatch):
    clock = FakeClock()
    monkeypatch.setattr(rdap, "RATE_LIMITER", rdap.RateLimiter(clock=clock.monotonic, sleep=clock.sleep))
    monkeypatch.setattr(rdap, "CIRCUIT_BREAKER", rdap.CircuitBreaker())
    monkeypatch.setattr(rdap, "JITTER", lambda: 0.0)
    return clock


def check(session, clock, **kwargs):
    return rdap.check_domain(
        "example",
        session=session,
        clock=clock.utc,
        sleep=clock.sleep,
        **kwargs,
    )


def test_200_registered_requires_rdap_domain_json(fake_clock):
    session = FakeSession([Response(200, {"objectClassName": "domain"})])
    result = check(session, fake_clock)
    assert result.domain == "example.si"
    assert result.http_status == 200
    assert result.classification == "registered"
    assert result.attempts == 1
    assert result.error == ""
    assert session.calls[0][1]["allow_redirects"] is False
    assert "si-domain-research/1.0" in session.calls[0][1]["headers"]["User-Agent"]


def test_404_requires_json_error_code_404(fake_clock):
    session = FakeSession([Response(404, {"errorCode": 404})])
    result = check(session, fake_clock)
    assert result.classification == "potentially_unregistered"
    assert result.http_status == 404


def test_json_content_type_is_accepted_for_404(fake_clock):
    result = check(FakeSession([Response(404, {"errorCode": 404}, content_type="application/json; charset=utf-8")]), fake_clock)
    assert result.classification == "potentially_unregistered"


@pytest.mark.parametrize(
    "response,expected_error",
    [
        (Response(403, {"errorCode": 403}), "http_403"),
        (Response(404, {"errorCode": 404}, content_type="text/html"), "unexpected_content_type"),
        (Response(404, {"errorCode": 400}), "ambiguous_404_response"),
        (Response(200, {"objectClassName": "entity"}), "unexpected_rdap_object"),
        (Response(302, {}, headers={"Location": "https://elsewhere.invalid"}), "redirect_not_followed"),
    ],
)
def test_ambiguous_and_forbidden_responses_are_unverified_without_retry(fake_clock, response, expected_error):
    session = FakeSession([response])
    result = check(session, fake_clock)
    assert result.classification == "unverified"
    assert result.error == expected_error
    assert len(session.calls) == 1


def test_429_retry_after_seconds_uses_max_of_backoff_and_header(fake_clock):
    session = FakeSession(
        [
            Response(429, {}, headers={"Retry-After": "7"}),
            Response(200, {"objectClassName": "domain"}),
        ]
    )
    result = check(session, fake_clock)
    assert result.classification == "registered"
    assert result.attempts == 2
    assert fake_clock.now == datetime(2026, 10, 12, 12, 0, 7, tzinfo=timezone.utc)
    assert result.utc_timestamp == "2026-10-12T12:00:07Z"


def test_retry_after_http_date_is_honored(fake_clock):
    target = fake_clock.now + timedelta(seconds=5)
    session = FakeSession(
        [
            Response(429, {}, headers={"Retry-After": format_datetime(target, usegmt=True)}),
            Response(404, {"errorCode": 404}),
        ]
    )
    result = check(session, fake_clock)
    assert result.classification == "potentially_unregistered"
    assert fake_clock.now == target


def test_retry_after_over_15_minutes_stops_without_sleep(fake_clock):
    session = FakeSession([Response(429, {}, headers={"Retry-After": "901"})])
    result = check(session, fake_clock)
    assert result.classification == "unverified"
    assert result.attempts == 1
    assert result.error == "retry_after_exceeds_limit"
    assert fake_clock.now == datetime(2026, 10, 12, 12, 0, 0, tzinfo=timezone.utc)


def test_5xx_uses_exponential_backoff_and_attempt_cap(fake_clock):
    session = FakeSession([Response(500, {}) for _ in range(5)])
    result = check(session, fake_clock)
    assert result.classification == "unverified"
    assert result.http_status == 500
    assert result.attempts == 5
    assert len(session.calls) == 5
    assert fake_clock.now == datetime(2026, 10, 12, 12, 0, 30, tzinfo=timezone.utc)
    assert fake_clock.sleeps == [2.0, 4.0, 8.0, 16.0]


@pytest.mark.parametrize(
    "exception,error",
    [
        (requests.Timeout("timeout"), "network_timeout"),
        (requests.ConnectionError("offline"), "network_connection_error"),
    ],
)
def test_network_failures_retry_to_attempt_cap(fake_clock, exception, error):
    session = FakeSession([exception for _ in range(5)])
    result = check(session, fake_clock)
    assert result.classification == "unverified"
    assert result.error == error
    assert result.attempts == 5


def test_rate_limiter_spaces_any_request_starts_by_one_second():
    elapsed = [0.0]
    starts = []

    def clock():
        return elapsed[0]

    def sleep(seconds):
        elapsed[0] += seconds

    limiter = rdap.RateLimiter(min_interval=1.0, clock=clock, sleep=sleep)
    for _ in range(4):
        limiter.wait()
        starts.append(elapsed[0])
    assert starts == [0.0, 1.0, 2.0, 3.0]
    assert all(right - left >= 1.0 for left, right in zip(starts, starts[1:]))


def test_adaptive_pacing_covers_retries_and_later_domains(fake_clock):
    limiter = rdap.RateLimiter(
        min_interval=2.0,
        clock=fake_clock.monotonic,
        sleep=fake_clock.sleep,
    )
    session = FakeSession(
        [
            Response(429, {}, headers={"Retry-After": "0"}),
            Response(429, {}, headers={"Retry-After": "0"}),
            Response(429, {}, headers={"Retry-After": "0"}),
            Response(429, {}, headers={"Retry-After": "0"}),
            Response(200, {"objectClassName": "domain"}),
            Response(404, {"errorCode": 404}),
        ],
        monotonic=fake_clock.monotonic,
    )

    first = rdap.check_domain(
        "example",
        session=session,
        clock=fake_clock.utc,
        sleep=fake_clock.sleep,
        jitter=lambda: 0.0,
        rate_limiter=limiter,
    )
    second = rdap.check_domain(
        "another",
        session=session,
        clock=fake_clock.utc,
        sleep=fake_clock.sleep,
        jitter=lambda: 0.0,
        rate_limiter=limiter,
    )

    assert first.classification == "registered"
    assert first.attempts == 5
    assert second.classification == "potentially_unregistered"
    assert session.starts == [0.0, 3.0, 7.5, 15.5, 31.5, 36.5]
    assert limiter.min_interval == 5.0
    assert limiter.configured_min_interval == 2.0


def test_rate_limiter_never_adapts_below_configured_interval():
    limiter = rdap.RateLimiter(min_interval=6.0, clock=lambda: 0.0, sleep=lambda _: None)

    limiter.increase_after_429()

    assert limiter.min_interval == 6.0


def test_retries_are_also_spaced_by_rate_limiter(fake_clock):
    session = FakeSession([Response(500, {}), Response(200, {"objectClassName": "domain"})])
    result = check(session, fake_clock)
    assert result.classification == "registered"
    assert fake_clock.monotonic_now == 2.0


def test_invalid_syntax_never_hits_network(fake_clock):
    session = FakeSession([])
    result = rdap.check_domain("ab--cd", session=session, clock=fake_clock.utc, sleep=fake_clock.sleep)
    assert result.classification == "invalid_syntax"
    assert result.http_status is None
    assert result.attempts == 0
    assert session.calls == []


def test_registry_rules_prevent_rdap_lookup(fake_clock):
    session = FakeSession([])
    result = rdap.check_domain("112", session=session, clock=fake_clock.utc, sleep=fake_clock.sleep)
    assert result.classification == "reserved"
    assert result.http_status is None
    assert result.attempts == 0
    assert session.calls == []


def test_idn_is_sent_as_ascii_ace_to_rdap(fake_clock):
    session = FakeSession([Response(404, {"errorCode": 404})])
    result = rdap.check_domain("roža", session=session, clock=fake_clock.utc, sleep=fake_clock.sleep)
    assert result.classification == "potentially_unregistered"
    assert result.domain == "roža.si"
    assert session.calls[0][0] == f"{rdap.RDAP_BASE_URL}xn--roa-d3a.si"


def test_consecutive_outages_trip_circuit_breaker(fake_clock, monkeypatch):
    monkeypatch.setattr(rdap, "CIRCUIT_BREAKER", rdap.CircuitBreaker(threshold=2))
    first = check(FakeSession([Response(403, {})]), fake_clock)
    assert first.classification == "unverified"
    with pytest.raises(rdap.RegistryInaccessible) as caught:
        check(FakeSession([Response(429, {}) for _ in range(5)]), fake_clock)
    assert caught.value.result.classification == "unverified"
    with pytest.raises(rdap.RegistryInaccessible):
        check(FakeSession([Response(200, {"objectClassName": "domain"})]), fake_clock)


def test_non_outage_result_resets_circuit_streak(fake_clock, monkeypatch):
    monkeypatch.setattr(rdap, "CIRCUIT_BREAKER", rdap.CircuitBreaker(threshold=2))
    check(FakeSession([Response(403, {})]), fake_clock)
    check(FakeSession([Response(200, {"objectClassName": "domain"})]), fake_clock)
    check(FakeSession([Response(403, {})]), fake_clock)
    assert not rdap.CIRCUIT_BREAKER.is_open


def test_timestamp_uses_seconds_and_z_suffix(fake_clock):
    fake_clock.now = datetime(2026, 10, 12, 12, 34, 56, 987654, tzinfo=timezone.utc)
    result = check(FakeSession([Response(200, {"objectClassName": "domain"})]), fake_clock)
    assert result.utc_timestamp == "2026-10-12T12:34:56Z"


def test_unknown_content_type_and_invalid_json_are_unverified(fake_clock):
    html = Response(200, {"objectClassName": "domain"}, content_type="text/html")
    invalid_json = Response(404, ValueError("secret response data"))
    first = check(FakeSession([html]), fake_clock)
    second = check(FakeSession([invalid_json]), fake_clock)
    assert first.error == "unexpected_content_type"
    assert second.error == "invalid_json"
    assert "secret response data" not in first.error + second.error
