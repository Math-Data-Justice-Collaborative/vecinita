"""Integration contract tests aligned to docs/architecture/SERVICE_INTEGRATION_POINTS.md.

Each test maps to one documented integration point and validates the current
cross-service contract (routing, headers, env wiring, and fallback behavior).
"""

from __future__ import annotations

import importlib
import json
import sys
from pathlib import Path
from typing import Any
from unittest.mock import Mock, patch

import httpx
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.agent.tools import db_search as db_search_module
from src.agent.tools.db_search import create_db_search_tool, get_last_search_metrics
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


def test_ip01_frontend_to_gateway_contract_file_wiring() -> None:
    """IP-01: Frontend -> Gateway URL and ask/stream path contract."""
    content = _read_workspace_file("frontend", "src", "app", "services", "agentService.ts")

    assert "VITE_GATEWAY_URL" in content
    assert "VITE_BACKEND_URL" in content
    assert "/ask/stream" in content
    assert "/api/v1" in content


def test_ip02_frontend_to_direct_admin_auth_contract_file_wiring() -> None:
    """IP-02: Frontend -> direct admin auth env vars and session storage contract."""
    content = _read_workspace_file("frontend", "src", "app", "context", "AuthContext.tsx")

    assert "VITE_ADMIN_AUTH_ENABLED" in content
    assert "vecinita-admin-session" in content
    assert "direct-admin" in content


def test_ip03_gateway_to_agent_forwards_query_params(monkeypatch) -> None:
    """IP-03: Gateway ask endpoint forwards to Agent /ask with expected params."""
    from src.api import router_ask

    class _FakeAgentClient:
        def __init__(self) -> None:
            self.last_url: str | None = None
            self.last_params: dict | None = None
            self.last_timeout: Any = None

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
    t = fake_client.last_timeout
    assert isinstance(t, httpx.Timeout)
    assert t.read == pytest.approx(42.0)
    assert t.write == pytest.approx(42.0)


def test_ip04_gateway_to_embedding_service_headers_and_endpoint(monkeypatch) -> None:
    """IP-04: Gateway embedding route builds direct embedding auth headers."""
    import src.api.router_embed as router_embed

    monkeypatch.setattr(router_embed, "EMBEDDING_SERVICE_AUTH_TOKEN", "embed-token")

    headers = router_embed._embedding_service_headers()
    assert headers["x-embedding-service-token"] == "embed-token"
    assert headers["authorization"] == "Bearer embed-token"
    assert "X-Service-Token" not in headers
    assert "Modal-Key" not in headers
    assert "Modal-Secret" not in headers


def test_ip05_gateway_to_reindex_route_forwards_token_and_params(monkeypatch) -> None:
    """IP-05: Gateway scrape/reindex forwards trigger token to direct jobs endpoint."""
    from src.api import router_scrape

    monkeypatch.setattr(router_scrape, "modal_function_invocation_enabled", lambda: False)

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

    monkeypatch.setattr(
        router_scrape,
        "REINDEX_SERVICE_URL",
        "https://reindex.example.com/jobs",
    )
    monkeypatch.setattr(router_scrape, "REINDEX_TRIGGER_TOKEN", "reindex-secret")
    monkeypatch.setattr(router_scrape.httpx, "AsyncClient", lambda *args, **kwargs: _StubClient())

    app = FastAPI()
    app.include_router(router_scrape.router, prefix="/api/v1")
    client = TestClient(app)

    response = client.post("/api/v1/scrape/reindex?clean=true&verbose=true")
    assert response.status_code == 200
    assert captured["url"] == "https://reindex.example.com/jobs/reindex"
    assert captured["params"] == {"clean": True, "stream": True, "verbose": True}
    assert captured["headers"] == {"x-reindex-token": "reindex-secret"}


