"""Integration contract tests aligned to docs/architecture/SERVICE_INTEGRATION_POINTS.md.

Each test maps to one documented integration point and validates the current
cross-service contract (routing, headers, env wiring, and fallback behavior).
"""

from __future__ import annotations

import importlib
import json
import sys
from pathlib import Path
from unittest.mock import Mock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.agent.tools import db_search as db_search_module
from src.agent.tools.db_search import create_db_search_tool, get_last_search_metrics
from src.services.scraper.uploader import DatabaseUploader

pytestmark = pytest.mark.integration


WORKSPACE_ROOT = Path(__file__).resolve().parents[3]


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


def test_ip01_frontend_to_gateway_contract_file_wiring() -> None:
    """IP-01: Frontend -> Gateway URL and ask/stream path contract."""
    content = (
        WORKSPACE_ROOT / "frontend" / "src" / "app" / "services" / "agentService.ts"
    ).read_text(encoding="utf-8")

    assert "VITE_GATEWAY_URL" in content
    assert "VITE_BACKEND_URL" in content
    assert "/ask/stream" in content
    assert "/api/v1" in content


def test_ip02_frontend_to_supabase_auth_contract_file_wiring() -> None:
    """IP-02: Frontend -> Supabase auth env vars and SDK client contract."""
    content = (WORKSPACE_ROOT / "frontend" / "src" / "lib" / "supabase.ts").read_text(
        encoding="utf-8"
    )

    assert "VITE_SUPABASE_URL" in content
    assert "VITE_SUPABASE_ANON_KEY" in content
    assert "createClient" in content


def test_ip03_gateway_to_agent_proxy_forwards_query_params(monkeypatch) -> None:
    """IP-03: Gateway ask endpoint proxies to Agent /ask with expected params."""
    from src.api import router_ask

    class _FakeAgentClient:
        def __init__(self) -> None:
            self.last_url: str | None = None
            self.last_params: dict | None = None
            self.last_timeout: float | None = None

        async def get(self, url: str, params=None, timeout=None):
            self.last_url = url
            self.last_params = params
            self.last_timeout = timeout
            return _JsonResponse(
                {
                    "answer": "ok",
                    "sources": [],
                    "language": "en",
                    "model": "test-model",
                }
            )

    fake_client = _FakeAgentClient()
    monkeypatch.setenv("AGENT_TIMEOUT", "42")
    monkeypatch.setattr(router_ask, "AGENT_SERVICE_URL", "http://agent-internal:8000")
    monkeypatch.setattr(router_ask, "DEMO_MODE", False)
    monkeypatch.setattr(router_ask, "_get_agent_client", lambda: fake_client)

    app = FastAPI()
    app.include_router(router_ask.router, prefix="/api/v1")
    client = TestClient(app)

    response = client.get(
        "/api/v1/ask",
        params={
            "question": "Where can I find housing help?",
            "tags": "housing,benefits",
            "tag_match_mode": "all",
            "include_untagged_fallback": "false",
            "rerank": "true",
            "rerank_top_k": "7",
        },
    )

    assert response.status_code == 200
    assert fake_client.last_url == "http://agent-internal:8000/ask"
    assert fake_client.last_params is not None
    assert fake_client.last_params["question"] == "Where can I find housing help?"
    assert fake_client.last_params["tags"] == "housing,benefits"
    assert fake_client.last_params["tag_match_mode"] == "all"
    assert fake_client.last_timeout == pytest.approx(42.0)


def test_ip04_gateway_to_embedding_service_headers_and_endpoint(monkeypatch) -> None:
    """IP-04: Gateway embedding route builds expected auth/proxy headers."""
    import src.api.router_embed as router_embed

    monkeypatch.setattr(router_embed, "EMBEDDING_SERVICE_AUTH_TOKEN", "embed-token")
    monkeypatch.setattr(router_embed, "PROXY_AUTH_TOKEN", "proxy-token")
    monkeypatch.setattr(router_embed, "MODAL_PROXY_KEY", "wk-test")
    monkeypatch.setattr(router_embed, "MODAL_PROXY_SECRET", "ws-test")

    headers = router_embed._embedding_service_headers()
    assert headers["x-embedding-service-token"] == "embed-token"
    assert headers["authorization"] == "Bearer embed-token"
    assert headers["X-Proxy-Token"] == "proxy-token"
    assert headers["Modal-Key"] == "wk-test"
    assert headers["Modal-Secret"] == "ws-test"


