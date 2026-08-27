"""T129.4 — finetune_train job type + POST /jobs/{id}/approve (F77 / TC-260).

[Corpus: feature-list.md §F77]
[Spec: docs/api-contract.md §Fine-tune]
[Spec: docs/adr/ADR-053-modal-lora-finetune.md]
[Spec: docs/test-plan.md §TC-260]
[Spec: docs/acceptance-criteria.md §AC-FT2]
"""

from __future__ import annotations

from http import HTTPStatus
from typing import TYPE_CHECKING
from uuid import UUID

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError
from vecinita_data_management_backend.app import create_app
from vecinita_data_management_backend.store import InMemoryJobStore
from vecinita_shared_schemas.auth import (
    AuthContext,
    AuthPrincipal,
    get_principal,
    reset_auth_config_for_tests,
    resolve_operator_or_service,
)
from vecinita_shared_schemas.data_management import CreateJobRequest, JobOptions

from tests.helpers.json_response import json_str, response_json_object

if TYPE_CHECKING:
    from collections.abc import Callable

_ADMIN = AuthPrincipal(sub=UUID("11111111-1111-4111-8111-111111111111"), role="admin")
_VIEWER = AuthPrincipal(sub=UUID("22222222-2222-4222-8222-222222222222"), role="viewer")


@pytest.fixture(autouse=True)
def _disable_auth_required(monkeypatch: pytest.MonkeyPatch) -> None:  # pyright: ignore[reportUnusedFunction]
    """Allow route tests without a live Supabase JWKS."""
    reset_auth_config_for_tests()
    monkeypatch.setenv("VECINITA_AUTH_REQUIRED", "false")


def _client_with_principal(
    store: InMemoryJobStore,
    principal: AuthPrincipal,
    *,
    runner: Callable[[UUID], None] | None = None,
) -> TestClient:
    app = create_app(
        store=store,
        require_proxy_auth=False,
        pipeline_runner=runner,
    )
    ctx = AuthContext(principal=principal, is_service=False)
    app.dependency_overrides[get_principal] = lambda: principal
    app.dependency_overrides[resolve_operator_or_service] = lambda: ctx
    return TestClient(app)


def test_create_job_request_accepts_finetune_train_without_urls() -> None:
    """Schema accepts job_type=finetune_train with empty urls (TP6)."""
    body = CreateJobRequest(options=JobOptions(job_type="finetune_train"))
    assert body.options is not None
    assert body.options.job_type == "finetune_train"
    assert body.urls == []


def test_create_job_request_rejects_unknown_finetune_typo() -> None:
    """Unknown job_type still fail-closed at schema boundary."""
    with pytest.raises(ValidationError):
        JobOptions(job_type="finetune")  # type: ignore[arg-type]


def test_post_finetune_train_stays_pending_without_starting_runner() -> None:
    """TC-260: create finetune_train does not start GPU runner until approve."""
    store = InMemoryJobStore()
    started: list[UUID] = []

    def _runner(job_id: UUID) -> None:
        started.append(job_id)

    client = _client_with_principal(store, _ADMIN, runner=_runner)
    response = client.post("/jobs", json={"options": {"job_type": "finetune_train"}})

    assert response.status_code == HTTPStatus.ACCEPTED
    body = response_json_object(response)
    assert body["status"] == "pending"
    job_id = UUID(json_str(body, "job_id"))
    record = store.get_job(job_id)
    assert record is not None
    assert record.job_type == "finetune_train"
    assert record.status == "pending"
    assert record.options.get("approved") is False
    assert started == []

    get_resp = client.get(f"/jobs/{job_id}")
    assert get_resp.status_code == HTTPStatus.OK
    get_body = response_json_object(get_resp)
    assert get_body["status"] == "pending"
    assert get_body["job_type"] == "finetune_train"
    assert get_body["approved"] is False


