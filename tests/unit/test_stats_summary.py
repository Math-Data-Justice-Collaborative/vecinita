"""T24.3 / UJ-013 / TC-051 / AC-E3: stats summary returns aggregated counts."""

from __future__ import annotations

import os

import pytest
from fastapi.testclient import TestClient
from tests.helpers.json_response import response_json_object

pytestmark = pytest.mark.unit

_API_KEY = "test-internal-key"


def _database_url() -> str:
    return os.environ.get(
        "DATABASE_URL",
        "postgresql+psycopg://vecinita:vecinita@localhost:5432/vecinita",
    )


@pytest.fixture()
def client():
    os.environ["DATABASE_URL"] = _database_url()
    os.environ["VECINITA_INTERNAL_API_KEY"] = _API_KEY
    from vecinita_internal_write_api.app import create_app

    return TestClient(create_app())


def _auth() -> dict[str, str]:
    return {"Authorization": f"Bearer {_API_KEY}"}


def test_stats_summary_returns_counts(client) -> None:
    resp = client.get("/internal/v1/stats/summary", headers=_auth())
    assert resp.status_code == 200
    data = response_json_object(resp)
    assert "total_documents" in data
    assert "total_chunks" in data
    assert isinstance(data["total_documents"], int)
    assert isinstance(data["total_chunks"], int)


def test_stats_summary_includes_tag_distribution(client) -> None:
    resp = client.get("/internal/v1/stats/summary", headers=_auth())
    data = response_json_object(resp)
    assert "tag_distribution" in data
    assert isinstance(data["tag_distribution"], list)


def test_stats_summary_includes_language_breakdown(client) -> None:
    resp = client.get("/internal/v1/stats/summary", headers=_auth())
    data = response_json_object(resp)
    assert "language_breakdown" in data
    assert isinstance(data["language_breakdown"], dict)


def test_stats_summary_includes_recent_activity(client) -> None:
    resp = client.get("/internal/v1/stats/summary", headers=_auth())
    data = response_json_object(resp)
    assert "recent_activity" in data
    assert isinstance(data["recent_activity"], list)


def test_stats_summary_includes_top_served(client) -> None:
    resp = client.get("/internal/v1/stats/summary", headers=_auth())
    data = response_json_object(resp)
    assert "top_served" in data
    assert isinstance(data["top_served"], list)
