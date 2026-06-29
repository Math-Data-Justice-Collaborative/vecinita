"""T24.3 / UJ-013 / TC-051 / AC-E3: stats summary returns aggregated counts."""

from __future__ import annotations

import os
from http import HTTPStatus

import pytest
from fastapi.testclient import TestClient
from vecinita_shared_schemas.auth import reset_auth_config_for_tests

from tests.helpers.json_response import (
    response_json_object,
)

pytestmark = pytest.mark.unit

_API_KEY = "test-internal-key"


def _database_url() -> str:
    """Return the configured database URL, falling back to the local default."""
    return os.environ.get(
        "DATABASE_URL",
        "postgresql+psycopg://vecinita:vecinita@localhost:5432/vecinita",
    )


@pytest.fixture
def client(monkeypatch: pytest.MonkeyPatch) -> TestClient:
    """Provide a TestClient for the internal write API with env configured."""
    monkeypatch.setenv("DATABASE_URL", _database_url())
    monkeypatch.setenv("VECINITA_INTERNAL_API_KEY", _API_KEY)
    monkeypatch.setenv("SUPABASE_URL", "https://test.supabase.co")
    monkeypatch.setenv("VECINITA_AUTH_REQUIRED", "true")
    reset_auth_config_for_tests()
    from vecinita_internal_write_api.app import (  # noqa: PLC0415
        create_app,
    )

    return TestClient(create_app())


def _auth() -> dict[str, str]:
    """Return the bearer auth header for the internal API key."""
    return {"Authorization": f"Bearer {_API_KEY}"}


def test_stats_summary_returns_counts(client: TestClient) -> None:
    """Stats summary returns integer document and chunk totals."""
    resp = client.get("/internal/v1/stats/summary", headers=_auth())
    assert resp.status_code == HTTPStatus.OK
    data = response_json_object(resp)
    assert "total_documents" in data
    assert "total_chunks" in data
    assert isinstance(data["total_documents"], int)
    assert isinstance(data["total_chunks"], int)


def test_stats_summary_includes_tag_distribution(client: TestClient) -> None:
    """Stats summary includes a tag distribution list."""
    resp = client.get("/internal/v1/stats/summary", headers=_auth())
    data = response_json_object(resp)
    assert "tag_distribution" in data
    assert isinstance(data["tag_distribution"], list)


def test_stats_summary_includes_language_breakdown(client: TestClient) -> None:
    """Stats summary includes a language breakdown mapping."""
    resp = client.get("/internal/v1/stats/summary", headers=_auth())
    data = response_json_object(resp)
    assert "language_breakdown" in data
    assert isinstance(data["language_breakdown"], dict)


def test_stats_summary_includes_recent_activity(client: TestClient) -> None:
    """Stats summary includes a recent activity list."""
    resp = client.get("/internal/v1/stats/summary", headers=_auth())
    data = response_json_object(resp)
    assert "recent_activity" in data
    assert isinstance(data["recent_activity"], list)


def test_stats_summary_includes_top_served(client: TestClient) -> None:
    """Stats summary includes a top-served list."""
    resp = client.get("/internal/v1/stats/summary", headers=_auth())
    data = response_json_object(resp)
    assert "top_served" in data
    assert isinstance(data["top_served"], list)
