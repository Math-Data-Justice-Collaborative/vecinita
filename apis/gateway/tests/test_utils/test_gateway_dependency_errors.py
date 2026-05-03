"""Tests for ``gateway_dependency_errors`` sanitization."""

from __future__ import annotations

from src.utils.gateway_dependency_errors import client_safe_message_for_dependency_failure


def test_dns_translate_host_message_sanitized():
    raw = 'could not translate host name "dpg-d7chlqt7vvec73b700ng-a" to address: Name or service not known\n'
    msg = client_safe_message_for_dependency_failure(RuntimeError(raw))
    assert "dpg-" not in msg.lower()
    assert "could not translate host name" not in msg.lower()
    assert "Database unreachable" in msg


def test_exception_subclass_with_same_message_sanitized():
    """Sanitization uses ``str(exc)`` only; type does not need to be psycopg2."""

    class DnsStyleError(Exception):
        pass

    exc = DnsStyleError(
        'could not translate host name "dpg-abc123" to address: Name or service not known\n'
    )
    msg = client_safe_message_for_dependency_failure(exc)
    assert "dpg-" not in msg.lower()
    assert "Database unreachable" in msg