def test_ip06_agent_to_embedding_direct_endpoint_headers(monkeypatch) -> None:
    """IP-06: Agent startup wires direct embedding URL + auth token into client factory."""

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
    # Modal URLs require function invocation + tokens (see enforce_modal_function_policy_for_urls).
    monkeypatch.setenv("MODAL_FUNCTION_INVOCATION", "auto")
    monkeypatch.setenv("MODAL_TOKEN_ID", "ak-ip06-contract")
    monkeypatch.setenv("MODAL_TOKEN_SECRET", "as-ip06-contract")
    monkeypatch.setenv(
        "EMBEDDING_UPSTREAM_URL", "https://vecinita--vecinita-embedding-web-app.modal.run"
    )
    monkeypatch.setenv("EMBEDDING_SERVICE_AUTH_TOKEN", "embed-token")

    import src.config as app_config

    importlib.reload(app_config)

    import src.agent.main as agent_main

    importlib.reload(agent_main)

    assert captured["url"] == "https://vecinita--vecinita-embedding-web-app.modal.run"
    assert captured["validate_on_init"] is True
    assert captured["auth_token"] == "embed-token"


def test_ip07_agent_to_model_uses_direct_modal_fallback_on_render(monkeypatch) -> None:
    """IP-07: Agent model URL normalizes to direct Modal endpoint on Render."""
    monkeypatch.setenv("RENDER", "true")

    import src.config as app_config

    importlib.reload(app_config)

    resolved = app_config._normalize_internal_service_url(
        "http://localhost:11434",
        fallback_url="https://vecinita--vecinita-model-api.modal.run",
    )
    assert resolved == "https://vecinita--vecinita-model-api.modal.run"


def test_ip08_agent_tools_postgres_fallback_with_database_url(monkeypatch) -> None:
    """IP-08: Agent tools call Postgres fallback when a database URL is configured."""
    mock_store = Mock()
    mock_store.query_chunks.side_effect = RuntimeError("primary store unavailable")
    mock_embedding_model = Mock()
    mock_embedding_model.embed_query.return_value = [0.1] * 384

    monkeypatch.setenv("DATABASE_URL", "postgresql://user:pass@localhost:5432/db")
    monkeypatch.setenv("POSTGRES_DATA_READS_ENABLED", "true")

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
    monkeypatch.setattr(db_search_module, "_query_postgres_fallback", postgres_mock)

    import src.config as app_config

    importlib.reload(app_config)

    tool = create_db_search_tool(
        mock_store, mock_embedding_model, match_threshold=0.3, match_count=5
    )
    rows = json.loads(tool.invoke("housing"))

    assert rows[0]["source_url"] == "https://example.org/postgres"
    assert postgres_mock.called
    assert get_last_search_metrics()["retrieval_backend"] == "postgres"


def test_ip09_agent_tools_remain_postgres_only(monkeypatch) -> None:
    """IP-09: Agent tools remain postgres-only when the primary store fails."""
    mock_store = Mock()
    mock_store.query_chunks.side_effect = RuntimeError("primary store unavailable")
    mock_embedding_model = Mock()
    mock_embedding_model.embed_query.return_value = [0.1] * 384
    monkeypatch.setenv("DATABASE_URL", "postgresql://user:pass@localhost:5432/db")

    postgres_mock = Mock(
        return_value=[
            {
                "id": "doc-pg-2",
                "content": "postgres result",
                "source_url": "https://example.org/postgres",
                "source_domain": "example.org",
                "similarity": 0.89,
                "metadata": {},
            }
        ]
    )
    monkeypatch.setattr(db_search_module, "_query_postgres_fallback", postgres_mock)

    import src.config as app_config

    importlib.reload(app_config)

    tool = create_db_search_tool(
        mock_store, mock_embedding_model, match_threshold=0.3, match_count=5
    )
    rows = json.loads(tool.invoke("benefits"))

    assert rows[0]["source_url"] == "https://example.org/postgres"
    assert postgres_mock.called
    assert get_last_search_metrics()["retrieval_backend"] == "postgres"


def test_ip10_scraper_uploader_writes_to_sync_backend() -> None:
    """IP-10: Scraper uploader sends chunk rows to configured sync backend."""
    with (
        patch.object(DatabaseUploader, "_init_embeddings"),
        patch.object(DatabaseUploader, "_init_vector_sync"),
        patch.object(DatabaseUploader, "_init_local_llm_tagger"),
    ):
        uploader = DatabaseUploader(use_local_embeddings=False)

    uploader.local_llm_tagger = None
    uploader.local_llm_raw_model = None
    uploader._generate_embeddings = Mock(return_value=[[0.2] * 384])
    uploader._sync_rows = Mock(return_value=True)

    uploaded, failed = uploader.upload_chunks(
        chunks=[{"text": "community support", "metadata": {}}],
        source_identifier="https://example.org/vector-sync",
        loader_type="playwright",
    )

    assert uploaded == 1
    assert failed == 0
    uploader._sync_rows.assert_called_once()


