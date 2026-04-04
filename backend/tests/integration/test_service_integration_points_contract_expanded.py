"""Additional contract coverage for SERVICE_INTEGRATION_POINTS.md.

This module adds two extra checks per integration point on top of the primary
matrix suite to keep drift visible without relying on live infrastructure.
"""

from __future__ import annotations

import asyncio
import importlib
import json
import sys
from pathlib import Path
from unittest.mock import Mock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.agent.tools import db_search as db_search_module
from src.agent.tools.db_search import create_db_search_tool
from src.services.scraper.uploader import DatabaseUploader

pytestmark = pytest.mark.integration


WORKSPACE_ROOT = Path(__file__).resolve().parents[3]


def _read_workspace_file(*parts: str) -> str:
    target = WORKSPACE_ROOT.joinpath(*parts)
    if not target.exists():
        pytest.skip(f"Workspace file unavailable in this CI checkout: {target}")
    return target.read_text(encoding="utf-8")


class _JsonResponse:
    def __init__(self, payload: dict, status_code: int = 200):
        self._payload = payload
        self.status_code = status_code
        self.text = json.dumps(payload)

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            raise RuntimeError(f"HTTP {self.status_code}")

    def json(self):
        return self._payload


def test_ip01_frontend_gateway_render_helper_contract() -> None:
    content = _read_workspace_file("frontend", "src", "app", "services", "agentService.ts")
    assert "isDirectRenderAgentHost" in content
    assert "normalizeAgentApiBaseUrl" in content
    assert "resolveGatewayUrl" in content


def test_ip01_frontend_gateway_timeout_env_contract() -> None:
    content = _read_workspace_file("frontend", "src", "app", "services", "agentService.ts")
    assert "VITE_AGENT_REQUEST_TIMEOUT_MS" in content
    assert "VITE_AGENT_STREAM_TIMEOUT_MS" in content
    assert "VITE_AGENT_STREAM_FIRST_EVENT_TIMEOUT_MS" in content


def test_ip02_frontend_supabase_guard_contract() -> None:
    content = _read_workspace_file("frontend", "src", "lib", "supabase.ts")
    assert "isSupabaseConfigured" in content
    assert "supabaseConfigError" in content
    assert "VITE_DEV_ADMIN_ENABLED" in content


def test_ip02_frontend_supabase_session_persistence_contract() -> None:
    content = _read_workspace_file("frontend", "src", "lib", "supabase.ts")
    assert "autoRefreshToken: true" in content
    assert "persistSession: true" in content
    assert "detectSessionInUrl: true" in content


def test_ip03_gateway_agent_config_proxy_contract(monkeypatch) -> None:
    from src.api import router_ask

    class _FakeAgentClient:
        async def get(self, url: str, params=None, timeout=None):
            assert url.endswith("/config")
            return _JsonResponse(
                {"providers": [{"name": "ollama"}], "models": {"ollama": ["llama3.1:8b"]}}
            )

    monkeypatch.setattr(router_ask, "_get_agent_client", lambda: _FakeAgentClient())

    app = FastAPI()
    app.include_router(router_ask.router, prefix="/api/v1")
    client = TestClient(app)
    response = client.get("/api/v1/ask/config")

    assert response.status_code == 200
    assert "providers" in response.json()


def test_ip03_gateway_agent_stream_proxy_contract(monkeypatch) -> None:
    from src.api import router_ask

    class _StreamResponse:
        status_code = 200

        def raise_for_status(self) -> None:
            return None

        async def aiter_bytes(self):
            yield b'data: {"type":"thinking","message":"step"}\n\n'
            yield b'data: {"type":"complete","answer":"done","sources":[]}\n\n'

    class _StreamContext:
        async def __aenter__(self):
            return _StreamResponse()

        async def __aexit__(self, exc_type, exc, tb):
            return False

    class _FakeAgentClient:
        def stream(self, method, url, params=None, timeout=None):
            assert method == "GET"
            assert url.endswith("/ask-stream")
            return _StreamContext()

    monkeypatch.setattr(router_ask, "_get_agent_client", lambda: _FakeAgentClient())

    app = FastAPI()
    app.include_router(router_ask.router, prefix="/api/v1")
    client = TestClient(app)
    response = client.get("/api/v1/ask/stream", params={"question": "Need housing"})

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/event-stream")
    assert '"type":"complete"' in response.text


