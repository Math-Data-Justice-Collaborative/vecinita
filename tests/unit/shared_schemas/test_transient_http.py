"""Unit tests for vecinita_shared_schemas.transient_http."""

from __future__ import annotations

from vecinita_shared_schemas.transient_http import should_retry_ask


def test_should_retry_ask_on_network_error() -> None:
    assert should_retry_ask(status_code=None, is_network_error=True) is True


def test_should_retry_ask_on_transient_status_codes() -> None:
    for status in (502, 503, 504):
        assert should_retry_ask(status_code=status, is_network_error=False) is True


def test_should_not_retry_ask_on_success_or_client_error() -> None:
    assert should_retry_ask(status_code=200, is_network_error=False) is False
    assert should_retry_ask(status_code=404, is_network_error=False) is False
    assert should_retry_ask(status_code=None, is_network_error=False) is False
