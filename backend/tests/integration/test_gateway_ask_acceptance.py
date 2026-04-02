from __future__ import annotations

import importlib
import json

import httpx
import pytest
from fastapi.testclient import TestClient

pytestmark = [pytest.mark.integration, pytest.mark.api]


class _FakeResponse:
    def __init__(self, payload: dict, status_code: int = 200):
        self._payload = payload
        self.status_code = status_code
        self.text = json.dumps(payload)

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            request = httpx.Request("GET", "http://agent.test")
            response = httpx.Response(self.status_code, request=request, text=self.text)
            raise httpx.HTTPStatusError("upstream error", request=request, response=response)

    def json(self) -> dict:
        return self._payload


class _StreamResponse:
    def __init__(self, chunks: list[bytes]):
        self._chunks = chunks
        self.status_code = 200

    def raise_for_status(self) -> None:
        return None

    async def aiter_bytes(self):
        for chunk in self._chunks:
            yield chunk


class _StreamContext:
    def __init__(
        self,
        chunks: list[bytes] | None = None,
        exception: Exception | None = None,
    ):
        self._chunks = chunks or []
        self._exception = exception

    async def __aenter__(self):
        if self._exception is not None:
            raise self._exception
        return _StreamResponse(self._chunks)

    async def __aexit__(self, exc_type, exc, tb):
        return False


class _FakeAgentClient:
    def __init__(
        self,
        *,
        get_response: _FakeResponse | None = None,
        get_exception: Exception | None = None,
        stream_chunks: list[bytes] | None = None,
        stream_exception: Exception | None = None,
    ):
        self.get_response = get_response
        self.get_exception = get_exception
        self.stream_chunks = stream_chunks or []
        self.stream_exception = stream_exception
        self.get_calls: list[tuple[str, dict | None, float | None]] = []
        self.stream_calls: list[tuple[str, str, dict | None, float | None]] = []

    async def get(self, url: str, params=None, timeout=None):
        self.get_calls.append((url, params, timeout))
        if self.get_exception is not None:
            raise self.get_exception
        return self.get_response or _FakeResponse({})

    def stream(self, method: str, url: str, params=None, timeout=None):
        self.stream_calls.append((method, url, params, timeout))
        return _StreamContext(chunks=self.stream_chunks, exception=self.stream_exception)


def _build_gateway_client(env_vars, monkeypatch, *, enable_auth: bool = True):
    for key, value in env_vars.items():
        monkeypatch.setenv(key, value)

    monkeypatch.setenv("AGENT_SERVICE_URL", "http://agent.test")
    monkeypatch.setenv("DEMO_MODE", "false")
    monkeypatch.setenv("ENABLE_AUTH", "true" if enable_auth else "false")
    monkeypatch.setenv("AUTH_FAIL_CLOSED", "true")
    monkeypatch.delenv("MODAL_EMBEDDING_ENDPOINT", raising=False)

    import src.api.main as main_module
    import src.api.middleware as middleware_module
    import src.api.router_ask as router_ask_module

    importlib.reload(middleware_module)
    importlib.reload(router_ask_module)
    importlib.reload(main_module)

    return TestClient(main_module.app), middleware_module, router_ask_module


def _patch_auth(monkeypatch, middleware_module, *, valid: bool) -> None:
    async def _validate_api_key(self, api_key: str) -> bool:
        return valid

    async def _track_usage(self, api_key: str, tokens: int) -> None:
        return None

    monkeypatch.setattr(
        middleware_module.AuthenticationMiddleware,
        "_validate_api_key",
        _validate_api_key,
    )
    monkeypatch.setattr(
        middleware_module.AuthenticationMiddleware,
        "_track_usage",
        _track_usage,
    )