def test_ip04_gateway_embedding_url_normalization_contract(monkeypatch) -> None:
    import src.api.router_embed as router_embed

    monkeypatch.delenv("RENDER", raising=False)
    monkeypatch.delenv("RENDER_SERVICE_ID", raising=False)
    monkeypatch.setenv("LOCAL_EMBEDDING_SERVICE_URL", "http://localhost:8001")

    result = router_embed._normalize_embedding_service_url("https://remote.example.com/embed")
    assert result == "http://localhost:8001"


def test_ip04_gateway_embedding_batch_fallback_contract() -> None:
    import src.api.router_embed as router_embed

    class _StubClient:
        def __init__(self):
            self.calls: list[tuple[str, dict]] = []

        async def post(self, url, json=None, headers=None):
            self.calls.append((url, json or {}))
            if url.endswith("/embed/batch"):
                return _JsonResponse({}, status_code=404)
            return _JsonResponse({"embeddings": [[0.1, 0.2]]})

    client = _StubClient()
    response = asyncio.run(router_embed._post_batch_embedding(client, ["hello"]))

    assert response.status_code == 200
    assert client.calls[0][0].endswith("/embed/batch")
    assert client.calls[1][0].endswith("/embed-batch")


def test_ip05_gateway_reindex_missing_service_contract(monkeypatch) -> None:
    from src.api import router_scrape

    monkeypatch.setattr(router_scrape, "REINDEX_SERVICE_URL", "")
    app = FastAPI()
    app.include_router(router_scrape.router, prefix="/api/v1")
    client = TestClient(app)

    response = client.post("/api/v1/scrape/reindex")
    assert response.status_code == 503


def test_ip05_gateway_reindex_default_proxy_path_contract() -> None:
    content = (WORKSPACE_ROOT / "backend" / "src" / "api" / "router_scrape.py").read_text(
        encoding="utf-8"
    )
    assert '"https://vecinita--vecinita-scraper-api-fastapi.modal.run/jobs"' in content
    assert 'headers["x-reindex-token"]' in content


def test_ip06_agent_embedding_auth_fallback_contract(monkeypatch) -> None:
    captured: dict[str, object] = {}

    def _fake_create_embedding_client(url: str, validate_on_init: bool = False, auth_token=None):
        captured["auth_token"] = auth_token
        return Mock(base_url=url, embed_query=Mock(return_value=[0.1] * 384))

    fake_client_module = sys.modules.get("src.embedding_service.client")
    if fake_client_module is None:
        pytest.skip("embedding service client module is unavailable in this test environment")

    monkeypatch.setattr(
        fake_client_module, "create_embedding_client", _fake_create_embedding_client
    )
    monkeypatch.setenv("RENDER", "true")
    monkeypatch.setenv(
        "MODAL_EMBEDDING_ENDPOINT", "https://vecinita--vecinita-embedding-web-app.modal.run"
    )
    monkeypatch.setenv("EMBEDDING_SERVICE_AUTH_TOKEN", "")
    monkeypatch.setenv("MODAL_API_KEY", "")
    monkeypatch.setenv("MODAL_TOKEN_SECRET", "")
    monkeypatch.setenv("MODAL_API_PROXY_SECRET", "modal-secret-token")

    import src.agent.main as agent_main
    import src.config as app_config

    importlib.reload(app_config)
    importlib.reload(agent_main)

    assert captured["auth_token"] == "modal-secret-token"


def test_ip06_agent_embedding_preserves_explicit_modal_url_on_render(monkeypatch) -> None:
    monkeypatch.setenv("RENDER", "true")
    import src.config as app_config

    importlib.reload(app_config)
    result = app_config._normalize_internal_service_url(
        "https://vecinita--vecinita-embedding-web-app.modal.run",
        fallback_url="https://vecinita--vecinita-embedding-web-app.modal.run",
    )
    assert result == "https://vecinita--vecinita-embedding-web-app.modal.run"