def test_ip05_gateway_to_reindex_route_forwards_token_and_params(monkeypatch) -> None:
    """IP-05: Gateway scrape/reindex forwards trigger token to proxy jobs endpoint."""
    from src.api import router_scrape

    captured: dict[str, object] = {}

    class _StubClient:
        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return False

        async def post(self, url: str, params=None, headers=None):
            captured["url"] = url
            captured["params"] = params
            captured["headers"] = headers
            return _JsonResponse({"status": "queued", "call_id": "call-1"})

    monkeypatch.setattr(router_scrape, "REINDEX_SERVICE_URL", "http://proxy:10000/jobs")
    monkeypatch.setattr(router_scrape, "REINDEX_TRIGGER_TOKEN", "reindex-secret")
    monkeypatch.setattr(router_scrape.httpx, "AsyncClient", lambda *args, **kwargs: _StubClient())

    app = FastAPI()
    app.include_router(router_scrape.router, prefix="/api/v1")
    client = TestClient(app)

    response = client.post("/api/v1/scrape/reindex?clean=true&verbose=true")
    assert response.status_code == 200
    assert captured["url"] == "http://proxy:10000/jobs/reindex"
    assert captured["params"] == {"clean": True, "stream": True, "verbose": True}
    assert captured["headers"] == {"x-reindex-token": "reindex-secret"}


def test_ip06_agent_to_embedding_modal_proxy_headers(monkeypatch) -> None:
    """IP-06: Agent startup wires modal-proxy embedding URL + auth token into client factory."""

    captured: dict[str, object] = {}

    def _fake_create_embedding_client(url: str, validate_on_init: bool = False, auth_token=None):
        captured["url"] = url
        captured["validate_on_init"] = validate_on_init
        captured["auth_token"] = auth_token
        return Mock(base_url=url, embed_query=Mock(return_value=[0.1] * 384))

    fake_client_module = sys.modules.get("src.embedding_service.client")
    if fake_client_module is None:
        pytest.skip("embedding service client module is unavailable in this test environment")

    monkeypatch.setattr(
        fake_client_module, "create_embedding_client", _fake_create_embedding_client
    )
    monkeypatch.setenv("RENDER", "true")
    monkeypatch.setenv("MODAL_EMBEDDING_ENDPOINT", "http://vecinita-modal-proxy-v1:10000/embedding")
    monkeypatch.delenv("EMBEDDING_SERVICE_URL", raising=False)
    monkeypatch.setenv("EMBEDDING_SERVICE_AUTH_TOKEN", "embed-token")

    import src.config as app_config

    importlib.reload(app_config)

    import src.agent.main as agent_main

    importlib.reload(agent_main)

    assert captured["url"] == "http://vecinita-modal-proxy-v1:10000/embedding"
    assert captured["validate_on_init"] is True
    assert captured["auth_token"] == "embed-token"


def test_ip07_agent_to_model_uses_proxy_fallback_on_render(monkeypatch) -> None:
    """IP-07: Agent model URL normalizes to /model proxy route on Render."""
    monkeypatch.setenv("RENDER", "true")

    import src.config as app_config

    importlib.reload(app_config)

    resolved = app_config._normalize_internal_service_url(
        "http://localhost:11434",
        fallback_url="http://vecinita-modal-proxy-v1:10000/model",
    )
    assert resolved == "http://vecinita-modal-proxy-v1:10000/model"


def test_ip08_agent_tools_postgres_fallback_when_mode_postgres(monkeypatch) -> None:
    """IP-08: Agent tools call Postgres fallback in Postgres data mode."""
    mock_store = Mock()
    mock_store.query_chunks.side_effect = RuntimeError("chroma unavailable")
    mock_embedding_model = Mock()
    mock_embedding_model.embed_query.return_value = [0.1] * 384

    monkeypatch.setenv("DB_DATA_MODE", "postgres")
    monkeypatch.setenv("DATABASE_URL", "postgresql://user:pass@localhost:5432/db")
    monkeypatch.setenv("POSTGRES_DATA_READS_ENABLED", "true")
    monkeypatch.setenv("SUPABASE_DATA_READS_ENABLED", "false")

    postgres_mock = Mock(
        return_value=[
            {
                "id": "doc-pg-1",
                "content": "postgres result",
                "source_url": "https://example.org/postgres",
                "source_domain": "example.org",
                "similarity": 0.9,
                "metadata": {},
            }
        ]
    )
    supabase_mock = Mock(return_value=[])
    monkeypatch.setattr(db_search_module, "_query_postgres_fallback", postgres_mock)
    monkeypatch.setattr(db_search_module, "_query_supabase_fallback", supabase_mock)

    import src.config as app_config

    importlib.reload(app_config)

    tool = create_db_search_tool(
        mock_store, mock_embedding_model, match_threshold=0.3, match_count=5
    )
    rows = json.loads(tool.invoke("housing"))

    assert rows[0]["source_url"] == "https://example.org/postgres"
    assert postgres_mock.called
    assert get_last_search_metrics()["retrieval_backend"] == "postgres"


