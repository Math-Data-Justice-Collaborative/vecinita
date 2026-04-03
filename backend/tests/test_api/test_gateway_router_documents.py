"""Unit tests for public documents router endpoints (Postgres-backed)."""

import pytest
from fastapi.testclient import TestClient

pytestmark = pytest.mark.unit


@pytest.fixture
def documents_client(monkeypatch, env_vars):
    for key, value in env_vars.items():
        monkeypatch.setenv(key, value)
    monkeypatch.setenv("DATABASE_URL", "postgresql://test:test@localhost:5432/test")

    from src.api.main import app

    client = TestClient(app)
    return client


class _FakeCursor:
    def __init__(self, scripted_results):
        self._scripted_results = list(scripted_results)
        self._current = []

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def execute(self, _query, _params=None):
        self._current = self._scripted_results.pop(0) if self._scripted_results else []

    def fetchone(self):
        return self._current[0] if self._current else None

    def fetchall(self):
        return self._current


class _FakeConnection:
    def __init__(self, scripted_results):
        self._scripted_results = list(scripted_results)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def cursor(self, cursor_factory=None):  # noqa: ARG002
        return _FakeCursor(self._scripted_results)


def test_documents_overview_aggregates_sources(documents_client):
    client = documents_client

    from src.api import router_documents

    stats = {"total_chunks": 2, "avg_chunk_size": 150}
    sources = [
        {"url": "https://a.example.org", "domain": "a.example.org", "total_chunks": 1},
        {"url": "https://b.example.org", "domain": "b.example.org", "total_chunks": 1},
    ]
    router_documents._load_overview_via_sql = lambda: (stats, sources)

    response = client.get("/api/v1/documents/overview")
    assert response.status_code == 200
    payload = response.json()
    assert payload["total_chunks"] == 2
    assert payload["unique_sources"] == 2
    assert payload["avg_chunk_size"] == 150


