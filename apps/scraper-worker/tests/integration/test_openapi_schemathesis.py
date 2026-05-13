"""Offline Schemathesis OpenAPI checks for the data-management (scraper) HTTP API."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest
import schemathesis
from hypothesis import HealthCheck, settings
from schemathesis.generation import GenerationMode

from vecinita_scraper.api.server import create_app
from vecinita_scraper.core.models import (
    OPENAPI_EXAMPLE_JOB_ID,
    JobStatus,
    JobStatusResponse,
    ScrapeJobCancelResponse,
    ScrapeJobCreatedResponse,
    ScrapeJobListQueryParams,
    ScrapeJobListResponse,
    ScrapeJobRequest,
)

schemathesis = pytest.importorskip("schemathesis")


async def _fake_submit(
    request: ScrapeJobRequest,
    *,
    jobs_queue: object,
) -> ScrapeJobCreatedResponse:
    return ScrapeJobCreatedResponse(
        job_id=OPENAPI_EXAMPLE_JOB_ID,
        status=JobStatus.PENDING,
        created_at=datetime.now(UTC).replace(microsecond=0).isoformat(),
        url=str(request.url),
    )


async def _fake_get(job_id: str) -> JobStatusResponse:
    now = datetime.now(UTC)
    return JobStatusResponse(
        job_id=job_id,
        status=JobStatus.COMPLETED,
        progress_pct=100,
        current_step="done",
        updated_at=now,
        created_at=now,
    )


async def _fake_list(params: ScrapeJobListQueryParams) -> ScrapeJobListResponse:
    return ScrapeJobListResponse(user_id=params.user_id, limit=params.limit, jobs=[], total=0)


async def _fake_cancel(job_id: str) -> ScrapeJobCancelResponse:
    return ScrapeJobCancelResponse(
        job_id=job_id,
        previous_status="crawling",
        new_status="cancelled",
    )


@pytest.fixture
def scraper_app_schema(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("SCRAPER_DEBUG_BYPASS_AUTH", "true")
    monkeypatch.setenv("ENVIRONMENT", "test")

    import vecinita_scraper.api.routes as api_routes

    monkeypatch.setattr(api_routes, "submit_scrape_job", _fake_submit)
    monkeypatch.setattr(api_routes, "get_scrape_job_status", _fake_get)
    monkeypatch.setattr(api_routes, "list_scrape_jobs", _fake_list)
    monkeypatch.setattr(api_routes, "cancel_scrape_job", _fake_cancel)

    app = create_app()
    schema = schemathesis.openapi.from_asgi("/openapi.json", app)
    schema.config.generation.modes = [GenerationMode.POSITIVE]
    return schema


schema = schemathesis.pytest.from_fixture("scraper_app_schema")


@pytest.mark.integration
@schema.parametrize()
@settings(
    max_examples=15,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture, HealthCheck.filter_too_much],
)
def test_scraper_openapi_not_server_error(case):
    case.call_and_validate(checks=[schemathesis.checks.not_a_server_error])
