"""Schemathesis OpenAPI conformance tests for the Vecinita agent (offline ASGI).

Uses the FastAPI app in-process with the same import-time stubs as the rest of
the test suite (see ``tests/conftest.py``). Heavy endpoints (/ask, streams, DB
diagnostics) stay out of the fuzz allowlist; cover those with targeted tests and
live suites.

Run from repo root::

    make test-schemathesis-agent
"""

from __future__ import annotations

import pytest

from tests.integration._agent_schemathesis_stable_ops import AGENT_STABLE_OPERATIONS

schemathesis = pytest.importorskip("schemathesis")
hypothesis = pytest.importorskip("hypothesis")
HealthCheck = hypothesis.HealthCheck
settings = hypothesis.settings
from schemathesis.generation import GenerationMode  # noqa: E402


@pytest.fixture(scope="session")
def agent_schema():
    """Load OpenAPI from the agent app; restrict to positive schema-valid inputs."""
    from src.agent.main import app

    schema = schemathesis.openapi.from_asgi("/openapi.json", app)
    schema.config.generation.modes = [GenerationMode.POSITIVE]
    return schema


schema = schemathesis.pytest.from_fixture("agent_schema")


@pytest.mark.integration
@pytest.mark.schema
@schema.parametrize()
@settings(
    max_examples=15,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture],
)
def test_agent_openapi_stable_operations(case):
    """No 5xx on a small allowlist of cheap, deterministic agent routes."""
    if (case.method, case.path) not in AGENT_STABLE_OPERATIONS:
        pytest.skip("Operation excluded from stable agent Schemathesis contract run")

    case.call_and_validate(
        checks=[schemathesis.checks.not_a_server_error],
        timeout=30,
    )
