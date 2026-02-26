"""Unit tests for admin router tag management functionality."""

from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

pytestmark = pytest.mark.unit


class _FakeResponse:
    def __init__(self, text: str = "", status_code: int = 200, headers: dict | None = None, json_data=None):
        self.text = text
        self.status_code = status_code
        self.headers = headers or {}
        self._json_data = json_data or {}

    def json(self):
        return self._json_data


class _FakeAsyncClient:
    def __init__(self, *args, **kwargs):
        pass

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    async def get(self, url: str, **kwargs):
        return _FakeResponse(
            text="<html><body>Housing assistance and food support information.</body></html>",
            status_code=200,
            headers={"content-type": "text/html"},
        )

    async def post(self, url: str, json=None, headers=None, **kwargs):
        texts = (json or {}).get("texts", [])
        return _FakeResponse(json_data={"embeddings": [[0.1] * 384 for _ in texts]})


@pytest.fixture
def admin_client(env_vars, monkeypatch):
    for key, value in env_vars.items():
        monkeypatch.setenv(key, value)

    from src.api.main import app
    from src.api import router_admin

    mock_db = MagicMock()
    mock_store = MagicMock()

    app.dependency_overrides[router_admin.get_database_client] = lambda: mock_db
    app.dependency_overrides[router_admin._verify_admin] = lambda: {"id": "admin-user"}
    monkeypatch.setattr(router_admin, "get_chroma_store", lambda: mock_store)

    client = TestClient(app)
    yield client, mock_db, mock_store

    app.dependency_overrides.clear()


class TestAdminTagsEndpoints:
    def test_get_metadata_tags(self, admin_client):
        client, _mock_db, mock_store = admin_client
        mock_store.iter_all_chunks.return_value = [
            {"metadata": {"tags": ["food", "housing"]}},
            {"metadata": {"tags": ["community"]}},
        ]

        response = client.get("/api/v1/admin/tags?query=ho&limit=10")

        assert response.status_code == 200
        body = response.json()
        assert body["tags"] == ["housing"]
        assert body["total"] == 1

    def test_get_metadata_tags_supports_spanish_errors(self, admin_client):
        client, _mock_db, mock_store = admin_client
        mock_store.iter_all_chunks.side_effect = RuntimeError("boom")

        response = client.get("/api/v1/admin/tags?lang=es")

        assert response.status_code == 500
        assert "No se pudieron obtener las etiquetas de metadatos" in str(response.json())

    def test_patch_source_tags_updates_chunks(self, admin_client):
        client, _mock_db, mock_store = admin_client
        mock_store.get_source.return_value = {"title": "Example", "metadata": {"tags": ["old"]}}
        mock_store.get_chunks.return_value = {
            "ids": ["chunk-1", "chunk-2"],
            "documents": ["Doc A", "Doc B"],
            "metadatas": [{"title": "A", "source_url": "https://example.com/resource"}, {"title": "B", "source_url": "https://example.com/resource"}],
        }
        mock_store.chunks.return_value.get.return_value = {
            "embeddings": [[0.1, 0.2], [0.3, 0.4]]
        }

        response = client.patch(
            "/api/v1/admin/sources/tags",
            json={"url": "https://example.com/resource", "tags": ["Housing", "food", "food"]},
        )

        assert response.status_code == 200
        body = response.json()
        assert body["status"] == "updated"
        assert body["tags"] == ["housing", "food"]
        assert body["chunks_updated"] == 2
        assert body["message"] == "Source tags updated successfully."
        mock_store.upsert_source.assert_called_once()
        mock_store.upsert_chunks.assert_called_once()

    def test_patch_source_tags_returns_spanish_message(self, admin_client):
        client, _mock_db, mock_store = admin_client
        mock_store.get_source.return_value = {"title": "Example", "metadata": {"tags": ["old"]}}
        mock_store.get_chunks.return_value = {
            "ids": ["chunk-1"],
            "documents": ["Doc A"],
            "metadatas": [{"title": "A", "source_url": "https://example.com/resource"}],
        }
        mock_store.chunks.return_value.get.return_value = {
            "embeddings": [[0.1, 0.2]]
        }

        response = client.patch(
            "/api/v1/admin/sources/tags?lang=es",
            json={"url": "https://example.com/resource", "tags": ["Housing"]},
        )

        assert response.status_code == 200
        body = response.json()
        assert body["message"] == "Las etiquetas de la fuente se actualizaron correctamente."

    def test_add_source_accepts_tags(self, admin_client):
        client, _mock_db, mock_store = admin_client
        from src.api import router_admin

        mock_store.upsert_chunks.return_value = 1

        original_client = router_admin.httpx.AsyncClient
        router_admin.httpx.AsyncClient = _FakeAsyncClient

        try:
            response = client.post(
                "/api/v1/admin/sources",
                data={"url": "https://example.com", "depth": 1, "tags": "Housing, Community"},
            )
        finally:
            router_admin.httpx.AsyncClient = original_client

        assert response.status_code == 200
        body = response.json()
        assert body["status"] == "completed"
        assert body["tags"] == ["housing", "community"]
        assert body["chunks_inserted"] == 1
        assert mock_store.upsert_source.call_count >= 2
        assert mock_store.add_queue_job.call_count >= 2
        mock_store.upsert_chunks.assert_called_once()


