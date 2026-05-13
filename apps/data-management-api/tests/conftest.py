"""Pytest configuration for ``apis/data-management-api/tests`` (invoked from monorepo ``backend/``)."""

from __future__ import annotations

import pytest


def pytest_configure(config: pytest.Config) -> None:
    for line in (
        "unit: fast unit scope",
        "contract: contract and pact consumer tests",
        "integration: integration scope",
        "pact_provider: Pact provider verification",
    ):
        config.addinivalue_line("markers", line)


@pytest.fixture(autouse=True)
def force_http_service_clients_when_mocking(monkeypatch: pytest.MonkeyPatch) -> None:
    """Parity tests mock ``httpx``; shell ``MODAL_FUNCTION_INVOCATION=auto`` would call Modal instead."""
    monkeypatch.setenv("MODAL_FUNCTION_INVOCATION", "http")
