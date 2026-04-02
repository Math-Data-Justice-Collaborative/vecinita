"""Schemathesis-based OpenAPI conformance tests for stable gateway contracts."""

from __future__ import annotations

import importlib
import json
from pathlib import Path

import pytest
from hypothesis import HealthCheck, settings

schemathesis = pytest.importorskip("schemathesis")


class _FakeResponse:
    def __init__(self, payload: dict, status_code: int = 200):
        self._payload = payload
        self.status_code = status_code
        self.text = json.dumps(payload)

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            raise RuntimeError(f"HTTP {self.status_code}")

    def json(self):
        return self._payload


@pytest.fixture
def gateway_schema(monkeypatch):
    monkeypatch.setenv("ENABLE_AUTH", "false")

    import src.api.main as main_module
    import src.api.middleware as middleware_module
    import src.api.router_ask as router_ask
    import src.api.router_documents as router_documents
    import src.api.router_embed as router_embed

    importlib.reload(middleware_module)
    importlib.reload(router_ask)
    importlib.reload(router_documents)
    importlib.reload(router_embed)
    importlib.reload(main_module)

    class _FakeAgentClient:
        async def get(self, url: str, params=None, timeout=None):
            if url.endswith("/config"):
                return _FakeResponse(
                    {
                        "providers": [
                            {"name": "ollama", "models": ["llama3.1:8b"], "default": True}
                        ],
                        "models": {"ollama": ["llama3.1:8b"]},
                    }
                )
            return _FakeResponse(
                {
                    "answer": "Schema validation response",
                    "sources": [],
                    "language": "en",
                    "model": "test-model",
                }
            )

    class _EmbedClient:
        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return False

        async def post(self, url: str, json=None, headers=None):
            if url.endswith("/embed/batch") or url.endswith("/embed-batch"):
                queries = (json or {}).get("queries") or (json or {}).get("texts") or []
                return _FakeResponse(
                    {
                        "embeddings": [[0.1] * 4 for _ in queries],
                        "model": "sentence-transformers/all-MiniLM-L6-v2",
                        "dimension": 4,
                    }
                )
            if url.endswith("/config"):
                payload = json or {}
                return _FakeResponse(
                    {
                        "current": {
                            "provider": payload.get("provider", "huggingface"),
                            "model": payload.get("model", "sentence-transformers/all-MiniLM-L6-v2"),
                        }
                    }
                )
            return _FakeResponse(
                {
                    "embedding": [0.1] * 4,
                    "model": "sentence-transformers/all-MiniLM-L6-v2",
                    "dimension": 4,
                }
            )

        async def get(self, url: str, headers=None):
            return _FakeResponse(
                {
                    "current": {
                        "provider": "huggingface",
                        "model": "sentence-transformers/all-MiniLM-L6-v2",
                    }
                }
            )

    class _FakeChromaStore:
        def iter_all_chunks(self):
            return [
                {
                    "id": "chunk-1",
                    "content": "housing support details",
                    "metadata": {
                        "source_url": "https://example.org/housing",
                        "source_domain": "example.org",
                        "chunk_size": 24,
                        "document_title": "Housing Guide",
                        "tags": ["housing"],
                    },
                }
            ]

    monkeypatch.setattr(router_ask, "_get_agent_client", lambda: _FakeAgentClient())
    monkeypatch.setattr(router_embed.httpx, "AsyncClient", lambda *args, **kwargs: _EmbedClient())
    monkeypatch.setattr(router_documents, "get_chroma_store", lambda: _FakeChromaStore())

    return schemathesis.openapi.from_asgi("/api/v1/openapi.json", main_module.app)


schema = schemathesis.pytest.from_fixture("gateway_schema")


@pytest.mark.integration
@pytest.mark.schema
@schema.parametrize()
@settings(
    max_examples=20,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture],
)
def test_gateway_openapi_schema(case):
    allowed_operations = {
        ("GET", "/health"),
        ("GET", "/config"),
        ("GET", "/api/v1/ask"),
        ("GET", "/api/v1/ask/config"),
        ("POST", "/api/v1/embed"),
        ("POST", "/api/v1/embed/batch"),
        ("POST", "/api/v1/embed/similarity"),
        ("GET", "/api/v1/embed/config"),
        ("POST", "/api/v1/embed/config"),
        ("GET", "/api/v1/documents/overview"),
    }

    if (case.method, case.path) not in allowed_operations:
        pytest.skip("Operation excluded from stable Schemathesis contract run")

    case.call_and_validate()


@pytest.mark.integration
@pytest.mark.schema
def test_schemathesis_config_file_is_present():
    config_path = Path(__file__).resolve().parents[2] / "schemathesis.toml"
    assert config_path.exists()
    content = config_path.read_text(encoding="utf-8")
    assert "max-examples = 25" in content
    assert "continue-on-failure = true" in content