def test_admin_approve_finetune_train_schedules_runner() -> None:
    """TC-260 / AC-FT2: admin approve sets approved and schedules runner once."""
    store = InMemoryJobStore()
    started: list[UUID] = []

    def _runner(job_id: UUID) -> None:
        started.append(job_id)

    client = _client_with_principal(store, _ADMIN, runner=_runner)
    create = client.post("/jobs", json={"options": {"job_type": "finetune_train"}})
    job_id = UUID(json_str(response_json_object(create), "job_id"))

    response = client.post(f"/jobs/{job_id}/approve")

    assert response.status_code == HTTPStatus.OK
    body = response_json_object(response)
    assert body["job_id"] == str(job_id)
    assert body["status"] == "pending"
    assert body["job_type"] == "finetune_train"
    assert body["approved"] is True
    record = store.get_job(job_id)
    assert record is not None
    assert record.options.get("approved") is True
    assert started == [job_id]


def test_viewer_approve_returns_403() -> None:
    """Approve requires admin JWT (TP6)."""
    store = InMemoryJobStore()
    admin_client = _client_with_principal(store, _ADMIN)
    create = admin_client.post("/jobs", json={"options": {"job_type": "finetune_train"}})
    job_id = UUID(json_str(response_json_object(create), "job_id"))

    viewer = _client_with_principal(store, _VIEWER)
    response = viewer.post(f"/jobs/{job_id}/approve")
    assert response.status_code == HTTPStatus.FORBIDDEN


def test_approve_non_finetune_job_returns_409() -> None:
    """Approve is finetune_train-only (TP6)."""
    store = InMemoryJobStore()
    record = store.create_job(urls=["https://example.com/a"], job_type="ingest")
    client = _client_with_principal(store, _ADMIN)

    response = client.post(f"/jobs/{record.job_id}/approve")
    assert response.status_code == HTTPStatus.CONFLICT


def test_approve_missing_job_returns_404() -> None:
    """Unknown job id → 404."""
    store = InMemoryJobStore()
    client = _client_with_principal(store, _ADMIN)
    missing = UUID("aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa")
    response = client.post(f"/jobs/{missing}/approve")
    assert response.status_code == HTTPStatus.NOT_FOUND


def test_double_approve_returns_409() -> None:
    """Second approve on already-approved train is rejected."""
    store = InMemoryJobStore()
    client = _client_with_principal(store, _ADMIN, runner=lambda _jid: None)
    create = client.post("/jobs", json={"options": {"job_type": "finetune_train"}})
    job_id = UUID(json_str(response_json_object(create), "job_id"))
    assert client.post(f"/jobs/{job_id}/approve").status_code == HTTPStatus.OK

    response = client.post(f"/jobs/{job_id}/approve")
    assert response.status_code == HTTPStatus.CONFLICT


def test_approve_without_runner_sets_approved_only() -> None:
    """Approve with no pipeline runner still marks approved (no schedule)."""
    store = InMemoryJobStore()
    client = _client_with_principal(store, _ADMIN, runner=None)
    create = client.post("/jobs", json={"options": {"job_type": "finetune_train"}})
    job_id = UUID(json_str(response_json_object(create), "job_id"))
    response = client.post(f"/jobs/{job_id}/approve")
    assert response.status_code == HTTPStatus.OK
    body = response_json_object(response)
    assert body["approved"] is True
    record = store.get_job(job_id)
    assert record is not None
    assert record.options.get("approved") is True
    assert record.status == "pending"


def test_approve_non_pending_returns_409() -> None:
    """Cannot approve a finetune job that already left pending."""
    store = InMemoryJobStore()
    record = store.create_job(
        urls=[],
        job_type="finetune_train",
        options={"approved": False},
    )
    _ = store.update_job(record.job_id, status="running")
    client = _client_with_principal(store, _ADMIN)
    response = client.post(f"/jobs/{record.job_id}/approve")
    assert response.status_code == HTTPStatus.CONFLICT
