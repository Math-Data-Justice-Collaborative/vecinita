"""Unit tests for env-driven gateway rate-limit configuration."""

from __future__ import annotations

import importlib

import pytest

pytestmark = pytest.mark.unit


def test_endpoint_rate_limits_load_from_env(monkeypatch):
    monkeypatch.setenv("RATE_LIMIT_ASK_REQUESTS_PER_HOUR", "321")
    monkeypatch.setenv("RATE_LIMIT_ASK_TOKENS_PER_DAY", "6543")
    monkeypatch.setenv("RATE_LIMIT_SCRAPE_REQUESTS_PER_HOUR", "22")
    monkeypatch.setenv("RATE_LIMIT_SCRAPE_TOKENS_PER_DAY", "333")

    import src.api.middleware as middleware

    importlib.reload(middleware)

    assert middleware.ENDPOINT_RATE_LIMITS["/api/v1/ask"]["requests_per_hour"] == 321
    assert middleware.ENDPOINT_RATE_LIMITS["/api/v1/ask"]["tokens_per_day"] == 6543
    assert middleware.ENDPOINT_RATE_LIMITS["/api/v1/scrape"]["requests_per_hour"] == 22
    assert middleware.ENDPOINT_RATE_LIMITS["/api/v1/scrape"]["tokens_per_day"] == 333


def test_endpoint_rate_limits_invalid_values_fallback_or_clamp(monkeypatch):
    monkeypatch.setenv("RATE_LIMIT_ADMIN_REQUESTS_PER_HOUR", "not-an-int")
    monkeypatch.setenv("RATE_LIMIT_ADMIN_TOKENS_PER_DAY", "-5")

    import src.api.middleware as middleware

    importlib.reload(middleware)

    # invalid integer -> default
    assert middleware.ENDPOINT_RATE_LIMITS["/api/v1/admin"]["requests_per_hour"] == 50
    # below minimum -> clamped to minimum
    assert middleware.ENDPOINT_RATE_LIMITS["/api/v1/admin"]["tokens_per_day"] == 1
