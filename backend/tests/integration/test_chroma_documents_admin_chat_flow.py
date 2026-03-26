"""Integration coverage for Chroma ingestion and source attribution flows."""

from __future__ import annotations

from typing import Any

import pytest
from fastapi.testclient import TestClient

pytestmark = pytest.mark.integration


class _FakeChromaStore:
    def __init__(self) -> None:
        self.rows: list[dict[str, Any]] = []
        self.sources: dict[str, dict[str, Any]] = {}
        self.queue: dict[str, dict[str, Any]] = {}

    def iter_all_chunks(self, batch_size: int = 500):
        yield from self.rows

    def upsert_source(
        self, *, url: str, metadata: dict, title: str | None = None, is_active: bool = True
    ):
        self.sources[url] = {
            "url": url,
            "title": title or url,
            "metadata": metadata,
            "is_active": is_active,
        }

    def upsert_chunks(self, rows: list[dict[str, Any]]) -> int:
        for row in rows:
            self.rows.append(
                {
                    "id": row.get("id"),
                    "content": row.get("content", ""),
                    "metadata": row.get("metadata", {}),
                }
            )
        return len(rows)

    def add_queue_job(self, *, job_id: str, payload: dict[str, Any]) -> None:
        self.queue[job_id] = payload


class _FakeResponse:
    def __init__(
        self,
        payload: dict[str, Any],
        status_code: int = 200,
        text: str = "",
        headers: dict[str, str] | None = None,
    ):
        self._payload = payload
        self.status_code = status_code
        self.text = text
        self.headers = headers or {}

    def json(self):
        return self._payload

    def raise_for_status(self):
        if self.status_code >= 400:
            raise RuntimeError(f"HTTP {self.status_code}")


class _FakeAsyncClient:
    def __init__(self, *args, **kwargs):
        pass

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    async def get(self, url: str, params=None, **kwargs):
        if url.endswith("/ask"):
            return _FakeResponse(
                {
                    "answer": "Answer from agent",
                    "sources": [
                        {
                            "url": "https://example.org/source-a",
                            "title": "Source A",
                            "chunk_id": "chunk-1",
                            "relevance": 0.91,
                            "excerpt": "source excerpt",
                        }
                    ],
                    "language": "en",
                    "model": "test-model",
                }
            )
        return _FakeResponse(
            {},
            text="<html><body>Community health and housing support resources.</body></html>",
            headers={"content-type": "text/html"},
        )

    async def post(self, url: str, json=None, **kwargs):
        texts = (json or {}).get("texts", [])
        return _FakeResponse({"embeddings": [[0.1] * 384 for _ in texts]})


class _FakeDB:
    pass


@pytest.fixture
def gateway_client(env_vars, monkeypatch):
    for key, value in env_vars.items():
        monkeypatch.setenv(key, value)

    from src.api.main import app

    client = TestClient(app)
    yield client


def test_documents_overview_uses_chroma_data(gateway_client, monkeypatch):
    from src.api import router_documents

    store = _FakeChromaStore()
    store.rows = [
        {
            "id": "row-1",
            "content": "Chunk one content",
            "metadata": {
                "source_url": "https://example.org/source-a",
                "source_domain": "example.org",
                "document_title": "Source A",
                "chunk_size": 17,
            },
        },
        {
            "id": "row-2",
            "content": "Chunk two content",
            "metadata": {
                "source_url": "https://example.org/source-a",
                "source_domain": "example.org",
                "document_title": "Source A",
                "chunk_size": 18,
            },
        },
    ]

    monkeypatch.setattr(router_documents, "get_chroma_store", lambda: store)

    response = gateway_client.get("/api/v1/documents/overview")
    assert response.status_code == 200
    data = response.json()
    assert data["total_chunks"] == 2
    assert data["unique_sources"] == 1
    assert data["sources"][0]["url"] == "https://example.org/source-a"


def test_admin_upload_writes_chunks_to_chroma(gateway_client, monkeypatch):
    from src.api import router_admin
    from src.api.main import app

    store = _FakeChromaStore()
    monkeypatch.setattr(router_admin, "get_chroma_store", lambda: store)
    monkeypatch.setattr(router_admin.httpx, "AsyncClient", _FakeAsyncClient)

    app.dependency_overrides[router_admin.get_database_client] = lambda: _FakeDB()
    app.dependency_overrides[router_admin._verify_admin] = lambda: {"id": "admin-user"}

    files = {
        "file": ("sample.txt", b"Housing assistance information for residents.", "text/plain"),
    }
    response = gateway_client.post(
        "/api/v1/admin/upload", files=files, data={"tags": "housing,benefits"}
    )

    app.dependency_overrides.clear()

    assert response.status_code == 200
    payload = response.json()
    assert payload["chunks_inserted"] >= 1
    assert len(store.rows) >= 1
    assert any(row.get("metadata", {}).get("source_type") == "upload" for row in store.rows)


def test_admin_add_source_ingests_url_into_chroma(gateway_client, monkeypatch):
    from src.api import router_admin
    from src.api.main import app

    store = _FakeChromaStore()
    monkeypatch.setattr(router_admin, "get_chroma_store", lambda: store)
    monkeypatch.setattr(router_admin.httpx, "AsyncClient", _FakeAsyncClient)

    app.dependency_overrides[router_admin.get_database_client] = lambda: _FakeDB()
    app.dependency_overrides[router_admin._verify_admin] = lambda: {"id": "admin-user"}

    response = gateway_client.post(
        "/api/v1/admin/sources",
        data={"url": "https://example.org/source-a", "depth": 1, "tags": "housing,benefits"},
    )

    app.dependency_overrides.clear()

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "completed"
    assert body["chunks_inserted"] >= 1
    assert "https://example.org/source-a" in store.sources
    assert len(store.rows) >= 1


def test_ask_endpoint_preserves_source_attribution(gateway_client, monkeypatch):
    from src.api import router_ask

    monkeypatch.setattr(router_ask.httpx, "AsyncClient", _FakeAsyncClient)

    response = gateway_client.get(
        "/api/v1/ask", params={"question": "Where can I find assistance?"}
    )
    assert response.status_code == 200

    data = response.json()
    assert data["answer"] == "Answer from agent"
    assert len(data["sources"]) == 1
    assert data["sources"][0]["url"] == "https://example.org/source-a"
    assert data["sources"][0]["title"] == "Source A"
