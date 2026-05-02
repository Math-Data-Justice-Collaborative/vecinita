"""Live Schemathesis for the Data Management (scraper) API — same surface as Render lx27.

OpenAPI: https://vecinita-data-management-api-v1-lx27.onrender.com/openapi.json

Requires ``SCRAPER_API_KEYS`` or ``SCRAPER_SCHEMATHESIS_BEARER`` (see ``run_schemathesis_live.sh``).
Collection skips this file when unset so CI without secrets stays green.

TraceCov: run alone (``make test-schemathesis-data-management``) with ``--tracecov-fail-under=100``
for strict schema coverage gates.

**Feature 007** (``specs/007-scraper-via-dm-api``): scrape/job HTTP surfaces on the DM API remain
covered by this parametrized suite plus ``tests/schemathesis_hooks.py`` DM hooks
(``_data_management_job_id``, bearer auth). No duplicate DM-only harness under
``apis/data-management-api/tests/`` unless a route is unreachable from the
backend pytest entrypoint (document splits in ``modal-migration-inventory.md``).
"""

from __future__ import annotations

import os
from typing import Any

import httpx
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


@pytest.mark.integration
def test_data_management_openapi_defines_scraper_job_paths() -> None:
    """Contract guard (no Bearer): public OpenAPI lists ``/health`` and ``/jobs`` (007 / SC-001).

    Skips when the schema URL is unreachable or auth-gated so CI without network stays green.
    """
    url = os.environ.get("DATA_MANAGEMENT_SCHEMA_URL", DEFAULT_SCHEMA_URL).strip()
    try:
        resp = httpx.get(url, timeout=45.0)
    except httpx.RequestError as exc:  # pragma: no cover - network flake
        pytest.skip(f"DM OpenAPI unreachable: {exc}")

    if resp.status_code in (401, 403):
        pytest.skip("DM OpenAPI schema URL requires authentication for this environment")

    resp.raise_for_status()
    doc: dict[str, Any] = resp.json()
    paths = doc.get("paths") or {}
    keys_preview = " ".join(list(paths.keys())[:40])
    assert "/health" in paths, f"expected /health in DM OpenAPI paths; saw: {keys_preview}"
    assert any(
        "/jobs" in p for p in paths
    ), f"expected /jobs in DM OpenAPI paths; saw: {keys_preview}"
