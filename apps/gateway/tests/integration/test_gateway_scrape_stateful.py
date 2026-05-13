"""Schemathesis stateful scenarios for gateway scrape jobs (offline, mocked upstreams)."""

from __future__ import annotations

import pytest
from hypothesis import HealthCheck, settings

from tests.integration.test_api_schema_schemathesis import (
    _reload_gateway_with_mocks,
    clone_gateway_schema_path_prefix,
)

_STATEFUL_SETTINGS = settings(
    max_examples=12,
    stateful_step_count=8,
    deadline=None,
    suppress_health_check=list(HealthCheck),
)


@pytest.mark.integration
@pytest.mark.schema
def test_gateway_scrape_stateful_job_flow(monkeypatch: pytest.MonkeyPatch) -> None:
    """Chains POST/GET/cancel using dependency-analysis links (``job_id`` ↔ path param)."""
    schema = _reload_gateway_with_mocks(monkeypatch, enable_auth=False)
    narrow = clone_gateway_schema_path_prefix(schema, "/api/v1/scrape")
    narrow.config.phases.stateful.enabled = True
    # Stateful mixes negative examples; the gateway accepts some bodies FastAPI treats as valid.
    narrow.config.checks.negative_data_rejection.enabled = False

    base = narrow.as_state_machine()

    class _ScrapeJobWorkflow(base):
        pass

    _ScrapeJobWorkflow.TestCase.settings = _STATEFUL_SETTINGS
    _ScrapeJobWorkflow.TestCase().runTest()
