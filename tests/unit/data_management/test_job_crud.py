"""T82.1 / TC-146–147 — Admin job cancel, retry, delete + Job schema extras (EV-012).

Red until M82 store + routes land (T82.3 / T82.4).
"""

from __future__ import annotations

from http import HTTPStatus
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient
from vecinita_data_management_backend.app import create_app
from vecinita_data_management_backend.store import InMemoryJobStore, job_record_to_schema
from vecinita_shared_schemas.auth import AuthPrincipal, get_principal, reset_auth_config_for_tests
from vecinita_shared_schemas.json_types import as_json_object

from tests.helpers.json_response import json_str, response_json_object

_ADMIN = AuthPrincipal(sub=UUID("11111111-1111-4111-8111-111111111111"), role="admin")
_VIEWER = AuthPrincipal(sub=UUID("22222222-2222-4222-8222-222222222222"), role="viewer")
_DOC_ID = UUID("33333333-3333-4333-8333-333333333333")
_EVAL_RUN_ID = UUID("44444444-4444-4444-8444-444444444444")


@pytest.fixture(autouse=True)
def _disable_auth_required(monkeypatch: pytest.MonkeyPatch) -> None:  # pyright: ignore[reportUnusedFunction]
    """Allow route tests without a live Supabase JWKS."""
    reset_auth_config_for_tests()
    monkeypatch.setenv("VECINITA_AUTH_REQUIRED", "false")


def _client_with_principal(
    store: InMemoryJobStore,
    principal: AuthPrincipal,
) -> TestClient:
    app = create_app(store=store, require_proxy_auth=False)
    app.dependency_overrides[get_principal] = lambda: principal
    return TestClient(app)


def test_admin_cancel_sets_job_cancelled() -> None:
    """POST /jobs/{id}/cancel marks the job cancelled (TC-147)."""
    store = InMemoryJobStore()
    record = store.create_job(urls=["https://example.com/a"])
    store.update_job(record.job_id, status="running")
    client = _client_with_principal(store, _ADMIN)

    response = client.post(f"/jobs/{record.job_id}/cancel")

    assert response.status_code == HTTPStatus.OK
    body = response_json_object(response)
    assert body["status"] == "cancelled"
    assert json_str(body, "job_id") == str(record.job_id)
    updated = store.get_job(record.job_id)
    assert updated is not None
    assert updated.status == "cancelled"


def test_viewer_cancel_returns_403() -> None:
    """Viewer cannot cancel jobs (TC-147 / RD-176)."""
    store = InMemoryJobStore()
    record = store.create_job(urls=["https://example.com/a"])
    client = _client_with_principal(store, _VIEWER)

    response = client.post(f"/jobs/{record.job_id}/cancel")

    assert response.status_code == HTTPStatus.FORBIDDEN


def test_admin_retry_returns_202_new_job() -> None:
    """POST /jobs/{id}/retry accepts and returns a new pending job_id (TC-147)."""
    store = InMemoryJobStore()
    record = store.create_job(urls=["https://example.com/a"])
    store.update_job(record.job_id, status="failed", error_code="X", error_message="boom")
    client = _client_with_principal(store, _ADMIN)

    response = client.post(f"/jobs/{record.job_id}/retry")

    assert response.status_code == HTTPStatus.ACCEPTED
    body = response_json_object(response)
    assert body["status"] == "pending"
    new_id = UUID(json_str(body, "job_id"))
    assert new_id != record.job_id
    new_record = store.get_job(new_id)
    assert new_record is not None
    assert new_record.status == "pending"
    assert new_record.urls == record.urls


def test_viewer_retry_returns_403() -> None:
    """Viewer cannot retry jobs (TC-147)."""
    store = InMemoryJobStore()
    record = store.create_job(urls=["https://example.com/a"])
    store.update_job(record.job_id, status="failed")
    client = _client_with_principal(store, _VIEWER)

    response = client.post(f"/jobs/{record.job_id}/retry")

    assert response.status_code == HTTPStatus.FORBIDDEN


def test_admin_delete_removes_job() -> None:
    """DELETE /jobs/{id} removes the JobStore record (TC-147)."""
    store = InMemoryJobStore()
    record = store.create_job(urls=["https://example.com/a"])
    client = _client_with_principal(store, _ADMIN)

    response = client.delete(f"/jobs/{record.job_id}")

    assert response.status_code == HTTPStatus.NO_CONTENT
    assert store.get_job(record.job_id) is None


def test_viewer_delete_returns_403() -> None:
    """Viewer cannot delete jobs (TC-147)."""
    store = InMemoryJobStore()
    record = store.create_job(urls=["https://example.com/a"])
    client = _client_with_principal(store, _VIEWER)

    response = client.delete(f"/jobs/{record.job_id}")

    assert response.status_code == HTTPStatus.FORBIDDEN
    assert store.get_job(record.job_id) is not None


def test_get_job_includes_ev012_extras() -> None:
    """GET /jobs/{id} surfaces document_id, eval_run_id, modal_call_id, dashboard_url (TC-146)."""
    store = InMemoryJobStore()
    record = store.create_job(
        urls=[],
        job_type="retag",
        options={"document_id": str(_DOC_ID)},
    )
    store.update_job(
        record.job_id,
        status="failed",
        error_code="PipelineError",
        error_message="failed",
        modal_call_id="fc-abc123",
        dashboard_url="https://modal.com/apps/vecinita/main/fc-abc123",
        eval_run_id=_EVAL_RUN_ID,
    )
    # Retag jobs keep document_id in options; eval_run_id may be set on record.
    client = _client_with_principal(store, _ADMIN)

    response = client.get(f"/jobs/{record.job_id}")

    assert response.status_code == HTTPStatus.OK
    body = response_json_object(response)
    assert body.get("document_id") == str(_DOC_ID)
    assert body.get("modal_call_id") == "fc-abc123"
    assert body.get("dashboard_url") == "https://modal.com/apps/vecinita/main/fc-abc123"
    assert body.get("eval_run_id") == str(_EVAL_RUN_ID)


def test_job_record_to_schema_maps_cancelled_and_extras() -> None:
    """Job schema accepts cancelled status and EV-012 extras (TC-146)."""
    store = InMemoryJobStore()
    record = store.create_job(
        urls=["https://example.com/a"],
        job_type="eval",
        options={"eval_run_id": str(_EVAL_RUN_ID)},
    )
    store.update_job(
        record.job_id,
        status="cancelled",
        modal_call_id="fc-xyz",
        dashboard_url="https://modal.com/apps/example",
        eval_run_id=_EVAL_RUN_ID,
    )
    refreshed = store.get_job(record.job_id)
    assert refreshed is not None

    schema = job_record_to_schema(refreshed)
    payload = as_json_object(schema.model_dump(mode="json"))

    assert payload["status"] == "cancelled"
    assert payload.get("eval_run_id") == str(_EVAL_RUN_ID)
    assert payload.get("modal_call_id") == "fc-xyz"
    assert payload.get("dashboard_url") == "https://modal.com/apps/example"


def test_cancel_unknown_job_returns_404() -> None:
    """Cancel on missing job_id returns 404."""
    store = InMemoryJobStore()
    client = _client_with_principal(store, _ADMIN)

    response = client.post(f"/jobs/{uuid4()}/cancel")

    assert response.status_code == HTTPStatus.NOT_FOUND