def test_ip07_agent_model_preserves_explicit_modal_url_on_render(monkeypatch) -> None:
    monkeypatch.setenv("RENDER", "true")
    import src.config as app_config

    importlib.reload(app_config)
    result = app_config._normalize_internal_service_url(
        "https://vecinita--vecinita-model-api.modal.run",
        fallback_url="https://vecinita--vecinita-model-api.modal.run",
    )
    assert result == "https://vecinita--vecinita-model-api.modal.run"


def test_ip07_agent_model_preserves_direct_modal_when_strict_mode_enabled(monkeypatch) -> None:
    monkeypatch.setenv("RENDER", "true")
    monkeypatch.setenv("RENDER_REMOTE_INFERENCE_ONLY", "true")
    import src.config as app_config

    importlib.reload(app_config)
    result = app_config._normalize_internal_service_url(
        "https://vecinita--vecinita-model-api.modal.run",
        fallback_url="https://vecinita--vecinita-model-api.modal.run",
    )
    assert result == "https://vecinita--vecinita-model-api.modal.run"


def test_ip06_agent_embedding_preserves_direct_modal_when_strict_mode_enabled(monkeypatch) -> None:
    monkeypatch.setenv("RENDER", "true")
    monkeypatch.setenv("AGENT_ENFORCE_PROXY", "true")
    import src.config as app_config

    importlib.reload(app_config)
    result = app_config._normalize_internal_service_url(
        "https://vecinita--vecinita-embedding-web-app.modal.run",
        fallback_url="https://vecinita--vecinita-embedding-web-app.modal.run",
    )
    assert result == "https://vecinita--vecinita-embedding-web-app.modal.run"


def test_ip07_agent_model_default_direct_modal_contract(monkeypatch) -> None:
    monkeypatch.setenv("RENDER", "true")
    monkeypatch.delenv("MODAL_OLLAMA_ENDPOINT", raising=False)
    monkeypatch.delenv("OLLAMA_BASE_URL", raising=False)
    monkeypatch.delenv("VECINITA_MODEL_API_URL", raising=False)

    import src.config as app_config

    importlib.reload(app_config)
    assert app_config.OLLAMA_BASE_URL == "https://vecinita--vecinita-model-api.modal.run"


def test_ip08_agent_postgres_auto_mode_prefers_postgres_when_supabase_missing(monkeypatch) -> None:
    mock_store = Mock()
    mock_store.query_chunks.side_effect = RuntimeError("chroma unavailable")
    mock_embedding_model = Mock(embed_query=Mock(return_value=[0.1] * 384))

    postgres_mock = Mock(
        return_value=[
            {
                "id": "doc-pg-2",
                "content": "postgres auto result",
                "source_url": "https://example.org/postgres-auto",
                "source_domain": "example.org",
                "similarity": 0.9,
                "metadata": {},
            }
        ]
    )
    supabase_mock = Mock(return_value=[])

    monkeypatch.setenv("DB_DATA_MODE", "auto")
    monkeypatch.setenv("DATABASE_URL", "postgresql://user:pass@localhost:5432/db")
    monkeypatch.delenv("SUPABASE_URL", raising=False)
    monkeypatch.delenv("SUPABASE_KEY", raising=False)
    monkeypatch.setattr(db_search_module, "_query_postgres_fallback", postgres_mock)
    monkeypatch.setattr(db_search_module, "_query_supabase_fallback", supabase_mock)

    import src.config as app_config

    importlib.reload(app_config)
    tool = create_db_search_tool(
        mock_store, mock_embedding_model, match_threshold=0.3, match_count=5
    )
    result = json.loads(tool.invoke("housing"))

    assert postgres_mock.called
    assert result[0]["source_url"] == "https://example.org/postgres-auto"


