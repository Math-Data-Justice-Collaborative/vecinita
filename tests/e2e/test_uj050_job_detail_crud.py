"""UJ-050 / TC-146-149: job detail drill-down + admin CRUD (EV-012 / #116).

Drives the data-management ASGI app end-to-end: create -> GET /jobs/{id} (type-aware
detail extras) -> admin cancel/retry/delete -> viewer 403 on mutate -> SSE status event
(TC-148) and failed-job Modal log fields (TC-149).
"""

from __future__ import annotations

import json
from http import HTTPStatus
from typing import cast
from uuid import UUID

import pytest
from fastapi.testclient import TestClient
from vecinita_data_management_backend.app import create_app
from vecinita_data_management_backend.store import InMemoryJobStore
from vecinita_shared_schemas.auth import AuthPrincipal, get_principal, reset_auth_config_for_tests
from vecinita_shared_schemas.json_types import JsonObject, as_json_object

from tests.helpers.json_response import json_str, response_json_object

pytestmark = pytest.mark.e2e

_ADMIN = AuthPrincipal(sub=UUID("11111111-1111-4111-8111-111111111111"), role="admin")
_VIEWER = AuthPrincipal(sub=UUID("22222222-2222-4222-8222-222222222222"), role="viewer")
_DOC_ID = UUID("33333333-3333-4333-8333-333333333333")
_EVAL_RUN_ID = UUID("44444444-4444-4444-8444-444444444444")
_MODAL_CALL_ID = "fc-e2e-failed"
_DASHBOARD_URL = "https://modal.com/apps/vecinita/main/fc-e2e-failed"


@pytest.fixture(autouse=True)
def _disable_auth_required(monkeypatch: pytest.MonkeyPatch) -> None:  # pyright: ignore[reportUnusedFunction]
    """Allow route tests without a live Supabase JWKS."""
    reset_auth_config_for_tests()
    monkeypatch.setenv("VECINITA_AUTH_REQUIRED", "false")


def _client(
    store: InMemoryJobStore,
    principal: AuthPrincipal,
    *,
    sse_max_cycles: int = 3,
) -> TestClient:
    app = create_app(
        store=store,
        require_proxy_auth=False,
        sse_poll_interval_s=0.05,
        sse_max_cycles=sse_max_cycles,
    )
    app.dependency_overrides[get_principal] = lambda: principal
    return TestClient(app)


def _flush_sse_block(
    blocks: list[tuple[str | None, str | None, JsonObject | None]],
    event_id: str | None,
    event_name: str | None,
    data_lines: list[str],
) -> None:
    if event_id is None and event_name is None and not data_lines:
        return
    data_obj: JsonObject | None = None
    if data_lines:
        data_obj = as_json_object(cast("object", json.loads("\n".join(data_lines))))
    blocks.append((event_id, event_name, data_obj))


def _parse_sse_blocks(raw: str) -> list[tuple[str | None, str | None, JsonObject | None]]:
    blocks: list[tuple[str | None, str | None, JsonObject | None]] = []
    event_id: str | None = None
    event_name: str | None = None
    data_lines: list[str] = []
    for line in raw.splitlines():
        if line == "":
            _flush_sse_block(blocks, event_id, event_name, data_lines)
            event_id = None
            event_name = None
            data_lines = []
            continue
        if line.startswith(":"):
            continue
        if line.startswith("id:"):
            event_id = line.removeprefix("id:").lstrip()
        elif line.startswith("event:"):
            event_name = line.removeprefix("event:").lstrip()
        elif line.startswith("data:"):
            data_lines.append(line.removeprefix("data:").lstrip())
    _flush_sse_block(blocks, event_id, event_name, data_lines)
    return blocks


def test_uj050_get_job_detail_includes_type_context_and_errors() -> None:
    """TC-146: GET /jobs/{id} returns status, timestamps, retag/eval context, errors."""
    store = InMemoryJobStore()
    ingest = store.create_job(urls=["https://example.com/ingest"])
    store.update_job(ingest.job_id, status="completed")

    retag = store.create_job(
        urls=[],
        job_type="retag",
        options={"document_id": str(_DOC_ID)},
    )
    store.update_job(
        retag.job_id,
        status="failed",
        error_code="TagError",
        error_message="retag failed",
    )

    eval_job = store.create_job(
        urls=[],
        job_type="eval",
        options={"eval_run_id": str(_EVAL_RUN_ID)},
    )
    store.update_job(eval_job.job_id, status="running", eval_run_id=_EVAL_RUN_ID)

    client = _client(store, _ADMIN)

    ingest_body = response_json_object(client.get(f"/jobs/{ingest.job_id}"))
    assert json_str(ingest_body, "status") == "completed"
    assert ingest_body.get("created_at")
    assert ingest_body.get("updated_at")
    assert json_str(ingest_body, "job_type") == "ingest"

    retag_body = response_json_object(client.get(f"/jobs/{retag.job_id}"))
    assert json_str(retag_body, "status") == "failed"
    assert retag_body.get("document_id") == str(_DOC_ID)
    assert retag_body.get("error_code") == "TagError"
    assert retag_body.get("error_message") == "retag failed"

    eval_body = response_json_object(client.get(f"/jobs/{eval_job.job_id}"))
    assert json_str(eval_body, "job_type") == "eval"
    assert eval_body.get("eval_run_id") == str(_EVAL_RUN_ID)
    assert json_str(eval_body, "status") == "running"