def test_documents_overview_filters_by_tags(documents_client):
    client = documents_client

    from src.api import router_documents

    stats = {"total_chunks": 2, "avg_chunk_size": 150}
    sources = [
        {
            "url": "https://a.example.org",
            "domain": "a.example.org",
            "total_chunks": 1,
            "tags": ["housing", "benefits"],
        },
        {
            "url": "https://b.example.org",
            "domain": "b.example.org",
            "total_chunks": 1,
            "tags": ["education"],
        },
    ]
    router_documents._load_overview_via_sql = lambda: (stats, sources)

    response = client.get(
        "/api/v1/documents/overview",
        params={"tags": "housing,education", "tag_match_mode": "all"},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["filtered"] is True
    assert payload["unique_sources"] == 0

    response_any = client.get(
        "/api/v1/documents/overview",
        params={"tags": "housing,education", "tag_match_mode": "any"},
    )
    assert response_any.status_code == 200
    payload_any = response_any.json()
    assert payload_any["unique_sources"] == 2


def test_documents_preview_reads_chunks_from_source(documents_client):
    client = documents_client

    from src.api import router_documents

    rows = [
        {
            "chunk_index": 0,
            "chunk_size": 20,
            "content": "Some preview content",
            "metadata": {"document_title": "Doc", "source_url": "https://x"},
        }
    ]
    router_documents.psycopg2.connect = lambda _url: _FakeConnection([rows])

    response = client.get(
        "/api/v1/documents/preview", params={"source_url": "https://x", "limit": 3}
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["source_url"] == "https://x"
    assert len(payload["chunks"]) == 1
    assert payload["chunks"][0]["document_title"] == "Doc"


def test_chunk_statistics_from_database(documents_client):
    client = documents_client

    from src.api import router_documents

    router_documents._load_chunk_statistics_via_sql = lambda _limit: [
        {
            "source_domain": "foo.org",
            "chunk_count": 2,
            "avg_chunk_size": 15,
        }
    ]

    response = client.get("/api/v1/documents/chunk-statistics", params={"limit": 8})
    assert response.status_code == 200
    payload = response.json()
    assert payload["total"] == 1
    assert payload["rows"][0]["source_domain"] == "foo.org"
    assert payload["rows"][0]["chunk_count"] == 2


def test_documents_download_url_returns_non_error_for_url_only_sources(documents_client):
    client = documents_client

    from src.api import router_documents

    source_row = {
        "url": "https://example.org/article",
        "title": "Example Article",
        "metadata": {"source_url": "https://example.org/article"},
    }
    router_documents.psycopg2.connect = lambda _url: _FakeConnection([[source_row]])

    response = client.get(
        "/api/v1/documents/download-url",
        params={"source_url": "https://example.org/article"},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["downloadable"] is False
    assert payload["download_url"] is None


def test_documents_download_url_resolves_upload_source_without_explicit_download_url(
    documents_client,
):
    client = documents_client

    from src.api import router_documents

    source_row = {
        "url": "upload://uploads/2026/02/26/file.txt",
        "title": "file.txt",
        "metadata": {
            "source_url": "upload://uploads/2026/02/26/file.txt",
            "download_url": "https://example.supabase.co/storage/v1/object/public/documents/uploads/2026/02/26/file.txt",
        },
    }
    router_documents.psycopg2.connect = lambda _url: _FakeConnection([[source_row]])

    response = client.get(
        "/api/v1/documents/download-url",
        params={"source_url": "upload://uploads/2026/02/26/file.txt"},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["downloadable"] is True
    assert payload["download_url"] is not None


def test_documents_overview_excludes_test_artifacts_by_default(documents_client):
    client = documents_client

    from src.api import router_documents

    stats = {"total_chunks": 2, "avg_chunk_size": 60}
    sources = [
        {
            "url": "https://community.example.org/resource",
            "domain": "community.example.org",
            "total_chunks": 1,
            "tags": ["housing"],
        },
        {
            "url": "upload://uploads/2026/02/26/community-resource-click.txt",
            "domain": "upload",
            "total_chunks": 1,
            "tags": ["e2e"],
        },
    ]
    router_documents._load_overview_via_sql = lambda: (stats, sources)

    response = client.get("/api/v1/documents/overview")
    assert response.status_code == 200
    payload = response.json()
    assert payload["unique_sources"] == 1

    response_with_test = client.get(
        "/api/v1/documents/overview", params={"include_test_data": "true"}
    )
    assert response_with_test.status_code == 200
    payload_with_test = response_with_test.json()
    assert payload_with_test["unique_sources"] == 2


def test_documents_tags_returns_counts(documents_client):
    client = documents_client

    from src.api import router_documents

    rows = [
        {
            "source_url": "https://a.example.org",
            "metadata": {"source_url": "https://a.example.org", "tags": ["housing", "benefits"]},
        },
        {
            "source_url": "https://a.example.org",
            "metadata": {"source_url": "https://a.example.org", "tags": ["housing"]},
        },
        {
            "source_url": "https://b.example.org",
            "metadata": {"source_url": "https://b.example.org", "tags": ["housing"]},
        },
    ]
    router_documents.psycopg2.connect = lambda _url: _FakeConnection([rows])

    response = client.get("/api/v1/documents/tags", params={"limit": 10})
    assert response.status_code == 200
    payload = response.json()
    assert payload["total"] >= 1
    assert payload["tags"][0]["tag"] == "housing"
    assert payload["tags"][0]["chunk_count"] == 3
    assert payload["tags"][0]["source_count"] == 2


def test_documents_tags_returns_503_when_database_unavailable(documents_client):
    client = documents_client

    from src.api import router_documents

    def _raise_connect_error(_url):
        raise RuntimeError("could not connect to server")

    router_documents.psycopg2.connect = _raise_connect_error

    response = client.get("/api/v1/documents/tags", params={"limit": 10})
    assert response.status_code == 503
    payload = response.json()
    assert "Document index is temporarily unavailable" in payload["error"]
