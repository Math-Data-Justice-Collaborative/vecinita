"""Schemathesis stateful scenarios for Modal job gateway routes (offline, mocked invoker)."""

from __future__ import annotations

import pytest
from hypothesis import HealthCheck, settings

from tests.integration.test_api_schema_schemathesis import (
    _reload_gateway_with_mocks,
    clone_gateway_schema_path_prefix,
)

_STATEFUL_SETTINGS = settings(
    max_examples=10,
    stateful_step_count=6,
    deadline=None,
    suppress_health_check=list(HealthCheck),
)


@pytest.mark.integration
@pytest.mark.schema
def test_gateway_modal_jobs_stateful_flow(monkeypatch: pytest.MonkeyPatch) -> None:
    """Covers scraper submit/get/cancel and registry paths with inferred links on typed models."""
    schema = _reload_gateway_with_mocks(monkeypatch, enable_auth=False)
    narrow = clone_gateway_schema_path_prefix(schema, "/api/v1/modal-jobs")
    narrow.config.phases.stateful.enabled = True
    narrow.config.checks.negative_data_rejection.enabled = False

    base = narrow.as_state_machine()

    class _ModalJobsWorkflow(base):
        pass

    _ModalJobsWorkflow.TestCase.settings = _STATEFUL_SETTINGS
    _ModalJobsWorkflow.TestCase().runTest()