def test_ip08_agent_postgres_backend_order_contract(monkeypatch) -> None:
    monkeypatch.setenv("DB_DATA_MODE", "postgres")
    import src.config as app_config

    importlib.reload(app_config)
    assert db_search_module._resolve_data_backend_order()[0] == "postgres"


def test_ip09_agent_supabase_disabled_fallback_contract(monkeypatch) -> None:
    mock_store = Mock()
    mock_store.query_chunks.side_effect = RuntimeError("chroma unavailable")
    mock_embedding_model = Mock(embed_query=Mock(return_value=[0.1] * 384))

    monkeypatch.setenv("DB_DATA_MODE", "supabase")
    monkeypatch.setenv("VECTOR_SYNC_SUPABASE_FALLBACK_READS", "false")
    tool = create_db_search_tool(
        mock_store, mock_embedding_model, match_threshold=0.3, match_count=5
    )

    assert tool.invoke("housing") == "[]"


def test_ip09_agent_supabase_legacy_rpc_signature_contract(monkeypatch) -> None:
    fresh_db_search_module = importlib.import_module("src.agent.tools.db_search")

    mock_store = Mock()
    mock_store.query_chunks.side_effect = RuntimeError("chroma unavailable")
    mock_embedding_model = Mock(embed_query=Mock(return_value=[0.1] * 384))

    rpc_chain = Mock()
    rpc_chain.execute.side_effect = [
        Exception("search_similar_documents(tag_filter) does not exist"),
        Mock(
            data=[
                {
                    "id": "doc-legacy-1",
                    "content": "Food pantry support",
                    "source_url": "https://example.org/food",
                    "source_domain": "example.org",
                    "similarity": 0.88,
                    "metadata": {},
                }
            ]
        ),
    ]
    mock_supabase = Mock()
    mock_supabase.rpc.return_value = rpc_chain

    monkeypatch.setenv("VECTOR_SYNC_SUPABASE_FALLBACK_READS", "true")
    monkeypatch.setenv("DB_DATA_MODE", "supabase")
    monkeypatch.setenv("SUPABASE_URL", "https://example.supabase.co")
    monkeypatch.setenv("SUPABASE_KEY", "test-key")
    monkeypatch.setattr(fresh_db_search_module.app_config, "DB_DATA_MODE", "supabase")
    monkeypatch.setattr(fresh_db_search_module, "_SUPABASE_CLIENT", None)
    monkeypatch.setattr(
        fresh_db_search_module,
        "create_client",
        lambda _url, _key: mock_supabase,
    )

    token = fresh_db_search_module.set_search_options(
        tags=["food"],
        tag_match_mode="all",
        include_untagged_fallback=False,
    )
    try:
        tool = fresh_db_search_module.create_db_search_tool(
            mock_store, mock_embedding_model, match_threshold=0.3, match_count=5
        )
        result = json.loads(tool.invoke("food"))
    finally:
        fresh_db_search_module.reset_search_options(token)

    assert result[0]["source_url"] == "https://example.org/food"
    assert mock_supabase.rpc.call_count == 2


def test_ip10_scraper_uploader_requires_chroma_store_contract() -> None:
    with (
        patch.object(DatabaseUploader, "_init_embeddings"),
        patch.object(DatabaseUploader, "_init_supabase"),
        patch.object(DatabaseUploader, "_init_local_llm_tagger"),
    ):
        uploader = DatabaseUploader(use_local_embeddings=False)

    uploader.chroma_store = None
    uploaded, failed = uploader.upload_chunks(
        chunks=[{"text": "community support", "metadata": {}}],
        source_identifier="https://example.org/chroma",
        loader_type="playwright",
    )

    assert uploaded == 0
    assert failed == 1


