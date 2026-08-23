"""Unit tests for vecinita_data_management_backend.app."""

from __future__ import annotations

from datetime import UTC, datetime
from http import HTTPStatus
from uuid import UUID, uuid4

import httpx
import pytest
from fastapi.testclient import TestClient
from vecinita_data_management_backend.app import (
    create_app,
)
from vecinita_data_management_backend.store import InMemoryJobStore
from vecinita_data_management_backend.write_client import InternalWriteClient
from vecinita_shared_schemas.auth import reset_auth_config_for_tests
from vecinita_shared_schemas.internal_write import (
    AuditEventRequest,
    EvalMetricsSummary,
    EvalRunListItem,
    EvalRunListResponse,
)
from vecinita_shared_schemas.json_types import as_json_object

from tests.helpers.json_response import (
    json_list,
    json_str,
    response_json_object,
)
from tests.helpers.user_admin_mocks import make_client, seed_users

_PROXY_KEY = "unit-test-proxy-key"
_CHUNK_SIZE_TOKENS = 128
_EXPECTED_JOB_LIST_COUNT = 2


@pytest.fixture(autouse=True)
def _disable_auth_required(monkeypatch: pytest.MonkeyPatch) -> None:  # pyright: ignore[reportUnusedFunction]
    """Allow data-management routes to use the dev auth bypass in unit tests."""
    reset_auth_config_for_tests()
    monkeypatch.setenv("VECINITA_AUTH_REQUIRED", "false")


def test_health_returns_ok() -> None:
    """Test health returns ok."""
    client = TestClient(create_app(require_proxy_auth=False))

    response = client.get("/health")

    assert response.status_code == HTTPStatus.OK
    assert response_json_object(response) == {"status": "ok"}