def test_ip11_scraper_uploader_switches_to_postgres_sync_target() -> None:
    """IP-11: Scraper uploader routes vector sync to Postgres when configured."""
    with (
        patch.object(DatabaseUploader, "_init_embeddings"),
        patch.object(DatabaseUploader, "_init_vector_sync"),
        patch.object(DatabaseUploader, "_init_local_llm_tagger"),
    ):
        uploader = DatabaseUploader(use_local_embeddings=False)

    uploader.vector_sync_target = "postgres"
    uploader._sync_rows_to_postgres = Mock(return_value=True)

    ok = uploader._sync_rows(
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
    """IP-12: Documents router keeps SQL + public asset URL builder contract."""
    import importlib

    from src.api import router_documents

    monkeypatch.setenv("UPLOADS_PUBLIC_BASE_URL", "https://assets.example.org/public")
    importlib.reload(router_documents)
    public_url = router_documents._build_public_storage_url("documents", "uploads/file.txt")
    assert public_url == "https://assets.example.org/public/documents/uploads/file.txt"

    normalized = router_documents._normalize_public_source(
        {
            "source_url": "https://example.org/resource",
            "metadata": {"tags": ["housing"], "download_url": "https://cdn.example.org/file.pdf"},
            "total_chunks": 3,
        }
    )
    assert normalized["downloadable"] is True
    assert normalized["download_url"] == "https://cdn.example.org/file.pdf"


def test_ip13_direct_modal_endpoint_contract_files() -> None:
    """IP-13: Service endpoint contracts prefer direct Modal URLs and no routing token headers."""
    service_endpoints_content = _read_workspace_file("backend", "src", "service_endpoints.py")
    embed_router_content = _read_workspace_file("backend", "src", "api", "router_embed.py")

    assert "vecinita--vecinita-scraper-api-fastapi.modal.run/jobs" in service_endpoints_content
    assert '"X-Service-Token"' not in embed_router_content


def test_ip14_env_auth_contract_local_render_and_modal(monkeypatch) -> None:
    """IP-14: Env/auth contract across local HTTP and Render+Modal invocation modes."""
    from src.services.modal import invoker

    # Local development contract: no Modal invocation requirement for non-Modal endpoints.
    monkeypatch.delenv("RENDER", raising=False)
    monkeypatch.delenv("RENDER_SERVICE_ID", raising=False)
    monkeypatch.delenv("MODAL_FUNCTION_INVOCATION", raising=False)
    monkeypatch.delenv("MODAL_TOKEN_ID", raising=False)
    monkeypatch.delenv("MODAL_TOKEN_SECRET", raising=False)
    assert invoker.modal_function_invocation_enabled() is False
    invoker.enforce_modal_function_policy_for_urls(
        {
            "EMBEDDING_UPSTREAM_URL": "http://localhost:8001",
            "OLLAMA_BASE_URL": "http://localhost:11434",
        }
    )

    # Render contract: Modal-hosted endpoints require invocation mode + token pair.
    monkeypatch.setenv("RENDER", "true")
    monkeypatch.setenv("MODAL_FUNCTION_INVOCATION", "auto")
    monkeypatch.setenv("MODAL_TOKEN_ID", "ak-ip14-contract")
    monkeypatch.setenv("MODAL_TOKEN_SECRET", "as-ip14-contract")
    assert invoker.modal_function_invocation_enabled() is True
    invoker.enforce_modal_function_policy_for_urls(
        {"EMBEDDING_UPSTREAM_URL": "https://vecinita--vecinita-embedding-web-app.modal.run"}
    )

    # Misconfigured Render contract must fail fast so CI blocks bad deploy config.
    monkeypatch.setenv("MODAL_FUNCTION_INVOCATION", "1")
    monkeypatch.delenv("MODAL_TOKEN_ID", raising=False)
    monkeypatch.delenv("MODAL_TOKEN_SECRET", raising=False)
    with pytest.raises(RuntimeError, match="Modal tokens are missing"):
        invoker.enforce_modal_function_policy_for_urls(
            {"OLLAMA_BASE_URL": "https://vecinita--vecinita-model-api.modal.run"}
        )
