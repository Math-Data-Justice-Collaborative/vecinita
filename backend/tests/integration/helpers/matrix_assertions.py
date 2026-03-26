"""Shared assertion helpers for gateway matrix tests."""

from __future__ import annotations


def assert_status(response, expected_status: int) -> None:
    """Assert status code with enriched diagnostics for matrix test failures."""
    assert response.status_code == expected_status, (
        f"Expected HTTP {expected_status}, got {response.status_code}. " f"Body: {response.text}"
    )
