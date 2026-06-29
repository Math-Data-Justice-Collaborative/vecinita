"""BUG-2026-05-22: Admin POST /jobs 401 — reserved Modal-Key header + app auth.

Modal reserves Modal-Key for workspace proxy tokens; app uses X-Vecinita-Proxy-Key.
These tests encode FastAPI proxy auth with the non-reserved header name.
"""

from __future__ import annotations

from http import HTTPStatus

import pytest
from fastapi.testclient import TestClient
from vecinita_data_management_backend.app import create_app
from vecinita_data_management_backend.store import InMemoryJobStore
from vecinita_shared_schemas.auth import reset_auth_config_for_tests

_EXPECTED_KEY = "staging-proxy-key-for-repro"


@pytest.fixture
def proxy_key_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Proxy key env."""
    reset_auth_config_for_tests()
    monkeypatch.setenv("VECINITA_MODAL_PROXY_KEY", _EXPECTED_KEY)
    monkeypatch.setenv("VECINITA_AUTH_REQUIRED", "false")


@pytest.mark.usefixtures("proxy_key_env")
def test_create_job_with_wrong_modal_key_returns_401() -> None:
    """Matches production 401 when frontend key drifts from Modal secret."""
    app = create_app(store=InMemoryJobStore(), require_proxy_auth=True)
    client = TestClient(app)

    response = client.post(
        "/jobs",
        json={"urls": ["https://vecina.wrwc.org/"], "options": {"chunk_size_tokens": 256}},
        headers={"X-Vecinita-Proxy-Key": "wrong-key-not-matching-modal-secret"},
    )
    assert response.status_code == HTTPStatus.UNAUTHORIZED
    assert response.json() == {"detail": "Unauthorized"}


@pytest.mark.usefixtures("proxy_key_env")
def test_legacy_modal_key_header_is_not_accepted() -> None:
    """Modal-Key carries workspace proxy credentials; custom keys must use X-Vecinita-Proxy-Key."""
    app = create_app(store=InMemoryJobStore(), require_proxy_auth=True)
    client = TestClient(app)
    response = client.post(
        "/jobs",
        json={"urls": ["https://vecina.wrwc.org/"]},
        headers={"Modal-Key": _EXPECTED_KEY},
    )
    assert response.status_code == HTTPStatus.UNAUTHORIZED


@pytest.mark.usefixtures("proxy_key_env")
def test_create_job_with_lowercase_proxy_header_succeeds_when_value_matches() -> None:
    """HTTP headers are case-insensitive; lowercase alias must still authenticate."""
    app = create_app(store=InMemoryJobStore(), require_proxy_auth=True)
    client = TestClient(app)

    response = client.post(
        "/jobs",
        json={"urls": ["https://vecina.wrwc.org/"], "options": {"chunk_size_tokens": 256}},
        headers={"x-vecinita-proxy-key": _EXPECTED_KEY},
    )
    assert response.status_code == HTTPStatus.ACCEPTED, response.text
    assert "job_id" in response.json()