def test_gateway_ask_acceptance_success(env_vars, monkeypatch):
    client, middleware_module, router_ask_module = _build_gateway_client(env_vars, monkeypatch)
    _patch_auth(monkeypatch, middleware_module, valid=True)

    fake_client = _FakeAgentClient(
        get_response=_FakeResponse(
            {
                "answer": "Housing support is available through local mutual-aid groups.",
                "sources": [
                    {
                        "url": "https://example.org/housing",
                        "title": "Housing Guide",
                        "relevance": 0.98,
                    }
                ],
                "language": "en",
                "model": "llama3.1:8b",
                "response_time_ms": 42,
            }
        )
    )
    monkeypatch.setattr(router_ask_module, "_get_agent_client", lambda: fake_client)

    response = client.get(
        "/api/v1/ask",
        params={
            "question": "Where can I find housing help?",
            "thread_id": "thread-123",
            "lang": "en",
        },
        headers={"Authorization": "Bearer test-key"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["question"] == "Where can I find housing help?"
    assert data["answer"].startswith("Housing support")
    assert data["sources"][0]["url"] == "https://example.org/housing"
    assert data["model"] == "llama3.1:8b"
    assert fake_client.get_calls == [
        (
            "http://agent.test/ask",
            {
                "question": "Where can I find housing help?",
                "thread_id": "thread-123",
                "lang": "en",
                "tag_match_mode": "any",
                "include_untagged_fallback": "true",
                "rerank": "false",
                "rerank_top_k": 10,
            },
            120.0,
        )
    ]


def test_gateway_ask_acceptance_validation_failure(env_vars, monkeypatch):
    client, middleware_module, _ = _build_gateway_client(env_vars, monkeypatch)
    _patch_auth(monkeypatch, middleware_module, valid=True)

    response = client.get("/api/v1/ask", headers={"Authorization": "Bearer test-key"})

    assert response.status_code == 422


def test_gateway_ask_acceptance_requires_api_key(env_vars, monkeypatch):
    client, _, _ = _build_gateway_client(env_vars, monkeypatch)

    response = client.get("/api/v1/ask", params={"question": "Need help"})

    assert response.status_code == 401
    assert response.json()["error"] == "Missing API key"


def test_gateway_ask_acceptance_rate_limit(env_vars, monkeypatch):
    client, middleware_module, router_ask_module = _build_gateway_client(env_vars, monkeypatch)
    _patch_auth(monkeypatch, middleware_module, valid=True)
    middleware_module.ENDPOINT_RATE_LIMITS["/api/v1/ask"] = {
        "requests_per_hour": 1,
        "tokens_per_day": 1000,
    }
    monkeypatch.setattr(
        router_ask_module,
        "_get_agent_client",
        lambda: _FakeAgentClient(
            get_response=_FakeResponse(
                {"answer": "ok", "sources": [], "language": "en", "model": "test-model"}
            )
        ),
    )

    first = client.get(
        "/api/v1/ask",
        params={"question": "Need help"},
        headers={"Authorization": "Bearer test-key"},
    )
    second = client.get(
        "/api/v1/ask",
        params={"question": "Need help again"},
        headers={"Authorization": "Bearer test-key"},
    )

    assert first.status_code == 200
    assert second.status_code == 429
    assert second.headers["X-RateLimit-Limit"] == "1"
    assert second.json()["limit_type"] == "requests_per_hour"


def test_gateway_ask_acceptance_upstream_timeout(env_vars, monkeypatch):
    client, middleware_module, router_ask_module = _build_gateway_client(env_vars, monkeypatch)
    _patch_auth(monkeypatch, middleware_module, valid=True)
    monkeypatch.setattr(
        router_ask_module,
        "_get_agent_client",
        lambda: _FakeAgentClient(get_exception=httpx.TimeoutException("timed out")),
    )

    response = client.get(
        "/api/v1/ask",
        params={"question": "Need help"},
        headers={"Authorization": "Bearer test-key"},
    )

    assert response.status_code == 504
    assert "timeout" in response.json()["error"].lower()


def test_gateway_ask_stream_acceptance_success(env_vars, monkeypatch):
    client, middleware_module, router_ask_module = _build_gateway_client(env_vars, monkeypatch)
    _patch_auth(monkeypatch, middleware_module, valid=True)

    fake_client = _FakeAgentClient(
        stream_chunks=[
            b'data: {"type":"thinking","message":"Searching"}\n\n',
            b'data: {"type":"complete","answer":"done","sources":[]}\n\n',
        ]
    )
    monkeypatch.setattr(router_ask_module, "_get_agent_client", lambda: fake_client)

    response = client.get(
        "/api/v1/ask/stream",
        params={"question": "Need help", "thread_id": "thread-123"},
        headers={"Authorization": "Bearer test-key"},
    )

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/event-stream")
    assert response.text.count("\n\n") >= 2
    assert '"type":"complete"' in response.text
    assert fake_client.stream_calls == [
        (
            "GET",
            "http://agent.test/ask-stream",
            {
                "question": "Need help",
                "thread_id": "thread-123",
                "tag_match_mode": "any",
                "include_untagged_fallback": "true",
                "rerank": "false",
                "rerank_top_k": 10,
            },
            120.0,
        )
    ]


def test_gateway_ask_stream_acceptance_requires_api_key(env_vars, monkeypatch):
    client, _, _ = _build_gateway_client(env_vars, monkeypatch)

    response = client.get("/api/v1/ask/stream", params={"question": "Need help"})

    assert response.status_code == 401
    assert response.json()["error"] == "Missing API key"


def test_gateway_ask_stream_acceptance_rate_limit(env_vars, monkeypatch):
    client, middleware_module, router_ask_module = _build_gateway_client(env_vars, monkeypatch)
    _patch_auth(monkeypatch, middleware_module, valid=True)
    middleware_module.ENDPOINT_RATE_LIMITS["/api/v1/ask"] = {
        "requests_per_hour": 1,
        "tokens_per_day": 1000,
    }
    monkeypatch.setattr(
        router_ask_module,
        "_get_agent_client",
        lambda: _FakeAgentClient(stream_chunks=[b'data: {"type":"complete"}\n\n']),
    )

    first = client.get(
        "/api/v1/ask/stream",
        params={"question": "Need help"},
        headers={"Authorization": "Bearer test-key"},
    )
    second = client.get(
        "/api/v1/ask/stream",
        params={"question": "Need help again"},
        headers={"Authorization": "Bearer test-key"},
    )

    assert first.status_code == 200
    assert second.status_code == 429
    assert second.json()["limit_type"] == "requests_per_hour"


def test_gateway_ask_stream_acceptance_timeout_yields_sse_error(env_vars, monkeypatch):
    client, middleware_module, router_ask_module = _build_gateway_client(env_vars, monkeypatch)
    _patch_auth(monkeypatch, middleware_module, valid=True)
    monkeypatch.setattr(
        router_ask_module,
        "_get_agent_client",
        lambda: _FakeAgentClient(stream_exception=httpx.TimeoutException("timed out")),
    )

    response = client.get(
        "/api/v1/ask/stream",
        params={"question": "Need help"},
        headers={"Authorization": "Bearer test-key"},
    )

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/event-stream")
    assert '"type": "error"' in response.text
    assert "Request timeout" in response.text


def test_gateway_ask_config_acceptance_falls_back_to_degraded_mode(env_vars, monkeypatch):
    client, _, router_ask_module = _build_gateway_client(env_vars, monkeypatch)
    monkeypatch.setattr(
        router_ask_module,
        "_get_agent_client",
        lambda: _FakeAgentClient(get_exception=httpx.RequestError("connection failed")),
    )

    response = client.get("/api/v1/ask/config")

    assert response.status_code == 200
    assert response.json()["service_status"] == "degraded"
