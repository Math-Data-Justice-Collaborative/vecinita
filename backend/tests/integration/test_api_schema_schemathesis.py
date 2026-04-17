"""Schemathesis-based OpenAPI conformance tests for stable gateway contracts."""

from __future__ import annotations

import importlib
import json
import re
import uuid
from pathlib import Path
from types import SimpleNamespace
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


class _FakeStreamBody:
    status_code = 200

    def raise_for_status(self) -> None:
        return None

    async def aiter_bytes(self):
        yield b'data: {"type":"complete","answer":"ok","sources":[]}\n\n'


class _FakeStreamCM:
    async def __aenter__(self) -> _FakeStreamBody:
        return _FakeStreamBody()

    async def __aexit__(self, exc_type, exc, tb) -> bool:
        return False


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


class _FakeDocumentsCursor:
    """Minimal cursor: SET statement_timeout, then document_chunks / sources queries."""

    def __init__(self) -> None:
        self._sql: str = ""
        self._params: tuple[Any, ...] = ()

    def __enter__(self) -> _FakeDocumentsCursor:
        return self

    def __exit__(self, *args: object) -> None:
        return None

    def execute(self, sql: str, params: Any = None) -> None:
        self._sql = sql or ""
        self._params = tuple(params) if params is not None else ()

    def fetchall(self) -> list[dict[str, Any]]:
        s = self._sql
        if (
            "SELECT chunk_index, chunk_size, content, metadata" in s
            and "public.document_chunks" in s
        ):
            return [
                {
                    "chunk_index": 0,
                    "chunk_size": 11,
                    "content": "hello world",
                    "metadata": {},
                },
            ]
        if "SELECT source_url, metadata FROM public.document_chunks" in s:
            return [
                {
                    "source_url": "https://example.org/doc",
                    "metadata": {"tags": ["housing"], "source_url": "https://example.org/doc"},
                },
            ]
        return []

    def fetchone(self) -> dict[str, Any] | None:
        s = self._sql
        if "FROM public.sources" in s and "WHERE url = %s" in s:
            url = self._params[0] if self._params else "https://example.org/x"
            return {"url": url, "title": "Example Source", "metadata": {}}
        if "FROM public.document_chunks" in s and "LIMIT 1" in s:
            return {
                "metadata": {"document_title": "Chunk Title", "source_url": "https://example.org/x"}
            }
        return None


class _FakeDocumentsConnection:
    def __enter__(self) -> _FakeDocumentsConnection:
        return self

    def __exit__(self, *args: object) -> None:
        return None

    def cursor(self, cursor_factory: Any = None) -> _FakeDocumentsCursor:
        return _FakeDocumentsCursor()


def _fake_documents_connect(*args: Any, **kwargs: Any) -> _FakeDocumentsConnection:
    return _FakeDocumentsConnection()


class _FakeModalJobRegistry:
    """In-memory registry so Modal job routes never call Modal SDK."""

    def __init__(self) -> None:
        self._by_id: dict[str, dict[str, Any]] = {}
        self._order: list[str] = []

    async def create_tracked_call(
        self,
        *,
        kind: str,
        function_call_id: str,
        app_name: str,
        function_name: str,
        extra: dict[str, Any] | None = None,
    ) -> str:
        jid = str(uuid.uuid4())
        rec: dict[str, Any] = {
            "gateway_job_id": jid,
            "kind": kind,
            "status": "completed",
            "modal_function_call_id": function_call_id,
            "modal_app": app_name,
            "modal_function": function_name,
            "created_at": "2020-01-01T00:00:00+00:00",
            "updated_at": "2020-01-01T00:00:00+00:00",
            "result": {"ok": True},
            "error": None,
        }
        if extra:
            rec["extra"] = extra
        self._by_id[jid] = rec
        self._order.insert(0, jid)
        return jid

    async def list_recent_ids(self, limit: int = 50) -> list[str]:
        return self._order[:limit]

    async def get_record(self, job_id: str) -> dict[str, Any] | None:
        if job_id in self._by_id:
            return dict(self._by_id[job_id])
        return {
            "gateway_job_id": job_id,
            "kind": "scrape",
            "status": "completed",
            "modal_function_call_id": "fc-test",
            "modal_app": "vecinita-scraper",
            "modal_function": "fn",
            "created_at": "2020-01-01T00:00:00+00:00",
            "updated_at": "2020-01-01T00:00:00+00:00",
            "result": None,
            "error": None,
        }

    async def update_record(self, job_id: str, patch: dict[str, Any]) -> None:
        base = self._by_id.setdefault(job_id, {"gateway_job_id": job_id})
        base.update(patch)

    async def delete_record(self, job_id: str) -> bool:
        self._by_id.pop(job_id, None)
        if job_id in self._order:
            self._order.remove(job_id)
        return True


async def _noop_background_scrape(*args: Any, **kwargs: Any) -> None:
    return None


