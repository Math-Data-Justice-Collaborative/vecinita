"""T82.1 / TC-146-147 - Admin job cancel, retry, delete + Job schema extras (EV-012)."""

from __future__ import annotations

from http import HTTPStatus
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient
from vecinita_data_management_backend.app import create_app
from vecinita_data_management_backend.store import InMemoryJobStore, job_record_to_schema
from vecinita_data_management_backend.write_client import InternalWriteClientError
from vecinita_shared_schemas.auth import (
    AuthContext,
    AuthPrincipal,
    get_principal,
    reset_auth_config_for_tests,
    resolve_operator_or_service,
)
from vecinita_shared_schemas.json_types import as_json_object

from tests.helpers.json_response import json_list, json_str, response_json_object

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
    ctx = AuthContext(principal=principal, is_service=False)
    app.dependency_overrides[get_principal] = lambda: principal
    app.dependency_overrides[resolve_operator_or_service] = lambda: ctx
    return TestClient(app)


def test_admin_cancel_sets_job_cancelled() -> None:
    """POST /jobs/{id}/cancel marks the job cancelled (TC-147)."""
    store = InMemoryJobStore()
    record = store.create_job(urls=["https://example.com/a"])
    _ = store.update_job(record.job_id, status="running")
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
    _ = store.update_job(record.job_id, status="failed", error_code="X", error_message="boom")
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


def test_admin_retry_finetune_train_clears_approved_flag() -> None:
    """Retrying failed finetune_train requires a fresh operator approve (ADR-053)."""
    store = InMemoryJobStore()
    record = store.create_job(
        urls=[],
        job_type="finetune_train",
        options={"approved": True},
    )
    _ = store.update_job(record.job_id, status="failed", error_code="X", error_message="boom")
    client = _client_with_principal(store, _ADMIN)

    response = client.post(f"/jobs/{record.job_id}/retry")

    assert response.status_code == HTTPStatus.ACCEPTED
    body = response_json_object(response)
    new_id = UUID(json_str(body, "job_id"))
    new_record = store.get_job(new_id)
    assert new_record is not None
    assert new_record.job_type == "finetune_train"
    assert new_record.options.get("approved") is False


def test_viewer_retry_returns_403() -> None:
    """Viewer cannot retry jobs (TC-147)."""
    store = InMemoryJobStore()
    record = store.create_job(urls=["https://example.com/a"])
    _ = store.update_job(record.job_id, status="failed")
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


def test_admin_delete_eval_job_soft_deletes_linked_run() -> None:
    """DELETE eval job soft-deletes linked eval_run via write client (TP-S013-03)."""
    store = InMemoryJobStore()
    record = store.create_job(
        urls=[],
        job_type="eval",
        options={"eval_run_id": str(_EVAL_RUN_ID)},
    )
    _ = store.update_job(record.job_id, eval_run_id=_EVAL_RUN_ID)
    soft_deleted: list[UUID] = []

    class _EvalClient:
        def soft_delete_eval_run(self, run_id: UUID) -> None:
            soft_deleted.append(run_id)

        def list_eval_runs(self, *, page: int = 1, page_size: int = 100) -> object:
            _ = (page, page_size)
            return type("Empty", (), {"items": []})()

    app = create_app(
        store=store,
        require_proxy_auth=False,
        eval_runs_client=_EvalClient(),  # type: ignore[arg-type]
    )
    app.dependency_overrides[get_principal] = lambda: _ADMIN
    client = TestClient(app)

    response = client.delete(f"/jobs/{record.job_id}")

    assert response.status_code == HTTPStatus.NO_CONTENT
    assert store.get_job(record.job_id) is None
    assert soft_deleted == [_EVAL_RUN_ID]


def test_admin_delete_eval_job_reads_eval_run_id_from_options() -> None:
    """When record.eval_run_id is unset, DELETE reads options.eval_run_id (TP-S013-03)."""
    store = InMemoryJobStore()
    record = store.create_job(urls=[], job_type="eval", options={})
    stored = store.get_job(record.job_id)
    assert stored is not None
    stored.options["eval_run_id"] = str(_EVAL_RUN_ID)
    soft_deleted: list[UUID] = []

    class _EvalClient:
        def soft_delete_eval_run(self, run_id: UUID) -> None:
            soft_deleted.append(run_id)

        def list_eval_runs(self, *, page: int = 1, page_size: int = 100) -> object:
            _ = (page, page_size)
            return type("Empty", (), {"items": []})()

    app = create_app(
        store=store,
        require_proxy_auth=False,
        eval_runs_client=_EvalClient(),  # type: ignore[arg-type]
    )
    app.dependency_overrides[get_principal] = lambda: _ADMIN
    client = TestClient(app)

    response = client.delete(f"/jobs/{record.job_id}")

    assert response.status_code == HTTPStatus.NO_CONTENT
    assert soft_deleted == [_EVAL_RUN_ID]


