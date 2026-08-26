"""BUG-2026-08-26: Refresh now skip_disabled — write API internal key rejected on POST /jobs.

Write-API ``enqueue_freshness_refresh`` forwards ``Authorization: Bearer {VECINITA_INTERNAL_API_KEY}``.
Modal DM ``write_auth_dep`` used ``require_admin`` (JWT only), so enqueue raised 401 and
``freshness_crud`` surfaced ``skip_disabled``.
"""

from __future__ import annotations

from http import HTTPStatus

import pytest
from fastapi.testclient import TestClient
from vecinita_data_management_backend.app import create_app
from vecinita_data_management_backend.store import InMemoryJobStore
from vecinita_shared_schemas.auth import reset_auth_config_for_tests
from vecinita_shared_schemas.data_management import CreateJobResponse

_PROXY = "staging-proxy-key"
_SERVICE_KEY = "internal-write-service-key"
_DOC_ID = "99263b22-7950-4ee4-8c0e-e6176e73308c"


@pytest.fixture
def auth_required_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Production-like auth: JWT required, internal API key accepted for service writes."""
    reset_auth_config_for_tests()
    monkeypatch.setenv("VECINITA_MODAL_PROXY_KEY", _PROXY)
    monkeypatch.setenv("VECINITA_INTERNAL_API_KEY", _SERVICE_KEY)
    monkeypatch.setenv("VECINITA_AUTH_REQUIRED", "true")


@pytest.mark.usefixtures("auth_required_env")
def test_create_freshness_job_accepts_internal_api_key_and_proxy() -> None:
    """TC-259 / F79: write-API service key must enqueue freshness_refresh on Modal DM."""
    app = create_app(store=InMemoryJobStore(), require_proxy_auth=True)
    client = TestClient(app)

    response = client.post(
        "/jobs",
        json={
            "urls": [],
            "options": {
                "job_type": "freshness_refresh",
                "document_id": _DOC_ID,
                "force": True,
                "refresh_enabled": True,
                "is_stale": True,
            },
        },
        headers={
            "X-Vecinita-Proxy-Key": _PROXY,
            "Authorization": f"Bearer {_SERVICE_KEY}",
        },
    )

    assert response.status_code == HTTPStatus.ACCEPTED, response.text
    body = CreateJobResponse.model_validate(response.json())
    assert body.status == "pending"
    assert body.job_id
