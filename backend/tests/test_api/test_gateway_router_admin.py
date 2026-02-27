"""Unit tests for admin router tag management functionality."""

import sys
import types
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

pytestmark = pytest.mark.unit


if "supabase" not in sys.modules:
    fake_supabase = types.ModuleType("supabase")

    class _FakeClient:
        pass

    def _fake_create_client(*_args, **_kwargs):
        return MagicMock()

    fake_supabase.Client = _FakeClient
    fake_supabase.create_client = _fake_create_client
    sys.modules["supabase"] = fake_supabase


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


class _FakeEmbeddingVector:
    def __init__(self, values):
        self._values = values

    def __bool__(self):
        raise ValueError("The truth value of an array with more than one element is ambiguous")

    def tolist(self):
        return list(self._values)


class _FakeEmbeddingsPayload:
    def __init__(self, vectors):
        self._vectors = vectors

    def __bool__(self):
        raise ValueError("The truth value of an array with more than one element is ambiguous")

    def __iter__(self):
        return iter(self._vectors)


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
    def test_admin_health_includes_vector_store_diagnostics(self, admin_client, monkeypatch):
        client, mock_db, mock_store = admin_client
        from src.api import router_admin

        mock_db.table.return_value.select.return_value.limit.return_value.execute.return_value = MagicMock(data=[{"id": "chunk-1"}])
        mock_store.heartbeat.return_value = True
        monkeypatch.setenv("VECTOR_SYNC_ENABLED", "true")
        monkeypatch.setenv("VECTOR_SYNC_SUPABASE_FALLBACK_READS", "true")

        original_client = router_admin.httpx.AsyncClient
        router_admin.httpx.AsyncClient = _FakeAsyncClient

        try:
            response = client.get("/api/v1/admin/health")
        finally:
            router_admin.httpx.AsyncClient = original_client

        assert response.status_code == 200
        body = response.json()
        vector_store = body["database"]["vector_store"]
        assert vector_store["primary"] == "chroma"
        assert vector_store["sync_mode"] == "dual_write_degraded"
        assert vector_store["supabase_dual_write_enabled"] is True
        assert vector_store["supabase_fallback_reads_enabled"] is True
        assert vector_store["chroma"]["status"] == "ok"

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

    def test_patch_source_tags_handles_array_like_embeddings(self, admin_client):
        client, _mock_db, mock_store = admin_client
        mock_store.get_source.return_value = {"title": "Example", "metadata": {"tags": ["old"]}}
        mock_store.get_chunks.return_value = {
            "ids": ["chunk-1"],
            "documents": ["Doc A"],
            "metadatas": [{"title": "A", "source_url": "https://example.com/resource"}],
        }
        mock_store.chunks.return_value.get.return_value = {
            "embeddings": [_FakeEmbeddingVector([0.1, 0.2])]
        }

        response = client.patch(
            "/api/v1/admin/sources/tags",
            json={"url": "https://example.com/resource", "tags": ["Housing"]},
        )

        assert response.status_code == 200
        assert response.json()["status"] == "updated"
        upsert_rows = mock_store.upsert_chunks.call_args.args[0]
        assert upsert_rows[0]["embedding"] == [0.1, 0.2]

    def test_patch_source_tags_handles_array_like_embeddings_payload(self, admin_client):
        client, _mock_db, mock_store = admin_client
        mock_store.get_source.return_value = {"title": "Example", "metadata": {"tags": ["old"]}}
        mock_store.get_chunks.return_value = {
            "ids": ["chunk-1"],
            "documents": ["Doc A"],
            "metadatas": [{"title": "A", "source_url": "https://example.com/resource"}],
        }
        mock_store.chunks.return_value.get.return_value = {
            "embeddings": _FakeEmbeddingsPayload([_FakeEmbeddingVector([0.1, 0.2])])
        }

        response = client.patch(
            "/api/v1/admin/sources/tags",
            json={"url": "https://example.com/resource", "tags": ["Housing"]},
        )

        assert response.status_code == 200
        assert response.json()["status"] == "updated"
        upsert_rows = mock_store.upsert_chunks.call_args.args[0]
        assert upsert_rows[0]["embedding"] == [0.1, 0.2]

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

    def test_add_source_retries_via_scraper_loader_on_blocked_fetch(self, admin_client, monkeypatch):
        client, _mock_db, mock_store = admin_client
        from src.api import router_admin

        async def _blocked_fetch(_url: str):
            raise router_admin.HTTPException(status_code=502, detail="Source returned HTTP 403")

        async def _fallback_ingest(_url: str, _depth: int):
            return {
                "chunks_total": 3,
                "chunks_inserted": 3,
                "ingestion_path": "scraper_loader_fallback",
            }

        monkeypatch.setattr(router_admin, "_extract_text_from_url", _blocked_fetch)
        monkeypatch.setattr(router_admin, "_ingest_source_via_scraper_loader", _fallback_ingest)

        response = client.post(
            "/api/v1/admin/sources",
            data={"url": "https://blocked.example.com", "depth": 1, "tags": "Housing"},
        )

        assert response.status_code == 200
        body = response.json()
        assert body["status"] == "completed"
        assert body["chunks_total"] == 3
        assert body["chunks_inserted"] == 3
        assert mock_store.add_queue_job.call_count >= 2

    def test_add_sources_batch_retries_via_scraper_loader_on_blocked_fetch(self, admin_client, monkeypatch):
        client, _mock_db, _mock_store = admin_client
        from src.api import router_admin

        async def _fake_ingest(url: str, depth: int, normalized_tags: list[str]):
            if "blocked" in url:
                return {
                    "status": "completed",
                    "url": url,
                    "depth": depth,
                    "tags": normalized_tags,
                    "chunks_inserted": 2,
                    "chunks_total": 2,
                    "job_id": "job-blocked",
                }
            return {
                "status": "completed",
                "url": url,
                "depth": depth,
                "tags": normalized_tags,
                "chunks_inserted": 1,
                "chunks_total": 1,
                "job_id": "job-1",
            }

        monkeypatch.setattr(router_admin, "_ingest_source_url", _fake_ingest)

        response = client.post(
            "/api/v1/admin/sources/batch",
            json={
                "urls": ["https://ok.example.com", "https://blocked.example.com"],
                "depth": 1,
                "tags": ["housing"],
                "tag_mode": "auto_infer",
            },
        )

        assert response.status_code == 200
        body = response.json()
        assert body["status"] == "completed"
        assert body["submitted"] == 2
        assert body["completed"] == 2
        assert body["failed"] == 0

    def test_add_sources_batch_parses_urls_and_returns_partial(self, admin_client, monkeypatch):
        client, _mock_db, _mock_store = admin_client
        from src.api import router_admin

        async def _fake_ingest(url: str, depth: int, normalized_tags: list[str]):
            if url.endswith("/bad"):
                raise router_admin.HTTPException(status_code=422, detail="unprocessable")
            return {
                "status": "completed",
                "url": url,
                "depth": depth,
                "tags": normalized_tags,
                "chunks_inserted": 1,
                "chunks_total": 1,
                "job_id": "job-1",
            }

        monkeypatch.setattr(router_admin, "_ingest_source_url", _fake_ingest)

        response = client.post(
            "/api/v1/admin/sources/batch",
            json={
                "urls_text": "# comment\nhttps://example.com/good\nhttps://example.com/bad",
                "depth": 2,
                "tags": ["Housing", "food"],
                "tag_mode": "auto_infer",
            },
        )

        assert response.status_code == 200
        body = response.json()
        assert body["status"] == "partial"
        assert body["submitted"] == 2
        assert body["completed"] == 1
        assert body["failed"] == 1
        assert body["baseline_tags"] == ["housing", "food"]
        assert body["tag_mode"] == "auto_infer"

    def test_add_sources_batch_rejects_empty_payload(self, admin_client):
        client, _mock_db, _mock_store = admin_client

        response = client.post(
            "/api/v1/admin/sources/batch",
            json={"urls_text": "\n\n", "depth": 1, "tags": [], "tag_mode": "auto_infer"},
        )

        assert response.status_code == 400
        assert "Provide at least one URL" in str(response.json())


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
