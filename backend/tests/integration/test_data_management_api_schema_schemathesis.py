"""Live Schemathesis for the Data Management (scraper) API — same surface as Render lx27.

OpenAPI: https://vecinita-data-management-api-v1-lx27.onrender.com/openapi.json

Requires ``SCRAPER_API_KEYS`` or ``SCRAPER_SCHEMATHESIS_BEARER`` (see ``run_schemathesis_live.sh``).
Collection skips this file when unset so CI without secrets stays green.

TraceCov: run alone (``make test-schemathesis-data-management``) with ``--tracecov-fail-under=100``
for strict schema coverage gates.
"""

from __future__ import annotations

import os

import pytest
from hypothesis import HealthCheck, settings
from schemathesis.generation import GenerationMode

from tests.integration._dm_schemathesis_auth import scraper_bearer_token

schemathesis = pytest.importorskip("schemathesis")

DEFAULT_SCHEMA_URL = "https://vecinita-data-management-api-v1-lx27.onrender.com/openapi.json"


@pytest.fixture(scope="session")
def data_management_live_schema() -> object:
    url = os.environ.get("DATA_MANAGEMENT_SCHEMA_URL", DEFAULT_SCHEMA_URL).strip()
    token = scraper_bearer_token()
    if not token:
        pytest.skip(
            "SCRAPER_API_KEYS or SCRAPER_SCHEMATHESIS_BEARER required for live data-management tests"
        )
    schema = schemathesis.openapi.from_url(
        url,
        headers={"Authorization": f"Bearer {token}"},
        timeout=60.0,
        wait_for_schema=90.0,
    )
    schema.config.generation.modes = [GenerationMode.POSITIVE]
    return schema


schema = schemathesis.pytest.from_fixture("data_management_live_schema")


@pytest.mark.integration
@pytest.mark.schema
@schema.parametrize()
@settings(
    max_examples=25,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture, HealthCheck.filter_too_much],
)
def test_data_management_openapi_stable(case) -> None:
    """Exercise all operations with positive generation; hooks pin valid bodies and path UUIDs."""
    case.call_and_validate(
        checks=[schemathesis.checks.not_a_server_error],
        timeout=120.0,
    )