def test_admin_delete_eval_job_soft_delete_error_returns_502() -> None:
    """Write-API soft-delete failure surfaces as 502 on Modal DELETE."""
    store = InMemoryJobStore()
    record = store.create_job(
        urls=[],
        job_type="eval",
        options={"eval_run_id": str(_EVAL_RUN_ID)},
    )
    _ = store.update_job(record.job_id, eval_run_id=_EVAL_RUN_ID)

    class _EvalClient:
        def soft_delete_eval_run(self, run_id: UUID) -> None:
            _ = run_id
            msg = "write down"
            raise InternalWriteClientError(msg)

        def list_eval_runs(self, *, page: int = 1, page_size: int = 100) -> object:
            _ = (page, page_size)
            return type("Empty", (), {"items": []})()

    app = create_app(
        store=store,
        require_proxy_auth=False,
        eval_runs_client=_EvalClient(),  # type: ignore[arg-type]
    )
    app.dependency_overrides[get_principal] = lambda: _ADMIN
    client = TestClient(app)

    response = client.delete(f"/jobs/{record.job_id}")

    assert response.status_code == HTTPStatus.BAD_GATEWAY
    assert store.get_job(record.job_id) is not None


def test_admin_delete_unknown_job_returns_404() -> None:
    """DELETE missing job_id returns 404."""
    store = InMemoryJobStore()
    client = _client_with_principal(store, _ADMIN)
    response = client.delete(f"/jobs/{uuid4()}")
    assert response.status_code == HTTPStatus.NOT_FOUND


def test_admin_delete_eval_job_without_write_client_still_deletes() -> None:
    """Eval job DELETE without eval_runs_client removes the JobStore row only."""
    store = InMemoryJobStore()
    record = store.create_job(
        urls=[],
        job_type="eval",
        options={"eval_run_id": str(_EVAL_RUN_ID)},
    )
    app = create_app(store=store, require_proxy_auth=False, eval_runs_client=None)
    app.dependency_overrides[get_principal] = lambda: _ADMIN
    client = TestClient(app)

    response = client.delete(f"/jobs/{record.job_id}")

    assert response.status_code == HTTPStatus.NO_CONTENT
    assert store.get_job(record.job_id) is None


