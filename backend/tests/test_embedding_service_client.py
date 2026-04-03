"""Unit tests for embedding service client validation and fallback behavior."""

from unittest.mock import Mock

import httpx
import pytest

from src.embedding_service.client import EmbeddingServiceClient, create_embedding_client

pytestmark = pytest.mark.unit


class _Resp:
    def __init__(self, status_code=200, payload=None):
        self.status_code = status_code
        self._payload = payload or {}

    def raise_for_status(self):
        if self.status_code >= 400:
            raise RuntimeError(f"HTTP {self.status_code}")

    def json(self):
        return self._payload


def test_validate_connection_uses_localhost_fallback(monkeypatch):
    client = EmbeddingServiceClient(base_url="http://embedding-service:8001")

    def fake_get(url, *args, **kwargs):
        if url.startswith("http://embedding-service:8001"):
            raise RuntimeError("dns fail")
        return _Resp(status_code=200, payload={"status": "ok"})

    monkeypatch.setattr(client.client, "get", fake_get)
    active = client.validate_connection()
    assert active in ("http://localhost:8001", "http://127.0.0.1:8001")


def test_create_embedding_client_validate_on_init(monkeypatch):
    called = {"validated": False}

    def fake_validate(self):
        called["validated"] = True
        return self.base_url

    monkeypatch.setattr(EmbeddingServiceClient, "validate_connection", fake_validate)

    create_embedding_client("http://embedding-service:8001", validate_on_init=True)
    assert called["validated"] is True


def test_validate_connection_raises_when_all_candidates_fail(monkeypatch):
    client = EmbeddingServiceClient(base_url="http://embedding-service:8001")
    monkeypatch.setattr(
        client.client, "get", lambda *_args, **_kwargs: (_ for _ in ()).throw(RuntimeError("down"))
    )

    with pytest.raises(RuntimeError, match="Embedding service is unavailable"):
        client.validate_connection()


def test_candidate_urls_include_discovered_cloud_run(monkeypatch):
    client = EmbeddingServiceClient(base_url="http://embedding-service:8001")

    monkeypatch.setenv("EMBEDDING_CLOUD_RUN_SERVICE", "vecinita-embed")
    monkeypatch.setenv("GCP_PROJECT_ID", "demo-project")
    monkeypatch.setenv("GCP_REGION", "us-central1")

    class _Proc:
        returncode = 0
        stdout = "https://vecinita-embed-abc123-uc.a.run.app\n"
        stderr = ""

    monkeypatch.setattr("subprocess.run", lambda *args, **kwargs: _Proc())

    candidates = client._candidate_base_urls()
    assert "https://vecinita-embed-abc123-uc.a.run.app" in candidates


def test_candidate_urls_include_local_fallbacks_for_remote_base_url(monkeypatch):
    monkeypatch.delenv("RENDER", raising=False)
    monkeypatch.delenv("RENDER_SERVICE_ID", raising=False)

    client = EmbeddingServiceClient(
        base_url="https://vecinita--vecinita-embedding-embeddingservicecontainer-api.modal.run"
    )

    candidates = client._candidate_base_urls()

    assert "http://localhost:8001" in candidates
    assert "http://127.0.0.1:8001" in candidates
    assert "http://localhost:10000/embedding" not in candidates


def test_embed_documents_falls_back_to_alt_batch_endpoint(monkeypatch):
    client = EmbeddingServiceClient(base_url="http://localhost:8001")
    calls = []

    def fake_post_with_fallback(endpoint, payload):
        calls.append(endpoint)
        if endpoint == "/embed-batch":
            raise RuntimeError("404")
        return _Resp(status_code=200, payload={"embeddings": [[0.1, 0.2]]})

    monkeypatch.setattr(client, "_post_with_fallback", fake_post_with_fallback)

    result = client.embed_documents(["hello"])
    assert result == [[0.1, 0.2]]
    assert calls == ["/embed-batch", "/embed/batch"]


def test_embed_query_falls_back_to_query_payload_on_422(monkeypatch):
    client = EmbeddingServiceClient(base_url="http://localhost:8001")
    calls: list[tuple[str, dict]] = []

    def fake_post_with_fallback(endpoint, payload, **_kwargs):
        calls.append((endpoint, payload))
        if payload == {"text": "hello"}:
            request = httpx.Request("POST", "http://localhost:8001/embed")
            response = httpx.Response(
                422,
                request=request,
                json={"detail": [{"loc": ["body", "query"], "msg": "Field required"}]},
            )
            raise httpx.HTTPStatusError("422", request=request, response=response)
        return _Resp(status_code=200, payload={"embedding": [0.11, 0.22]})

    monkeypatch.setattr(client, "_post_with_fallback", fake_post_with_fallback)

    result = client.embed_query("hello")

    assert result == [0.11, 0.22]
    assert calls == [
        ("/embed", {"text": "hello"}),
        ("/embed", {"query": "hello"}),
    ]


def test_client_sets_auth_header_from_env(monkeypatch):
    monkeypatch.setenv("EMBEDDING_SERVICE_AUTH_TOKEN", "abc123")
    client = EmbeddingServiceClient(base_url="http://localhost:8001")

    assert client.client.headers.get("x-embedding-service-token") == "abc123"


def test_client_prefers_explicit_auth_token_over_env(monkeypatch):
    monkeypatch.setenv("EMBEDDING_SERVICE_AUTH_TOKEN", "env-token")
    client = EmbeddingServiceClient(
        base_url="http://localhost:8001",
        auth_token="explicit-token",
    )

    assert client.client.headers.get("x-embedding-service-token") == "explicit-token"


def test_client_does_not_set_modal_headers_when_available(monkeypatch):
    monkeypatch.setenv("MODAL_TOKEN_ID", "wk-test-modal-key")
    monkeypatch.setenv("MODAL_TOKEN_SECRET", "ws-test-modal-secret")

    client = EmbeddingServiceClient(base_url="https://example.modal.run")

    assert client.client.headers.get("Modal-Key") is None
    assert client.client.headers.get("Modal-Secret") is None


def test_client_does_not_set_modal_key_from_token_id(monkeypatch):
    monkeypatch.delenv("MODAL_TOKEN_ID", raising=False)
    monkeypatch.setenv("MODAL_API_TOKEN_ID", "wk-token-id-fallback")
    monkeypatch.setenv("MODAL_TOKEN_SECRET", "ws-test-modal-secret")

    client = EmbeddingServiceClient(base_url="https://example.modal.run")

    assert client.client.headers.get("Modal-Key") is None
    assert client.client.headers.get("Modal-Secret") is None


def test_client_does_not_set_proxy_auth_token_header(monkeypatch):
    monkeypatch.setenv("PROXY_AUTH_TOKEN", "proxy-shared-token")

    client = EmbeddingServiceClient(base_url="https://example.modal.run")

    assert client.client.headers.get("X-Proxy-Token") is None


def test_create_embedding_client_passes_explicit_auth_token(monkeypatch):
    captured: dict[str, str | None] = {}

    def fake_init(self, base_url="http://localhost:8001", timeout=30, auth_token=None):
        captured["base_url"] = base_url
        captured["auth_token"] = auth_token
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.auth_token = auth_token
        self.client = Mock(headers={})

    monkeypatch.setattr(EmbeddingServiceClient, "__init__", fake_init)

    create_embedding_client(
        "http://embedding-service:8001",
        auth_token="factory-token",
    )

    assert captured == {
        "base_url": "http://embedding-service:8001",
        "auth_token": "factory-token",
    }