class TestAdminSourcesList:
    def test_list_sources_includes_tags(self, admin_client):
        client, _mock_db, mock_store = admin_client
        mock_store.list_sources.return_value = [
            {
                "url": "https://example.com",
                "title": "Example",
                "metadata": {"tags": ["Housing", "Benefits"], "source_domain": "example.com"},
            }
        ]
        mock_store.iter_all_chunks.return_value = [
            {"metadata": {"source_url": "https://example.com"}},
            {"metadata": {"source_url": "https://example.com"}},
            {"metadata": {"source_url": "https://example.com"}},
        ]

        response = client.get("/api/v1/admin/sources")

        assert response.status_code == 200
        body = response.json()
        assert body["total"] == 1
        assert body["sources"][0]["tags"] == ["housing", "benefits"]
        assert body["sources"][0]["total_chunks"] == 3

    def test_list_sources_normalizes_real_source_shape(self, admin_client):
        client, _mock_db, mock_store = admin_client
        mock_store.list_sources.return_value = [
            {
                "url": "https://www.nuestrasalud.com/blog/example",
                "title": None,
                "metadata": {
                    "domain": "www.nuestrasalud.com",
                    "source_domain": "www.nuestrasalud.com",
                    "scrape_count": 1,
                    "reliability_score": "1.00",
                    "total_characters": 4826,
                    "created_at": "2025-10-27T19:03:00.230822+00:00",
                    "updated_at": "2025-10-27T19:03:00.230822+00:00",
                },
                "created_at": "2025-10-27T19:03:00.230822+00:00",
                "updated_at": "2025-10-27T19:03:00.230822+00:00",
            }
        ]
        mock_store.iter_all_chunks.return_value = [
            {
                "content": "x" * 800,
                "metadata": {
                    "source_url": "https://www.nuestrasalud.com/blog/example",
                    "source_domain": "www.nuestrasalud.com",
                    "chunk_size": 804,
                },
            }
            for _ in range(6)
        ]

        response = client.get("/api/v1/admin/sources")

        assert response.status_code == 200
        body = response.json()
        assert body["total"] == 1
        source = body["sources"][0]
        assert source["source_domain"] == "www.nuestrasalud.com"
        assert source["domain"] == "www.nuestrasalud.com"
        assert source["total_chunks"] == 6
        assert source["chunk_count"] == 6
        assert source["total_characters"] == 4826
        assert source["scrape_count"] == 1
        assert source["reliability_score"] == "1.00"
        assert source["metadata"]["source_domain"] == "www.nuestrasalud.com"
        assert source["tags"] == []