def test_admin_delete_eval_job_skips_soft_delete_for_non_str_option() -> None:
    """Non-string options.eval_run_id is ignored when record.eval_run_id is unset."""
    store = InMemoryJobStore()
    record = store.create_job(urls=[], job_type="eval", options={})
    stored = store.get_job(record.job_id)
    assert stored is not None
    stored.options["eval_run_id"] = 12345
    soft_deleted: list[UUID] = []

    class _EvalClient:
        def soft_delete_eval_run(self, run_id: UUID) -> None:
            soft_deleted.append(run_id)

        def list_eval_runs(self, *, page: int = 1, page_size: int = 100) -> object:
            _ = (page, page_size)
            return type("Empty", (), {"items": []})()

    app = create_app(
        store=store,
        require_proxy_auth=False,
        eval_runs_client=_EvalClient(),  # type: ignore[arg-type]
    )
    app.dependency_overrides[get_principal] = lambda: _ADMIN
    client = TestClient(app)

    response = client.delete(f"/jobs/{record.job_id}")

    assert response.status_code == HTTPStatus.NO_CONTENT
    assert soft_deleted == []


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
    _ = store.update_job(
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
    _ = store.update_job(
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


def test_cancel_terminal_job_returns_409() -> None:
    """Cannot cancel a completed job (409)."""
    store = InMemoryJobStore()
    record = store.create_job(urls=["https://example.com/a"])
    _ = store.update_job(record.job_id, status="completed")
    client = _client_with_principal(store, _ADMIN)

    response = client.post(f"/jobs/{record.job_id}/cancel")

    assert response.status_code == HTTPStatus.CONFLICT


def test_cancel_invokes_modal_cancel_when_call_id_present() -> None:
    """Best-effort FunctionCall.cancel when modal_call_id is set."""
    store = InMemoryJobStore()
    record = store.create_job(urls=["https://example.com/a"])
    _ = store.update_job(record.job_id, status="running", modal_call_id="fc-123")
    cancelled: list[str] = []

    def _cancel(call_id: str) -> None:
        cancelled.append(call_id)

    app = create_app(
        store=store,
        require_proxy_auth=False,
        cancel_modal_call=_cancel,
    )
    app.dependency_overrides[get_principal] = lambda: _ADMIN
    client = TestClient(app)

    response = client.post(f"/jobs/{record.job_id}/cancel")

    assert response.status_code == HTTPStatus.OK
    assert cancelled == ["fc-123"]


def test_cancel_swallows_modal_cancel_errors() -> None:
    """Modal cancel failures do not block JobStore cancelled status."""
    store = InMemoryJobStore()
    record = store.create_job(urls=["https://example.com/a"])
    _ = store.update_job(record.job_id, status="running", modal_call_id="fc-boom")

    def _cancel(_call_id: str) -> None:
        msg = "modal down"
        raise RuntimeError(msg)

    app = create_app(
        store=store,
        require_proxy_auth=False,
        cancel_modal_call=_cancel,
    )
    app.dependency_overrides[get_principal] = lambda: _ADMIN
    client = TestClient(app)

    response = client.post(f"/jobs/{record.job_id}/cancel")

    assert response.status_code == HTTPStatus.OK
    assert response_json_object(response)["status"] == "cancelled"


def test_retry_running_job_returns_409() -> None:
    """Cannot retry a running job."""
    store = InMemoryJobStore()
    record = store.create_job(urls=["https://example.com/a"])
    _ = store.update_job(record.job_id, status="running")
    client = _client_with_principal(store, _ADMIN)

    response = client.post(f"/jobs/{record.job_id}/retry")

    assert response.status_code == HTTPStatus.CONFLICT


def test_delete_unknown_job_returns_404() -> None:
    """DELETE missing job returns 404."""
    store = InMemoryJobStore()
    client = _client_with_principal(store, _ADMIN)

    response = client.delete(f"/jobs/{uuid4()}")

    assert response.status_code == HTTPStatus.NOT_FOUND


def test_delete_job_returns_404_when_store_delete_fails(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """DELETE returns 404 when JobStore delete fails after the record was found."""
    store = InMemoryJobStore()
    record = store.create_job(urls=["https://example.com/a"])

    def _delete_always_false(_job_id: UUID) -> bool:
        return False

    monkeypatch.setattr(store, "delete_job", _delete_always_false)
    client = _client_with_principal(store, _ADMIN)

    response = client.delete(f"/jobs/{record.job_id}")

    assert response.status_code == HTTPStatus.NOT_FOUND
    assert store.get_job(record.job_id) is not None


def test_create_job_with_eval_run_id_option() -> None:
    """POST /jobs accepts eval job_type with eval_run_id."""
    store = InMemoryJobStore()
    client = _client_with_principal(store, _ADMIN)
    eval_run_id = uuid4()

    response = client.post(
        "/jobs",
        json={
            "urls": [],
            "options": {"job_type": "eval", "eval_run_id": str(eval_run_id)},
        },
    )

    assert response.status_code == HTTPStatus.ACCEPTED
    job_id = UUID(json_str(response_json_object(response), "job_id"))
    record = store.get_job(job_id)
    assert record is not None
    assert record.job_type == "eval"
    assert record.options.get("eval_run_id") == str(eval_run_id)


def test_create_job_continues_when_audit_emit_fails() -> None:
    """Audit failures must not block job enqueue."""
    store = InMemoryJobStore()

    def _boom(_event: object) -> None:
        msg = "audit down"
        raise RuntimeError(msg)

    app = create_app(store=store, require_proxy_auth=False, audit_emit=_boom)
    app.dependency_overrides[get_principal] = lambda: _ADMIN
    client = TestClient(app)

    response = client.post("/jobs", json={"urls": ["https://example.com/a"]})

    assert response.status_code == HTTPStatus.ACCEPTED


def test_retry_unknown_job_returns_404() -> None:
    """Retry missing job returns 404."""
    store = InMemoryJobStore()
    client = _client_with_principal(store, _ADMIN)

    response = client.post(f"/jobs/{uuid4()}/retry")

    assert response.status_code == HTTPStatus.NOT_FOUND


def test_retry_schedules_pipeline_runner_when_injected() -> None:
    """Retry adds background task when pipeline_runner is set."""
    store = InMemoryJobStore()
    record = store.create_job(urls=["https://example.com/a"])
    _ = store.update_job(record.job_id, status="failed")
    ran: list[UUID] = []

    def _runner(job_id: UUID) -> None:
        ran.append(job_id)

    app = create_app(store=store, require_proxy_auth=False, pipeline_runner=_runner)
    app.dependency_overrides[get_principal] = lambda: _ADMIN
    client = TestClient(app)

    response = client.post(f"/jobs/{record.job_id}/retry")

    assert response.status_code == HTTPStatus.ACCEPTED
    assert len(ran) == 1


def test_list_jobs_swallows_eval_client_errors() -> None:
    """Eval aggregation errors leave Modal jobs list intact."""
    store = InMemoryJobStore()
    _ = store.create_job(urls=["https://example.com/a"])

    class _BrokenEval:
        def list_eval_runs(self, *, page_size: int = 100) -> object:
            _ = page_size
            msg = "upstream"
            raise InternalWriteClientError(msg)

    app = create_app(
        store=store,
        require_proxy_auth=False,
        eval_runs_client=_BrokenEval(),  # type: ignore[arg-type]
    )
    app.dependency_overrides[get_principal] = lambda: _ADMIN
    client = TestClient(app)

    response = client.get("/jobs")

    assert response.status_code == HTTPStatus.OK
    assert len(json_list(response_json_object(response), "jobs")) == 1
