"""US2: exponential backoff and bounded retry counts for gateway policy."""

from __future__ import annotations

import pytest

from vecinita_scraper.workers.pipeline_retry import (
    gateway_retry_policy_from_env,
    is_transient_http_status,
    max_gateway_http_retries,
    sleep_before_retry_seconds,
)


def test_backoff_exponential_sequence() -> None:
    assert sleep_before_retry_seconds(1, base_seconds=1.0, multiplier=2.0, max_seconds=100.0) == 1.0
    assert sleep_before_retry_seconds(2, base_seconds=1.0, multiplier=2.0, max_seconds=100.0) == 2.0
    assert sleep_before_retry_seconds(3, base_seconds=1.0, multiplier=2.0, max_seconds=100.0) == 4.0
    assert sleep_before_retry_seconds(4, base_seconds=1.0, multiplier=2.0, max_seconds=100.0) == 8.0


def test_backoff_respects_cap() -> None:
    assert sleep_before_retry_seconds(10, base_seconds=1.0, multiplier=2.0, max_seconds=5.0) == 5.0


def test_max_retries_clamped(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SCRAPER_GATEWAY_HTTP_MAX_RETRIES", "99")
    assert max_gateway_http_retries() == 12
    monkeypatch.setenv("SCRAPER_GATEWAY_HTTP_MAX_RETRIES", "0")
    assert max_gateway_http_retries() == 1


def test_transient_status_codes() -> None:
    for code in (408, 425, 429, 500, 502, 503, 504):
        assert is_transient_http_status(code) is True
    assert is_transient_http_status(400) is False
    assert is_transient_http_status(404) is False


def test_gateway_retry_policy_from_env_defaults() -> None:
    policy = gateway_retry_policy_from_env()
    assert policy["base_seconds"] >= 0.05
    assert policy["multiplier"] >= 1.0
    assert policy["max_seconds"] >= 0.05
