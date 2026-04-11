"""Live Schemathesis for the deployed gateway OpenAPI (e.g. Render lx27).

Requires ``RENDER_GATEWAY_URL``. When the deployment uses ``ENABLE_AUTH=true``,
set ``GATEWAY_LIVE_BEARER`` to a valid API key.

**Tiers**

- ``SCHEMATHESIS_TIER=a`` (default): ``not_a_server_error`` only.
- ``SCHEMATHESIS_TIER=b``: also ``response_schema_conformance`` on a small
  allowlist of read-only routes with stable ``response_model`` coverage.

The main property suite avoids ``GET /api/v1/ask`` (LLM cost / latency); that
route is covered separately with a low example budget.
"""

from __future__ import annotations

import os

import pytest
import schemathesis
from hypothesis import HealthCheck, settings
from schemathesis.generation import GenerationMode
from schemathesis.specs.openapi.checks import response_schema_conformance

pytestmark = pytest.mark.live

_TIER = os.environ.get("SCHEMATHESIS_TIER", "a").lower()

_LIVE_GATEWAY_SCHEMA_CONTRACT_OPS: frozenset[tuple[str, str]] = frozenset(
    {
        ("GET", "/health"),
        ("GET", "/config"),
        ("GET", "/integrations/status"),
        ("GET", "/api/v1/ask/config"),
        ("GET", "/api/v1/documents/overview"),
    }
)

_LIVE_GATEWAY_STABLE_OPS: frozenset[tuple[str, str]] = frozenset(
    {
        ("GET", "/health"),
        ("GET", "/config"),
        ("GET", "/integrations/status"),
        ("GET", "/api/v1/ask/config"),
        ("GET", "/api/v1/documents/overview"),
        ("GET", "/api/v1/documents/chunk-statistics"),
        ("GET", "/api/v1/documents/tags"),
        ("GET", "/api/v1/embed/config"),
        ("POST", "/api/v1/embed"),
        ("POST", "/api/v1/embed/batch"),
        ("POST", "/api/v1/embed/similarity"),
    }
)


@pytest.fixture(scope="session")
def gateway_live_schema(gateway_url: str):
    schema = schemathesis.openapi.from_url(
        f"{gateway_url}/api/v1/docs/openapi.json",
        wait_for_schema=30.0,
    )
    schema.config.generation.modes = [GenerationMode.POSITIVE]
    return schema.exclude(path_regex=r"/ask/stream$").exclude(path="/api/v1/ask")


@pytest.fixture(scope="session")
def gateway_live_schema_ask(gateway_url: str):
    schema = schemathesis.openapi.from_url(
        f"{gateway_url}/api/v1/docs/openapi.json",
        wait_for_schema=30.0,
    )
    schema.config.generation.modes = [GenerationMode.POSITIVE]
    return schema.include(path="/api/v1/ask", method="GET")


gateway_schema = schemathesis.pytest.from_fixture("gateway_live_schema")
gateway_ask_schema = schemathesis.pytest.from_fixture("gateway_live_schema_ask")


def _optional_bearer_kwargs() -> dict:
    token = (os.environ.get("GATEWAY_LIVE_BEARER") or "").strip()
    if not token:
        return {}
    return {"headers": {"Authorization": f"Bearer {token}"}}


@gateway_schema.parametrize()
@settings(
    max_examples=8,
    suppress_health_check=[HealthCheck.too_slow, HealthCheck.filter_too_much],
    deadline=None,
)
def test_gateway_live_stable_operations(case):
    if (case.method, case.path) not in _LIVE_GATEWAY_STABLE_OPS:
        pytest.skip("Outside stable live gateway allowlist")

    checks = [schemathesis.checks.not_a_server_error]
    if _TIER == "b" and (case.method, case.path) in _LIVE_GATEWAY_SCHEMA_CONTRACT_OPS:
        checks.append(response_schema_conformance)

    case.call_and_validate(
        timeout=90,
        checks=checks,
        **_optional_bearer_kwargs(),
    )


@gateway_ask_schema.parametrize()
@settings(
    max_examples=3,
    suppress_health_check=[HealthCheck.too_slow, HealthCheck.filter_too_much],
    deadline=None,
)
def test_gateway_live_ask_not_server_error(case):
    case.call_and_validate(
        timeout=120,
        checks=[schemathesis.checks.not_a_server_error],
        **_optional_bearer_kwargs(),
    )