def _reload_gateway_with_mocks(monkeypatch: pytest.MonkeyPatch, *, enable_auth: bool) -> Any:
    monkeypatch.setenv("ENABLE_AUTH", "true" if enable_auth else "false")
    # Avoid lifespan Modal URL policy failures when .env points at *.modal.run without tokens.
    monkeypatch.setenv("REINDEX_SERVICE_URL", "")
    monkeypatch.setenv("SCRAPER_ENDPOINT", "http://127.0.0.1:1")
    monkeypatch.setenv("MODEL_ENDPOINT", "http://127.0.0.1:1")

    import src.api.main as main_module
    import src.api.middleware as middleware_module
    import src.api.router_ask as router_ask
    import src.api.router_documents as router_documents
    import src.api.router_embed as router_embed
    import src.api.router_modal_jobs as router_modal_jobs
    import src.services.modal.invoker as invoker_module

    monkeypatch.setattr(
        invoker_module, "enforce_modal_function_policy_for_urls", lambda _urls: None
    )

    importlib.reload(middleware_module)
    importlib.reload(router_ask)
    importlib.reload(router_documents)
    importlib.reload(router_embed)
    importlib.reload(router_modal_jobs)

    router_scrape_module: Any = None
    try:
        import src.api.router_scrape as rs

        importlib.reload(rs)
        router_scrape_module = rs
    except ModuleNotFoundError:
        pass

    class _FakeAgentClient:
        async def get(self, url: str, params=None, timeout=None):
            if url.endswith("/config"):
                return _FakeResponse(
                    {
                        "providers": [{"name": "ollama", "models": ["gemma3"], "default": True}],
                        "models": {"ollama": ["gemma3"]},
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

        def stream(self, method: str, url: str, params=None, timeout=None):
            return _FakeStreamCM()

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
    monkeypatch.setattr(router_embed, "modal_function_invocation_enabled", lambda: False)
    # Avoid ``*.modal.run`` HTTP block in ``_http_embeddings_blocked_modal_host`` when env points at Modal.
    monkeypatch.setattr(router_embed, "_embedding_service_url", lambda: "http://127.0.0.1:8001")

    monkeypatch.setattr(
        router_documents,
        "get_resolved_database_url",
        lambda: "postgresql://schemathesis:schemathesis@127.0.0.1:5432/postgres",
    )
    monkeypatch.setattr(router_documents, "_pg_connect", _fake_documents_connect)

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

    monkeypatch.setattr(router_modal_jobs, "modal_function_invocation_enabled", lambda: True)
    monkeypatch.setattr(
        router_modal_jobs,
        "invoke_modal_scrape_job_submit",
        lambda payload: {"ok": True, "data": {"job_id": "modal-job-1", "status": "queued"}},
    )
    monkeypatch.setattr(
        router_modal_jobs,
        "invoke_modal_scrape_job_get",
        lambda job_id: {"ok": True, "data": {"job_id": job_id, "status": "completed"}},
    )
    monkeypatch.setattr(
        router_modal_jobs,
        "invoke_modal_scrape_job_list",
        lambda user_id, limit: {"ok": True, "data": {"jobs": [], "total": 0}},
    )
    monkeypatch.setattr(
        router_modal_jobs,
        "invoke_modal_scrape_job_cancel",
        lambda job_id: {"ok": True, "data": {"status": "cancelled", "job_id": job_id}},
    )
    monkeypatch.setattr(
        router_modal_jobs,
        "spawn_modal_scraper_reindex",
        lambda clean, stream, verbose: SimpleNamespace(object_id="fc-schemathesis-test"),
    )
    monkeypatch.setattr(router_modal_jobs, "get_modal_function_call_result", lambda cid, t: {})
    monkeypatch.setattr(router_modal_jobs, "modal_job_registry", _FakeModalJobRegistry())

    if router_scrape_module is not None:
        monkeypatch.setattr(router_scrape_module, "background_scrape_task", _noop_background_scrape)
        monkeypatch.setattr(router_scrape_module, "modal_function_invocation_enabled", lambda: True)
        monkeypatch.setattr(
            router_scrape_module,
            "invoke_modal_scraper_reindex",
            lambda clean, stream, verbose: {"status": "accepted", "job_id": "reindex-1"},
        )

    importlib.reload(main_module)

    return schemathesis.openapi.from_asgi("/api/v1/docs/openapi.json", main_module.app)


@pytest.fixture
def gateway_schema(monkeypatch):
    return _reload_gateway_with_mocks(monkeypatch, enable_auth=False)


@pytest.fixture
def gateway_schema_auth(monkeypatch):
    return _reload_gateway_with_mocks(monkeypatch, enable_auth=True)


schema = schemathesis.pytest.from_fixture("gateway_schema")
schema_auth = schemathesis.pytest.from_fixture("gateway_schema_auth")

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
    suppress_health_check=[HealthCheck.function_scoped_fixture, HealthCheck.filter_too_much],
)
def test_gateway_openapi_schema(case):
    # Restrict to server errors: default ``load_all_checks()`` includes unsupported-method
    # checks (e.g. TRACE on ``/`` behind StaticFiles) that require an ``Allow`` header on 405.
    case.call_and_validate(checks=[schemathesis.checks.not_a_server_error])


@pytest.mark.integration
@pytest.mark.schema
@schema.parametrize()
@settings(
    max_examples=12,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture, HealthCheck.filter_too_much],
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
    suppress_health_check=[HealthCheck.function_scoped_fixture, HealthCheck.filter_too_much],
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