def test_ip09_agent_tools_supabase_fallback_when_enabled(monkeypatch) -> None:
    """IP-09: Agent tools call Supabase RPC fallback when enabled."""
    mock_store = Mock()
    mock_store.query_chunks.side_effect = RuntimeError("chroma unavailable")
    mock_embedding_model = Mock()
    mock_embedding_model.embed_query.return_value = [0.1] * 384

    monkeypatch.setenv("DB_DATA_MODE", "supabase")
    monkeypatch.setenv("VECTOR_SYNC_SUPABASE_FALLBACK_READS", "true")

    postgres_mock = Mock(return_value=[])
    supabase_mock = Mock(
        return_value=[
            {
                "id": "doc-sb-1",
                "content": "supabase result",
                "source_url": "https://example.org/supabase",
                "source_domain": "example.org",
                "similarity": 0.89,
                "metadata": {},
            }
        ]
    )
    monkeypatch.setattr(db_search_module, "_query_postgres_fallback", postgres_mock)
    monkeypatch.setattr(db_search_module, "_query_supabase_fallback", supabase_mock)

    import src.config as app_config

    importlib.reload(app_config)

    tool = create_db_search_tool(
        mock_store, mock_embedding_model, match_threshold=0.3, match_count=5
    )
    rows = json.loads(tool.invoke("benefits"))

    assert rows[0]["source_url"] == "https://example.org/supabase"
    assert supabase_mock.called
    assert get_last_search_metrics()["retrieval_backend"] == "supabase"


def test_ip10_scraper_uploader_writes_to_chroma() -> None:
    """IP-10: Scraper uploader sends chunk rows to Chroma upsert interface."""
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

    uploaded, failed = uploader.upload_chunks(
        chunks=[{"text": "community support", "metadata": {}}],
        source_identifier="https://example.org/chroma",
        loader_type="playwright",
    )

    assert uploaded == 1
    assert failed == 0
    uploader.chroma_store.upsert_chunks.assert_called_once()


def test_ip11_scraper_uploader_switches_to_postgres_sync_target() -> None:
    """IP-11: Scraper uploader routes vector sync to Postgres when configured."""
    with (
        patch.object(DatabaseUploader, "_init_embeddings"),
        patch.object(DatabaseUploader, "_init_supabase"),
        patch.object(DatabaseUploader, "_init_local_llm_tagger"),
    ):
        uploader = DatabaseUploader(use_local_embeddings=False)

    uploader.vector_sync_target = "postgres"
    uploader._sync_rows_to_postgres = Mock(return_value=True)

    ok = uploader._sync_rows_to_supabase(
        [
            {
                "id": "row-1",
                "content": "row",
                "source_url": "https://example.org/pg",
                "embedding": [0.1] * 3,
                "metadata": {},
            }
        ]
    )

    assert ok is True
    uploader._sync_rows_to_postgres.assert_called_once()


def test_ip12_documents_router_mixed_datasource_contract(monkeypatch) -> None:
    """IP-12: Documents router keeps SQL + Supabase URL builder contract."""
    from src.api import router_documents

    monkeypatch.setenv("SUPABASE_URL", "https://demo.supabase.co")
    public_url = router_documents._build_public_storage_url("documents", "uploads/file.txt")
    assert (
        public_url == "https://demo.supabase.co/storage/v1/object/public/documents/uploads/file.txt"
    )

    normalized = router_documents._normalize_public_source(
        {
            "source_url": "https://example.org/resource",
            "metadata": {"tags": ["housing"], "download_url": "https://cdn.example.org/file.pdf"},
            "total_chunks": 3,
        }
    )
    assert normalized["downloadable"] is True
    assert normalized["download_url"] == "https://cdn.example.org/file.pdf"


def test_ip13_modal_proxy_route_and_header_contract_files() -> None:
    """IP-13: Modal proxy keeps path-strip and credential-strip contracts."""
    defaults_content = (
        WORKSPACE_ROOT / "services" / "modal-proxy" / "app" / "backends" / "defaults.py"
    ).read_text(encoding="utf-8")
    proxy_content = (WORKSPACE_ROOT / "services" / "modal-proxy" / "app" / "proxy.py").read_text(
        encoding="utf-8"
    )

    assert 'path_prefix="/model"' in defaults_content
    assert 'path_strip_prefix="/model"' in defaults_content
    assert 'path_prefix="/embedding"' in defaults_content
    assert 'path_strip_prefix="/embedding"' in defaults_content

    assert '"modal-key"' in proxy_content
    assert '"modal-secret"' in proxy_content
    assert '"x-proxy-token"' in proxy_content
