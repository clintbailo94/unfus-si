import socket
from datetime import datetime, timezone
from pathlib import Path

from si_domains.whois import classify_whois_text, whois_check


FIXTURES = Path(__file__).parent / "fixtures"


class FakeSocket:
    def __init__(self, payload):
        self.payload = payload
        self.sent = b""
        self.timeout = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def settimeout(self, timeout):
        self.timeout = timeout

    def sendall(self, data):
        self.sent += data

    def recv(self, size):
        if not self.payload:
            return b""
        part = self.payload[:size]
        self.payload = self.payload[size:]
        return part


def fixed_clock():
    return datetime(2026, 10, 12, 13, 14, 15, tzinfo=timezone.utc)


def test_classifies_redacted_fixture_patterns():
    registered = (FIXTURES / "whois_registered.txt").read_text(encoding="utf-8")
    unregistered = (FIXTURES / "whois_unregistered.txt").read_text(encoding="utf-8")
    assert classify_whois_text(registered) == ("registered", "field:registrar")
    assert classify_whois_text(unregistered) == ("not_registered", "no_entries_found")


def test_whois_sends_rfc3912_query_and_returns_metadata_only():
    connection = FakeSocket(b"Registrar: [redacted]\r\nCreated: [redacted]\r\n")
    result = whois_check("google", connect=lambda address, timeout: connection, clock=fixed_clock)
    assert connection.sent == b"google.si\r\n"
    assert result.classification == "registered"
    assert result.matched_pattern == "field:registrar"
    assert not hasattr(result, "response")


def test_socket_failure_is_unverified_without_exposing_error_details():
    def fail(address, timeout):
        raise socket.timeout("private message should not escape")

    result = whois_check("google", connect=fail, clock=fixed_clock)
    assert result.classification == "unverified"
    assert result.error == "timeout"
    assert "private message" not in result.error


def test_connection_refusal_is_unverified():
    def fail(address, timeout):
        raise ConnectionRefusedError("connection refused")

    result = whois_check("google", connect=fail, clock=fixed_clock)
    assert result.classification == "unverified"
    assert result.error == "connection_error"


def test_whois_invalid_label_does_not_open_socket():
    called = []
    result = whois_check("bad.name", connect=lambda *args, **kwargs: called.append(True), clock=fixed_clock)
    assert result.classification == "unverified"
    assert result.error == "invalid_label"
    assert called == []