def test_uj050_admin_cancel_retry_delete_and_viewer_forbidden() -> None:
    """TC-147: Admin cancel/retry/delete succeed; viewer mutate returns 403 (RD-176)."""
    store = InMemoryJobStore()
    running = store.create_job(urls=["https://example.com/running"])
    store.update_job(running.job_id, status="running")
    failed = store.create_job(urls=["https://example.com/failed"])
    store.update_job(
        failed.job_id,
        status="failed",
        error_code="X",
        error_message="boom",
    )
    terminal = store.create_job(urls=["https://example.com/done"])
    store.update_job(terminal.job_id, status="completed")

    admin = _client(store, _ADMIN)
    viewer = _client(store, _VIEWER)

    assert viewer.post(f"/jobs/{running.job_id}/cancel").status_code == HTTPStatus.FORBIDDEN
    assert viewer.post(f"/jobs/{failed.job_id}/retry").status_code == HTTPStatus.FORBIDDEN
    assert viewer.delete(f"/jobs/{terminal.job_id}").status_code == HTTPStatus.FORBIDDEN
    assert store.get_job(terminal.job_id) is not None

    cancel = admin.post(f"/jobs/{running.job_id}/cancel")
    assert cancel.status_code == HTTPStatus.OK
    assert json_str(response_json_object(cancel), "status") == "cancelled"
    cancelled = store.get_job(running.job_id)
    assert cancelled is not None
    assert cancelled.status == "cancelled"

    retry = admin.post(f"/jobs/{failed.job_id}/retry")
    assert retry.status_code == HTTPStatus.ACCEPTED
    new_id = UUID(json_str(response_json_object(retry), "job_id"))
    assert new_id != failed.job_id
    new_record = store.get_job(new_id)
    assert new_record is not None
    assert new_record.status == "pending"
    assert new_record.urls == failed.urls

    delete = admin.delete(f"/jobs/{terminal.job_id}")
    assert delete.status_code == HTTPStatus.NO_CONTENT
    assert store.get_job(terminal.job_id) is None
    assert admin.get(f"/jobs/{terminal.job_id}").status_code == HTTPStatus.NOT_FOUND


def test_uj050_jobs_events_sse_emits_status_update() -> None:
    """TC-148: GET /jobs/events streams a job status update (SSE primary path)."""
    store = InMemoryJobStore()
    record = store.create_job(urls=["https://example.com/sse"])
    store.update_job(record.job_id, status="running")
    client = _client(store, _ADMIN, sse_max_cycles=8)

    with client.stream("GET", "/jobs/events") as response:
        assert response.status_code == HTTPStatus.OK
        assert response.headers["content-type"].startswith("text/event-stream")
        chunks: list[str] = []
        for chunk in response.iter_text():
            chunks.append(chunk)
            blocks = _parse_sse_blocks("".join(chunks))
            job_events = [
                data
                for _eid, name, data in blocks
                if name == "job"
                and data is not None
                and data.get("job_id") == str(record.job_id)
                and data.get("status") == "running"
            ]
            if job_events:
                break
        else:
            pytest.fail(f"timed out waiting for job SSE; chunks={chunks!r}")


def test_uj050_failed_job_detail_includes_modal_log_affordances() -> None:
    """TC-149: Failed job detail exposes modal_call_id + dashboard_url when known (RD-177)."""
    store = InMemoryJobStore()
    record = store.create_job(urls=["https://example.com/modal-fail"])
    store.update_job(
        record.job_id,
        status="failed",
        error_code="ModalError",
        error_message="container exit",
        modal_call_id=_MODAL_CALL_ID,
        dashboard_url=_DASHBOARD_URL,
    )
    client = _client(store, _ADMIN)

    body = response_json_object(client.get(f"/jobs/{record.job_id}"))
    assert json_str(body, "status") == "failed"
    assert body.get("modal_call_id") == _MODAL_CALL_ID
    assert body.get("dashboard_url") == _DASHBOARD_URL
    assert body.get("error_code") == "ModalError"
    assert body.get("error_message") == "container exit"

    # Affordance omitted when dashboard URL unknown (UI hides link).
    no_dash = store.create_job(urls=["https://example.com/no-dash"])
    store.update_job(
        no_dash.job_id,
        status="failed",
        error_code="X",
        error_message="y",
        modal_call_id="fc-only",
    )
    no_dash_body = response_json_object(client.get(f"/jobs/{no_dash.job_id}"))
    assert no_dash_body.get("modal_call_id") == "fc-only"
    assert no_dash_body.get("dashboard_url") in (None, "")
