"""BUG-2026-09-09: pending eval jobs must not orphan without dispatch identity.

[Corpus: staging]
[Spec: docs/adr/ADR-038-modal-job-lifecycle-storage-split.md]
[Spec: docs/bug-reports/BUG-2026-09-09-stuck-pending-eval-jobs.md]
"""

from __future__ import annotations

from datetime import UTC, datetime
from http import HTTPStatus
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from fastapi.testclient import TestClient
from vecinita_data_management_backend.app import create_app
from vecinita_data_management_backend.eval_jobs import eval_run_to_job
from vecinita_data_management_backend.store import InMemoryJobStore
from vecinita_internal_write_api.app import create_app as create_write_app
from vecinita_internal_write_api.eval_run_types import CreatedEvalRun
from vecinita_internal_write_api.jobs_client import DataManagementJobsClientError
from vecinita_shared_schemas.auth import reset_auth_config_for_tests
from vecinita_shared_schemas.eval_config import EvalConfig
from vecinita_shared_schemas.internal_write import (
    EvalMetricsSummary,
    EvalRunCreateResponse,
    EvalRunListItem,
)

from tests.eval.conftest import eval_embed_fn
from tests.helpers.eval_judge import MockEvalJudge
from tests.helpers.json_response import json_str, response_json_object
from tests.unit.internal_write_api.conftest import auth_headers, database_url

if TYPE_CHECKING:
    import pytest


def test_eval_run_to_job_uses_created_at_and_sets_eval_run_id() -> None:
    """Pending eval_runs must not fake created_at with datetime.now() (plunge F2)."""
    run_id = uuid4()
    created = datetime(2026, 9, 1, 12, 0, 0, tzinfo=UTC)
    item = EvalRunListItem(
        run_id=run_id,
        status="pending",
        started_at=None,
        completed_at=None,
        created_at=created,
        metrics_summary=EvalMetricsSummary(),
        error_message=None,
    )
    job = eval_run_to_job(item)
    assert job.job_id == run_id
    assert job.job_type == "eval"
    assert job.status == "pending"
    assert job.eval_run_id == run_id
    assert job.created_at == created
    assert job.updated_at == created
    assert job.modal_call_id is None


def test_create_job_spawner_sets_modal_call_id_fail_closed() -> None:
    """POST /jobs must spawn work and persist modal_call_id (ADR-038 / TP-S013-02)."""
    store = InMemoryJobStore()
    spawned: list[UUID] = []

    def spawner(job_id: UUID) -> str:
        spawned.append(job_id)
        return f"fc-{job_id}"

    client = TestClient(
        create_app(
            store=store,
            require_proxy_auth=False,
            job_spawner=spawner,
        )
    )
    response = client.post(
        "/jobs",
        json={"urls": [], "options": {"job_type": "eval", "eval_run_id": str(uuid4())}},
    )
    assert response.status_code == HTTPStatus.ACCEPTED
    job_id = UUID(json_str(response_json_object(response), "job_id"))
    assert spawned == [job_id]
    record = store.get_job(job_id)
    assert record is not None
    assert record.modal_call_id == f"fc-{job_id}"
    assert record.status == "pending"


def test_create_job_spawner_failure_marks_job_failed() -> None:
    """Spawn failure must fail closed — no forever-pending JobStore row."""
    store = InMemoryJobStore()

    def boom(_job_id: UUID) -> str:
        msg = "spawn denied"
        raise RuntimeError(msg)

    client = TestClient(
        create_app(
            store=store,
            require_proxy_auth=False,
            job_spawner=boom,
        )
    )
    response = client.post(
        "/jobs",
        json={"urls": ["https://example.com/page"]},
    )
    assert response.status_code == HTTPStatus.BAD_GATEWAY
    jobs = store.list_jobs()
    assert len(jobs) == 1
    assert jobs[0].status == "failed"
    assert jobs[0].modal_call_id is None
    assert jobs[0].error_code == "RuntimeError"


def test_create_eval_run_enqueue_failure_marks_run_failed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Orphan pending eval_runs are forbidden when Modal enqueue fails."""
    reset_auth_config_for_tests()
    monkeypatch.setenv("DATABASE_URL", database_url())
    monkeypatch.setenv("VECINITA_INTERNAL_API_KEY", "test-internal-key")
    monkeypatch.setenv("SUPABASE_URL", "https://test.supabase.co")
    monkeypatch.setenv("VECINITA_AUTH_REQUIRED", "true")

    run_id = uuid4()
    marked: list[tuple[UUID, str]] = []

    def fake_create(*_a: object, **_k: object) -> CreatedEvalRun:
        return CreatedEvalRun(
            response=EvalRunCreateResponse(
                run_id=run_id,
                status="pending",
                created_at=datetime.now(UTC),
            ),
            corpus_profile="staging",
            mode="golden",
            question=None,
            config_snapshot=EvalConfig(),
        )

    def fake_fail(_engine: object, *, run_id: UUID, error_message: str) -> None:
        marked.append((run_id, error_message))

    class BoomJobs:
        def enqueue_eval(self, *_a: object, **_k: object) -> UUID:
            msg = "modal unreachable"
            raise DataManagementJobsClientError(msg)

    monkeypatch.setattr(
        "vecinita_internal_write_api.routes.eval_runs.create_eval_run",
        fake_create,
    )
    monkeypatch.setattr(
        "vecinita_internal_write_api.routes.eval_runs.fail_eval_run_dispatch",
        fake_fail,
    )

    app = create_write_app(
        eval_embed_fn=eval_embed_fn,
        eval_judge=MockEvalJudge(),
        jobs_client=BoomJobs(),  # type: ignore[arg-type]
    )
    client = TestClient(app)
    response = client.post(
        "/internal/v1/eval/runs",
        headers=auth_headers(),
        json={"corpus_profile": "fixture"},
    )
    assert response.status_code == HTTPStatus.BAD_GATEWAY
    assert marked == [(run_id, "modal unreachable")]
