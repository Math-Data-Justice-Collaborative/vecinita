"""Unit tests for vecinita_data_management_backend.app."""

from __future__ import annotations

from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient
from tests.helpers.json_response import json_str, response_json_object
from vecinita_data_management_backend.app import create_app
from vecinita_data_management_backend.store import InMemoryJobStore

_PROXY_KEY = "unit-test-proxy-key"


def test_health_returns_ok() -> None:
    client = TestClient(create_app(require_proxy_auth=False))

    response = client.get("/health")

    assert response.status_code == 200
    assert response_json_object(response) == {"status": "ok"}


def test_create_job_requires_proxy_key_when_auth_enabled(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("VECINITA_MODAL_PROXY_KEY", _PROXY_KEY)
    client = TestClient(create_app(require_proxy_auth=True))

    response = client.post("/jobs", json={"urls": ["https://example.com/page"]})

    assert response.status_code == 401


def test_proxy_auth_not_configured_returns_503(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("VECINITA_MODAL_PROXY_KEY", raising=False)
    monkeypatch.delenv("MODAL_PROXY_KEY", raising=False)
    client = TestClient(create_app(require_proxy_auth=True))

    response = client.post(
        "/jobs",
        json={"urls": ["https://example.com/page"]},
        headers={"X-Vecinita-Proxy-Key": "any"},
    )

    assert response.status_code == 503


def test_create_job_accepts_retag_options() -> None:
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
                "chunk_size_tokens": 128,
            },
        },
    )

    assert response.status_code == 202
    job_id = UUID(json_str(response_json_object(response), "job_id"))
    record = store.get_job(job_id)
    assert record is not None
    assert record.job_type == "retag"
    assert record.options["document_id"] == str(document_id)
    assert record.options["chunk_size_tokens"] == 128


def test_create_job_schedules_pipeline_runner() -> None:
    scheduled: list[UUID] = []
    store = InMemoryJobStore()
    client = TestClient(
        create_app(
            store=store,
            require_proxy_auth=False,
            pipeline_runner=lambda job_id: scheduled.append(job_id),
        )
    )

    response = client.post("/jobs", json={"urls": ["https://example.com/page"]})

    assert response.status_code == 202
    job_id = UUID(json_str(response_json_object(response), "job_id"))
    assert scheduled == [job_id]


def test_create_job_succeeds_with_valid_proxy_key(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("VECINITA_MODAL_PROXY_KEY", _PROXY_KEY)
    client = TestClient(create_app(require_proxy_auth=True))

    response = client.post(
        "/jobs",
        json={"urls": ["https://example.com/page"]},
        headers={"X-Vecinita-Proxy-Key": _PROXY_KEY},
    )

    assert response.status_code == 202


def test_create_job_without_options_uses_defaults() -> None:
    store = InMemoryJobStore()
    client = TestClient(create_app(store=store, require_proxy_auth=False))

    response = client.post("/jobs", json={"urls": ["https://example.com/page"]})

    assert response.status_code == 202
    job_id = UUID(json_str(response_json_object(response), "job_id"))
    record = store.get_job(job_id)
    assert record is not None
    assert record.job_type == "ingest"
    assert record.options == {}


def test_get_job_returns_404_for_unknown_id() -> None:
    client = TestClient(create_app(require_proxy_auth=False))

    response = client.get(f"/jobs/{uuid4()}")

    assert response.status_code == 404


def test_get_job_returns_existing_job() -> None:
    store = InMemoryJobStore()
    record = store.create_job(urls=["https://example.com/page"])
    client = TestClient(create_app(store=store, require_proxy_auth=False))

    response = client.get(f"/jobs/{record.job_id}")

    assert response.status_code == 200
    assert json_str(response_json_object(response), "job_id") == str(record.job_id)


def test_create_job_with_minimal_ingest_options() -> None:
    store = InMemoryJobStore()
    client = TestClient(create_app(store=store, require_proxy_auth=False))

    response = client.post(
        "/jobs",
        json={"urls": ["https://example.com/page"], "options": {"job_type": "ingest"}},
    )

    assert response.status_code == 202
    job_id = UUID(json_str(response_json_object(response), "job_id"))
    record = store.get_job(job_id)
    assert record is not None
    assert record.job_type == "ingest"
    assert record.options == {}


def test_create_app_uses_explicit_cors_env_value() -> None:
    app = create_app(
        require_proxy_auth=False,
        cors_env_value="https://custom.example,https://other.example",
    )

    assert app.user_middleware


def test_create_app_uses_staging_cors_when_env_empty(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("VECINITA_CORS_ORIGINS", raising=False)
    app = create_app(require_proxy_auth=False, cors_env_value=None)

    assert app.user_middleware