def test_create_job_requires_proxy_key_when_auth_enabled(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test create job requires proxy key when auth enabled."""
    monkeypatch.setenv("VECINITA_MODAL_PROXY_KEY", _PROXY_KEY)
    client = TestClient(create_app(require_proxy_auth=True))

    response = client.post("/jobs", json={"urls": ["https://example.com/page"]})

    assert response.status_code == HTTPStatus.UNAUTHORIZED


def test_proxy_auth_not_configured_returns_503(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test proxy auth not configured returns 503."""
    monkeypatch.delenv("VECINITA_MODAL_PROXY_KEY", raising=False)
    monkeypatch.delenv("MODAL_PROXY_KEY", raising=False)
    client = TestClient(create_app(require_proxy_auth=True))

    response = client.post(
        "/jobs",
        json={"urls": ["https://example.com/page"]},
        headers={"X-Vecinita-Proxy-Key": "any"},
    )

    assert response.status_code == HTTPStatus.SERVICE_UNAVAILABLE


def test_create_job_accepts_retag_options() -> None:
    """Test create job accepts retag options."""
    store = InMemoryJobStore()
    document_id = uuid4()
    client = TestClient(create_app(store=store, require_proxy_auth=False))

    response = client.post(
        "/jobs",
        json={
            "urls": [],
            "options": {
                "job_type": "retag",
                "document_id": str(document_id),
                "chunk_size_tokens": _CHUNK_SIZE_TOKENS,
            },
        },
    )

    assert response.status_code == HTTPStatus.ACCEPTED
    job_id = UUID(json_str(response_json_object(response), "job_id"))
    record = store.get_job(job_id)
    assert record is not None
    assert record.job_type == "retag"
    assert record.options["document_id"] == str(document_id)
    assert record.options["chunk_size_tokens"] == _CHUNK_SIZE_TOKENS


def test_create_job_accepts_rebuild_options_without_backfill() -> None:
    """POST /jobs persists rebuild mode/force/dry_run/document_ids (T88.1 / TC-161)."""
    store = InMemoryJobStore()
    doc_id = uuid4()
    client = TestClient(create_app(store=store, require_proxy_auth=False))

    response = client.post(
        "/jobs",
        json={
            "urls": [],
            "options": {
                "job_type": "rebuild",
                "mode": "rechunk",
                "force": True,
                "dry_run": True,
                "document_ids": [str(doc_id)],
            },
        },
    )

    assert response.status_code == HTTPStatus.ACCEPTED
    job_id = UUID(json_str(response_json_object(response), "job_id"))
    record = store.get_job(job_id)
    assert record is not None
    assert record.job_type == "rebuild"
    assert record.options["mode"] == "rechunk"
    assert record.options["force"] is True
    assert record.options["dry_run"] is True
    assert record.options["document_ids"] == [str(doc_id)]
    assert "backfill" not in record.options


def test_create_job_accepts_backfill_rebuild_options() -> None:
    """POST /jobs persists rebuild backfill options (T87.5 / TP-S017-08)."""
    store = InMemoryJobStore()
    doc_id = uuid4()
    client = TestClient(create_app(store=store, require_proxy_auth=False))

    response = client.post(
        "/jobs",
        json={
            "urls": [],
            "options": {
                "job_type": "rebuild",
                "mode": "rescrape",
                "backfill": True,
                "backfill_source": "rescrape",
                "document_ids": [str(doc_id)],
                "force": True,
                "dry_run": False,
            },
        },
    )

    assert response.status_code == HTTPStatus.ACCEPTED
    job_id = UUID(json_str(response_json_object(response), "job_id"))
    record = store.get_job(job_id)
    assert record is not None
    assert record.job_type == "rebuild"
    assert record.options["mode"] == "rescrape"
    assert record.options["backfill"] is True
    assert record.options["backfill_source"] == "rescrape"
    assert record.options["document_ids"] == [str(doc_id)]
    assert record.options["force"] is True


def test_create_job_persists_from_chunks_ack_flag() -> None:
    """ack_reconstruct_from_chunks is stored when backfill_source=from_chunks."""
    store = InMemoryJobStore()
    client = TestClient(create_app(store=store, require_proxy_auth=False))
    response = client.post(
        "/jobs",
        json={
            "urls": [],
            "options": {
                "job_type": "rebuild",
                "mode": "rechunk",
                "backfill": True,
                "backfill_source": "from_chunks",
                "ack_reconstruct_from_chunks": True,
            },
        },
    )
    assert response.status_code == HTTPStatus.ACCEPTED
    job_id = UUID(json_str(response_json_object(response), "job_id"))
    record = store.get_job(job_id)
    assert record is not None
    assert record.options["backfill_source"] == "from_chunks"
    assert record.options["ack_reconstruct_from_chunks"] is True


def test_create_job_emits_job_created_audit() -> None:
    """POST /jobs records job.created with the initiating operator."""
    captured: list[AuditEventRequest] = []
    store = InMemoryJobStore()
    client = TestClient(
        create_app(
            store=store,
            require_proxy_auth=False,
            audit_emit=captured.append,
        )
    )

    response = client.post("/jobs", json={"urls": ["https://example.com/page"]})

    assert response.status_code == HTTPStatus.ACCEPTED
    assert len(captured) == 1
    assert captured[0].event_type == "job.created"
    assert captured[0].entity_type == "job"
    assert captured[0].actor_id is not None
    job_id = UUID(json_str(response_json_object(response), "job_id"))
    record = store.get_job(job_id)
    assert record is not None
    assert record.initiated_by_user_id == captured[0].actor_id


def test_create_job_schedules_pipeline_runner() -> None:
    """Test create job schedules pipeline runner."""
    scheduled: list[UUID] = []
    store = InMemoryJobStore()
    client = TestClient(
        create_app(
            store=store,
            require_proxy_auth=False,
            pipeline_runner=scheduled.append,
        )
    )

    response = client.post("/jobs", json={"urls": ["https://example.com/page"]})

    assert response.status_code == HTTPStatus.ACCEPTED
    job_id = UUID(json_str(response_json_object(response), "job_id"))
    assert scheduled == [job_id]


def test_create_job_succeeds_with_valid_proxy_key(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test create job succeeds with valid proxy key."""
    monkeypatch.setenv("VECINITA_MODAL_PROXY_KEY", _PROXY_KEY)
    client = TestClient(create_app(require_proxy_auth=True))

    response = client.post(
        "/jobs",
        json={"urls": ["https://example.com/page"]},
        headers={"X-Vecinita-Proxy-Key": _PROXY_KEY},
    )

    assert response.status_code == HTTPStatus.ACCEPTED


def test_create_job_without_options_uses_defaults() -> None:
    """Test create job without options uses defaults."""
    store = InMemoryJobStore()
    client = TestClient(create_app(store=store, require_proxy_auth=False))

    response = client.post("/jobs", json={"urls": ["https://example.com/page"]})

    assert response.status_code == HTTPStatus.ACCEPTED
    job_id = UUID(json_str(response_json_object(response), "job_id"))
    record = store.get_job(job_id)
    assert record is not None
    assert record.job_type == "ingest"
    assert record.options == {}


def test_get_job_returns_404_for_unknown_id() -> None:
    """Test get job returns 404 for unknown id."""
    client = TestClient(create_app(require_proxy_auth=False))

    response = client.get(f"/jobs/{uuid4()}")

    assert response.status_code == HTTPStatus.NOT_FOUND


def test_get_job_returns_existing_job() -> None:
    """Test get job returns existing job."""
    store = InMemoryJobStore()
    record = store.create_job(urls=["https://example.com/page"])
    client = TestClient(create_app(store=store, require_proxy_auth=False))

    response = client.get(f"/jobs/{record.job_id}")

    assert response.status_code == HTTPStatus.OK
    assert json_str(response_json_object(response), "job_id") == str(record.job_id)


def test_create_job_with_minimal_ingest_options() -> None:
    """Test create job with minimal ingest options."""
    store = InMemoryJobStore()
    client = TestClient(create_app(store=store, require_proxy_auth=False))

    response = client.post(
        "/jobs",
        json={"urls": ["https://example.com/page"], "options": {"job_type": "ingest"}},
    )

    assert response.status_code == HTTPStatus.ACCEPTED
    job_id = UUID(json_str(response_json_object(response), "job_id"))
    record = store.get_job(job_id)
    assert record is not None
    assert record.job_type == "ingest"
    assert record.options == {}


def test_create_job_persists_translate_locales_option() -> None:
    """TC-252: translate_locales survives POST /jobs → job store options."""
    store = InMemoryJobStore()
    client = TestClient(create_app(store=store, require_proxy_auth=False))

    response = client.post(
        "/jobs",
        json={
            "urls": ["https://example.com/page"],
            "options": {"translate_locales": ["es"], "force": True},
        },
    )

    assert response.status_code == HTTPStatus.ACCEPTED
    job_id = UUID(json_str(response_json_object(response), "job_id"))
    record = store.get_job(job_id)
    assert record is not None
    assert record.options["translate_locales"] == ["es"]
    assert record.options["force"] is True


def test_create_job_persists_freshness_toggle_options() -> None:
    """TC-259: refresh_enabled / is_stale survive POST /jobs → job store options."""
    store = InMemoryJobStore()
    client = TestClient(create_app(store=store, require_proxy_auth=False))

    response = client.post(
        "/jobs",
        json={
            "urls": ["https://example.com/page"],
            "options": {"refresh_enabled": False, "is_stale": True},
        },
    )

    assert response.status_code == HTTPStatus.ACCEPTED
    job_id = UUID(json_str(response_json_object(response), "job_id"))
    record = store.get_job(job_id)
    assert record is not None
    assert record.options["refresh_enabled"] is False
    assert record.options["is_stale"] is True


def test_list_jobs_returns_all_jobs() -> None:
    """Test list jobs returns all jobs."""
    store = InMemoryJobStore()
    store.create_job(urls=["https://example.com/a"])
    store.create_job(urls=["https://example.com/b"], job_type="retag")
    client = TestClient(create_app(store=store, require_proxy_auth=False))

    response = client.get("/jobs")

    assert response.status_code == HTTPStatus.OK
    body = response_json_object(response)
    jobs = json_list(body, "jobs")
    assert len(jobs) == _EXPECTED_JOB_LIST_COUNT


def test_list_jobs_includes_eval_runs_from_internal_write_api() -> None:
    """Test list jobs merges eval runs with job_type=eval (TC-124, ADR-035 §3)."""
    eval_run_id = uuid4()

    class _EvalRunsClient:
        def list_eval_runs(
            self,
            *,
            page: int = 1,
            page_size: int = 100,
        ) -> EvalRunListResponse:
            _ = (page, page_size)
            return EvalRunListResponse(
                items=[
                    EvalRunListItem(
                        run_id=eval_run_id,
                        status="running",
                        started_at=datetime(2026, 7, 2, 12, 0, tzinfo=UTC),
                        metrics_summary=EvalMetricsSummary(),
                    )
                ],
                page=1,
                page_size=100,
                total_count=1,
            )

    store = InMemoryJobStore()
    store.create_job(urls=["https://example.com/a"])
    client = TestClient(
        create_app(
            store=store,
            require_proxy_auth=False,
            eval_runs_client=_EvalRunsClient(),  # type: ignore[arg-type]
        )
    )

    response = client.get("/jobs")

    assert response.status_code == HTTPStatus.OK
    jobs = json_list(response_json_object(response), "jobs")
    assert len(jobs) == _EXPECTED_JOB_LIST_COUNT
    eval_job = next(job for job in jobs if json_str(as_json_object(job), "job_type") == "eval")
    assert json_str(as_json_object(eval_job), "job_id") == str(eval_run_id)
    assert json_str(as_json_object(eval_job), "status") == "running"


def test_list_jobs_filters_by_status() -> None:
    """Test list jobs filters by status."""
    store = InMemoryJobStore()
    done = store.create_job(urls=["https://example.com/a"])
    store.update_job(done.job_id, status="completed")
    store.create_job(urls=["https://example.com/b"])
    client = TestClient(create_app(store=store, require_proxy_auth=False))

    response = client.get("/jobs", params={"status": "completed"})

    assert response.status_code == HTTPStatus.OK
    jobs = json_list(response_json_object(response), "jobs")
    assert len(jobs) == 1
    first_job = as_json_object(jobs[0])
    assert json_str(first_job, "job_id") == str(done.job_id)
    assert json_str(first_job, "status") == "completed"


def test_list_jobs_requires_proxy_key_when_auth_enabled(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test list jobs requires proxy key when auth enabled."""
    monkeypatch.setenv("VECINITA_MODAL_PROXY_KEY", _PROXY_KEY)
    client = TestClient(create_app(require_proxy_auth=True))

    response = client.get("/jobs")

    assert response.status_code == HTTPStatus.UNAUTHORIZED


def test_create_app_uses_explicit_cors_env_value() -> None:
    """Test create app uses explicit cors env value."""
    app = create_app(
        require_proxy_auth=False,
        cors_env_value="https://custom.example,https://other.example",
    )

    assert app.user_middleware


def test_create_app_uses_staging_cors_when_env_empty(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test create app uses staging cors when env empty."""
    monkeypatch.delenv("VECINITA_CORS_ORIGINS", raising=False)
    app = create_app(require_proxy_auth=False, cors_env_value=None)

    assert app.user_middleware


def test_default_audit_emit_noops_when_write_api_unconfigured(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Factory audit emit falls back to a no-op when InternalWriteClient cannot be built."""
    monkeypatch.delenv("VECINITA_INTERNAL_WRITE_URL", raising=False)
    monkeypatch.delenv("VECINITA_INTERNAL_API_KEY", raising=False)
    monkeypatch.setenv(
        "VECINITA_ADMIN_FRONTEND_URL",
        "https://vecinita-admin-frontend-ef4ob.ondigitalocean.app",
    )
    app = create_app(
        require_proxy_auth=False,
        admin_client=make_client(seed_users()),
        audit_emit=None,
    )
    with TestClient(app) as client:
        response = client.post(
            "/admin/users/invite",
            json={"email": "noop-audit@example.org", "role": "viewer"},
        )
    assert response.status_code == HTTPStatus.CREATED


def test_default_audit_emit_posts_to_write_api(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Factory audit emit delegates to InternalWriteClient.post_audit_event when configured."""
    monkeypatch.setenv("VECINITA_INTERNAL_WRITE_URL", "http://write.test")
    monkeypatch.setenv("VECINITA_INTERNAL_API_KEY", "test-key")
    monkeypatch.setenv(
        "VECINITA_ADMIN_FRONTEND_URL",
        "https://vecinita-admin-frontend-ef4ob.ondigitalocean.app",
    )
    posted: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/internal/v1/audit/event":
            posted.append(request.url.path)
            return httpx.Response(HTTPStatus.ACCEPTED, json={})
        return httpx.Response(HTTPStatus.NOT_FOUND, json={})

    transport = httpx.MockTransport(handler)
    write = InternalWriteClient(
        "http://write.test",
        api_key="test-key",
        http_client=httpx.Client(transport=transport, base_url="http://write.test"),
    )
    monkeypatch.setattr(
        "vecinita_data_management_backend.app.InternalWriteClient",
        lambda: write,
    )
    app = create_app(
        require_proxy_auth=False,
        admin_client=make_client(seed_users()),
        audit_emit=None,
    )
    with TestClient(app) as client:
        response = client.post(
            "/admin/users/invite",
            json={"email": "audit-post@example.org", "role": "viewer"},
        )
    assert response.status_code == HTTPStatus.CREATED
    assert posted == ["/internal/v1/audit/event"]
    write.close()