def test_ip10_scraper_uploader_source_locator_contract() -> None:
    with (
        patch.object(DatabaseUploader, "_init_embeddings"),
        patch.object(DatabaseUploader, "_init_supabase"),
        patch.object(DatabaseUploader, "_init_local_llm_tagger"),
    ):
        uploader = DatabaseUploader(use_local_embeddings=False)

    uploader.chroma_store = Mock()
    uploader.chroma_store.upsert_chunks = Mock(return_value=1)
    uploader.chroma_store.list_sources.return_value = []
    uploader.chroma_store.get_source.return_value = None
    uploader.local_llm_tagger = None
    uploader.local_llm_raw_model = None
    uploader._generate_embeddings = Mock(return_value=[[0.2] * 384])

    uploader.upload_chunks(
        chunks=[{"text": "community support", "metadata": {"document_title": "Guide"}}],
        source_identifier="https://sub.example.com/help",
        loader_type="playwright",
    )

    row = uploader.chroma_store.upsert_chunks.call_args[0][0][0]
    assert row["metadata"]["source_locator"] == "sub.example.com/help"
    assert row["document_title"] == "Guide"


def test_ip11_scraper_sync_invalid_target_defaults_to_supabase() -> None:
    with (
        patch.object(DatabaseUploader, "_init_embeddings"),
        patch.object(DatabaseUploader, "_init_supabase"),
        patch.object(DatabaseUploader, "_init_local_llm_tagger"),
        patch.dict("os.environ", {"VECTOR_SYNC_TARGET": "bogus"}, clear=False),
    ):
        uploader = DatabaseUploader(use_local_embeddings=False)

    assert uploader.vector_sync_target == "supabase"


def test_ip11_scraper_sync_supabase_upsert_contract() -> None:
    with (
        patch.object(DatabaseUploader, "_init_embeddings"),
        patch.object(DatabaseUploader, "_init_supabase"),
        patch.object(DatabaseUploader, "_init_local_llm_tagger"),
    ):
        uploader = DatabaseUploader(use_local_embeddings=False)

    table_client = Mock()
    table_client.upsert.return_value.execute.return_value = None
    uploader.supabase_client = Mock()
    uploader._supabase_table_client = Mock(return_value=table_client)
    uploader.vector_sync_target = "supabase"

    ok = uploader._sync_rows_to_supabase(
        [{"id": "row-1", "content": "row", "source_url": "https://example.org/sb", "metadata": {}}]
    )

    assert ok is True
    table_client.upsert.assert_called_once()


def test_ip12_documents_upload_storage_path_contract() -> None:
    from src.api import router_documents

    assert (
        router_documents._storage_path_from_source_url("upload://uploads/2026/02/file.txt")
        == "uploads/2026/02/file.txt"
    )
    assert router_documents._storage_path_from_source_url("https://example.org/file.txt") is None


def test_ip12_documents_download_url_url_only_contract(monkeypatch) -> None:
    from src.api import router_documents

    class _FakeCursor:
        def __init__(self):
            self._fetch_results = [
                {
                    "url": "https://example.org/article",
                    "title": "Article",
                    "metadata": {"source_url": "https://example.org/article"},
                },
                None,
            ]

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def execute(self, _query, _params=None):
            return None

        def fetchone(self):
            if self._fetch_results:
                return self._fetch_results.pop(0)
            return None

    class _FakeConnection:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def cursor(self, cursor_factory=None):
            return _FakeCursor()

    monkeypatch.setenv("DATABASE_URL", "postgresql://user:pass@localhost:5432/db")
    monkeypatch.setattr(
        router_documents.psycopg2,
        "connect",
        lambda _url: _FakeConnection(),
        raising=False,
    )

    app = FastAPI()
    app.include_router(router_documents.router, prefix="/api/v1")
    client = TestClient(app)
    response = client.get(
        "/api/v1/documents/download-url", params={"source_url": "https://example.org/article"}
    )

    assert response.status_code == 200
    assert response.json()["downloadable"] is False


def test_ip13_direct_modal_endpoint_contract() -> None:
    content = _read_workspace_file("backend", "src", "config.py")

    assert "vecinita--vecinita-model-api.modal.run" in content
    assert "vecinita--vecinita-embedding-web-app.modal.run" in content


def test_ip13_gateway_embed_headers_do_not_use_proxy_token_contract() -> None:
    content = _read_workspace_file("backend", "src", "api", "router_embed.py")

    assert '"x-embedding-service-token"' in content
    assert '"X-Proxy-Token"' not in content
