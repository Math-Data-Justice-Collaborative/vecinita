"""UJ-044 / TC-124: unified GET /jobs includes eval runs (EV-009, ADR-035 / ADR-038)."""

from __future__ import annotations

from datetime import UTC, datetime
from http import HTTPStatus
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient
from vecinita_data_management_backend.app import create_app
from vecinita_data_management_backend.store import InMemoryJobStore
from vecinita_shared_schemas.auth import AuthPrincipal, get_principal, reset_auth_config_for_tests
from vecinita_shared_schemas.internal_write import (
    EvalMetricsSummary,
    EvalRunListItem,
    EvalRunListResponse,
)

from tests.helpers.json_response import as_json_object, json_list, json_str, response_json_object

pytestmark = pytest.mark.e2e

_EXPECTED_JOB_COUNT_WITH_EVAL = 2
_ADMIN = AuthPrincipal(sub=UUID("11111111-1111-4111-8111-111111111111"), role="admin")


class _EvalRunsClient:
    """Stub internal-write client returning a running eval run."""

    def __init__(self, run_id: UUID) -> None:
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
    """TC-124: GET /jobs merges DO eval runs with job_type=eval and live status."""
    eval_run_id = uuid4()
    store = InMemoryJobStore()
    _ = store.create_job(urls=["https://example.com/ingest"])
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
    eval_job = next(job for job in jobs if json_str(as_json_object(job), "job_type") == "eval")
    eval_body = as_json_object(eval_job)
    assert json_str(eval_body, "job_id") == str(eval_run_id)
    assert json_str(eval_body, "status") == "running"
    assert json_str(eval_body, "job_type") == "eval"


def test_uj044_modal_native_eval_job_on_jobs_list(monkeypatch: pytest.MonkeyPatch) -> None:
    """TC-124 (EV-012): Modal JobStore job_type=eval appears on GET /jobs (ADR-038)."""
    reset_auth_config_for_tests()
    monkeypatch.setenv("VECINITA_AUTH_REQUIRED", "false")
    eval_run_id = uuid4()
    store = InMemoryJobStore()
    _ = store.create_job(urls=["https://example.com/ingest"])
    eval_record = store.create_job(
        urls=[],
        job_type="eval",
        options={"eval_run_id": str(eval_run_id)},
    )
    _ = store.update_job(eval_record.job_id, status="running", eval_run_id=eval_run_id)
    app = create_app(store=store, require_proxy_auth=False)
    app.dependency_overrides[get_principal] = lambda: _ADMIN
    client = TestClient(app)

    response = client.get("/jobs")
    assert response.status_code == HTTPStatus.OK
    jobs = json_list(response_json_object(response), "jobs")
    eval_jobs = [
        as_json_object(job)
        for job in jobs
        if json_str(as_json_object(job), "job_type") == "eval"
        and json_str(as_json_object(job), "job_id") == str(eval_record.job_id)
    ]
    assert len(eval_jobs) == 1
    assert eval_jobs[0].get("eval_run_id") == str(eval_run_id)
    assert json_str(eval_jobs[0], "status") == "running"

    filtered = client.get("/jobs", params={"status": "running"})
    assert filtered.status_code == HTTPStatus.OK
    running_ids = {
        json_str(as_json_object(job), "job_id")
        for job in json_list(response_json_object(filtered), "jobs")
    }
    assert str(eval_record.job_id) in running_ids
