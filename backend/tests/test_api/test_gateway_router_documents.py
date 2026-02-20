"""Unit tests for public documents router endpoints (Chroma-backed)."""

from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

pytestmark = pytest.mark.unit


@pytest.fixture
def documents_client(monkeypatch, env_vars):
    for key, value in env_vars.items():
        monkeypatch.setenv(key, value)

    from src.api.main import app
    from src.api import router_documents

    mock_store = MagicMock()
    monkeypatch.setattr(router_documents, "get_chroma_store", lambda: mock_store)

    client = TestClient(app)
    return client, mock_store


def test_documents_overview_aggregates_sources(documents_client):
    client, mock_store = documents_client

    mock_store.iter_all_chunks.return_value = [
        {
            "id": "1",
            "content": "alpha",
            "metadata": {
                "source_url": "https://a.example.org",
                "source_domain": "a.example.org",
                "chunk_size": 100,
                "document_title": "A",
            },
        },
        {
            "id": "2",
            "content": "beta",
            "metadata": {
                "source_url": "https://b.example.org",
                "source_domain": "b.example.org",
                "chunk_size": 200,
                "document_title": "B",
            },
        },
    ]

    response = client.get("/api/v1/documents/overview")
    assert response.status_code == 200
    payload = response.json()
    assert payload["total_chunks"] == 2
    assert payload["unique_sources"] == 2
    assert payload["avg_chunk_size"] == 150


def test_documents_overview_filters_by_tags(documents_client):
    client, mock_store = documents_client

    mock_store.iter_all_chunks.return_value = [
        {
            "id": "1",
            "content": "alpha",
            "metadata": {
                "source_url": "https://a.example.org",
                "source_domain": "a.example.org",
                "chunk_size": 100,
                "document_title": "A",
                "tags": ["housing", "benefits"],
            },
        },
        {
            "id": "2",
            "content": "beta",
            "metadata": {
                "source_url": "https://b.example.org",
                "source_domain": "b.example.org",
                "chunk_size": 200,
                "document_title": "B",
                "tags": ["education"],
            },
        },
    ]

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
    client, mock_store = documents_client

    mock_store.get_chunks.return_value = {
        "ids": ["1"],
        "documents": ["Some preview content"],
        "metadatas": [{"chunk_index": 0, "chunk_size": 20, "document_title": "Doc", "source_url": "https://x"}],
    }

    response = client.get("/api/v1/documents/preview", params={"source_url": "https://x", "limit": 3})
    assert response.status_code == 200
    payload = response.json()
    assert payload["source_url"] == "https://x"
    assert len(payload["chunks"]) == 1
    assert payload["chunks"][0]["document_title"] == "Doc"


def test_chunk_statistics_from_chroma_metadata(documents_client):
    client, mock_store = documents_client

    mock_store.iter_all_chunks.return_value = [
        {"id": "1", "content": "abc", "metadata": {"source_domain": "foo.org", "source_url": "https://foo.org/a", "chunk_size": 10}},
        {"id": "2", "content": "xyz", "metadata": {"source_domain": "foo.org", "source_url": "https://foo.org/b", "chunk_size": 20}},
    ]

    response = client.get("/api/v1/documents/chunk-statistics", params={"limit": 8})
    assert response.status_code == 200
    payload = response.json()
    assert payload["total"] == 1
    assert payload["rows"][0]["source_domain"] == "foo.org"
    assert payload["rows"][0]["chunk_count"] == 2


def test_documents_download_url_returns_non_error_for_url_only_sources(documents_client):
    client, mock_store = documents_client

    mock_store.get_source.return_value = {
        "id": "https://example.org/article",
        "title": "Example Article",
        "metadata": {"source_url": "https://example.org/article"},
    }

    response = client.get(
        "/api/v1/documents/download-url",
        params={"source_url": "https://example.org/article"},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["downloadable"] is False
    assert payload["download_url"] is None


def test_documents_tags_returns_counts(documents_client):
    client, mock_store = documents_client

    mock_store.iter_all_chunks.return_value = [
        {
            "id": "1",
            "content": "alpha",
            "metadata": {
                "source_url": "https://a.example.org",
                "tags": ["housing", "benefits"],
            },
        },
        {
            "id": "2",
            "content": "beta",
            "metadata": {
                "source_url": "https://a.example.org",
                "tags": ["housing"],
            },
        },
        {
            "id": "3",
            "content": "gamma",
            "metadata": {
                "source_url": "https://b.example.org",
                "tags": ["housing"],
            },
        },
    ]

    response = client.get("/api/v1/documents/tags", params={"limit": 10})
    assert response.status_code == 200
    payload = response.json()
    assert payload["total"] >= 1
    assert payload["tags"][0]["tag"] == "housing"
    assert payload["tags"][0]["chunk_count"] == 3
    assert payload["tags"][0]["source_count"] == 2
