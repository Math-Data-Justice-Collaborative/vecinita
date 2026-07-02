"""UJ-044 / TC-124: unified GET /jobs includes eval runs (EV-009, ADR-035 §3)."""

from __future__ import annotations

from datetime import UTC, datetime
from http import HTTPStatus
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from vecinita_data_management_backend.app import create_app
from vecinita_data_management_backend.store import InMemoryJobStore
from vecinita_shared_schemas.internal_write import (
    EvalMetricsSummary,
    EvalRunListItem,
    EvalRunListResponse,
)

from tests.helpers.json_response import as_json_object, json_list, json_str, response_json_object

pytestmark = pytest.mark.e2e

_EXPECTED_JOB_COUNT_WITH_EVAL = 2


class _EvalRunsClient:
    """Stub internal-write client returning a running eval run."""

    def __init__(self, run_id: str) -> None:
        self._run_id = run_id

    def list_eval_runs(self, *, page: int = 1, page_size: int = 100) -> EvalRunListResponse:
        return EvalRunListResponse(
            items=[
                EvalRunListItem(
                    run_id=self._run_id,
                    status="running",
                    started_at=datetime(2026, 7, 2, 12, 0, tzinfo=UTC),
                    metrics_summary=EvalMetricsSummary(),
                )
            ],
            page=page,
            page_size=page_size,
            total_count=1,
        )


def test_uj044_unified_jobs_list_includes_eval_run_with_status() -> None:
    """TC-124: GET /jobs merges eval runs with job_type=eval and live status."""
    eval_run_id = uuid4()
    store = InMemoryJobStore()
    store.create_job(urls=["https://example.com/ingest"])
    client = TestClient(
        create_app(
            store=store,
            require_proxy_auth=False,
            eval_runs_client=_EvalRunsClient(str(eval_run_id)),  # type: ignore[arg-type]
        )
    )

    response = client.get("/jobs")

    assert response.status_code == HTTPStatus.OK
    jobs = json_list(response_json_object(response), "jobs")
    assert len(jobs) == _EXPECTED_JOB_COUNT_WITH_EVAL
    eval_job = next(
        job for job in jobs if json_str(as_json_object(job), "job_type") == "eval"
    )
    eval_body = as_json_object(eval_job)
    assert json_str(eval_body, "job_id") == str(eval_run_id)
    assert json_str(eval_body, "status") == "running"
    assert json_str(eval_body, "job_type") == "eval"
