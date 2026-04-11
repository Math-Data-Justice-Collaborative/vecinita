"""Schemathesis-based OpenAPI conformance tests for stable gateway contracts."""

from __future__ import annotations

import importlib
import json
import re
from pathlib import Path
from typing import Any

import pytest

schemathesis = pytest.importorskip("schemathesis")
hypothesis = pytest.importorskip("hypothesis")
HealthCheck = hypothesis.HealthCheck
settings = hypothesis.settings

schemathesis.checks.load_all_checks()
from schemathesis.specs.openapi.checks import response_schema_conformance  # noqa: E402


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


def _fake_chunk_statistics(_limit: int) -> list[dict[str, Any]]:
    return [
        {
            "source_domain": "example.org",
            "chunk_count": 3,
            "avg_chunk_size": 100,
            "total_size": 300,
            "document_count": 1,
            "latest_chunk": None,
        }
    ]


def _reload_gateway_with_mocks(monkeypatch: pytest.MonkeyPatch, *, enable_auth: bool) -> Any:
    monkeypatch.setenv("ENABLE_AUTH", "true" if enable_auth else "false")

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

    monkeypatch.setattr(router_ask, "_get_agent_client", lambda: _FakeAgentClient())
    monkeypatch.setattr(router_embed.httpx, "AsyncClient", lambda *args, **kwargs: _EmbedClient())
    monkeypatch.setattr(
        router_documents,
        "_load_overview_via_sql",
        lambda: (
            {"total_chunks": 1, "avg_chunk_size": 24},
            [
                {
                    "id": "src-1",
                    "url": "https://example.org/housing",
                    "domain": "example.org",
                    "source_domain": "example.org",
                    "title": "Housing Guide",
                    "total_chunks": 1,
                    "tags": ["housing"],
                    "metadata": {"document_title": "Housing Guide"},
                    "download_url": None,
                    "downloadable": False,
                }
            ],
        ),
    )
    monkeypatch.setattr(router_documents, "_load_chunk_statistics_via_sql", _fake_chunk_statistics)

    return schemathesis.openapi.from_asgi("/api/v1/docs/openapi.json", main_module.app)


@pytest.fixture
def gateway_schema(monkeypatch):
    return _reload_gateway_with_mocks(monkeypatch, enable_auth=False)


@pytest.fixture
def gateway_schema_auth(monkeypatch):
    return _reload_gateway_with_mocks(monkeypatch, enable_auth=True)


schema = schemathesis.pytest.from_fixture("gateway_schema")
schema_auth = schemathesis.pytest.from_fixture("gateway_schema_auth")

_STABLE_OPERATIONS: frozenset[tuple[str, str]] = frozenset(
    {
        ("GET", "/health"),
        ("GET", "/config"),
        ("GET", "/integrations/status"),
        ("GET", "/api/v1/ask"),
        ("GET", "/api/v1/ask/config"),
        ("POST", "/api/v1/embed"),
        ("POST", "/api/v1/embed/batch"),
        ("POST", "/api/v1/embed/similarity"),
        ("GET", "/api/v1/embed/config"),
        ("POST", "/api/v1/embed/config"),
        ("GET", "/api/v1/documents/overview"),
        ("GET", "/api/v1/documents/chunk-statistics"),
    }
)

_RESPONSE_CONTRACT_OPERATIONS: frozenset[tuple[str, str]] = frozenset(
    {
        ("GET", "/health"),
        ("GET", "/config"),
        ("GET", "/integrations/status"),
        ("GET", "/api/v1/ask/config"),
        ("GET", "/api/v1/embed/config"),
        ("GET", "/api/v1/documents/overview"),
        ("GET", "/api/v1/documents/chunk-statistics"),
    }
)


@pytest.mark.integration
@pytest.mark.schema
@schema.parametrize()
@settings(
    max_examples=20,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture],
)
def test_gateway_openapi_schema(case):
    if (case.method, case.path) not in _STABLE_OPERATIONS:
        pytest.skip("Operation excluded from stable Schemathesis contract run")

    case.call_and_validate()


@pytest.mark.integration
@pytest.mark.schema
@schema.parametrize()
@settings(
    max_examples=12,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture],
)
def test_gateway_openapi_response_schema_contract(case):
    """Stricter tier: response bodies must match OpenAPI models where declared."""
    if (case.method, case.path) not in _RESPONSE_CONTRACT_OPERATIONS:
        pytest.skip("Operation excluded from response schema conformance tier")

    case.call_and_validate(
        checks=[
            schemathesis.checks.not_a_server_error,
            response_schema_conformance,
        ],
    )


@pytest.mark.integration
@pytest.mark.schema
@schema_auth.parametrize()
@settings(
    max_examples=8,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture],
)
def test_gateway_ask_with_bearer_auth(case):
    """When auth is enabled, /api/v1/ask accepts a valid Bearer API key (mocked agent)."""
    if (case.method, case.path) != ("GET", "/api/v1/ask"):
        pytest.skip("Auth-tier Schemathesis targets GET /api/v1/ask only")

    case.call_and_validate(
        headers={"Authorization": "Bearer sk_schema_contract_test_key"},
        checks=[schemathesis.checks.not_a_server_error],
    )


@pytest.mark.integration
@pytest.mark.schema
def test_schemathesis_config_file_is_present():
    config_path = Path(__file__).resolve().parents[2] / "schemathesis.toml"
    assert config_path.is_file()
    text = config_path.read_text(encoding="utf-8")
    assert re.search(r"(?m)^continue-on-failure\s*=\s*true\s*$", text)
    gen = re.search(r"(?m)^max-examples\s*=\s*(\d+)\s*$", text)
    assert gen is not None and int(gen.group(1)) >= 1
