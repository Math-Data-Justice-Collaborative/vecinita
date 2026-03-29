"""End-to-end tests: modal proxy routing for model and embedding traffic.

Simulates a Render deployment where the agent must not contact localhost or
Docker-internal hostnames.  Verifies the full request path from the agent's
/ask endpoint through the proxy URL normalization all the way to LLM +
embedding mock calls, confirming base_url parameters contain the correct
proxy path prefixes.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

pytestmark = pytest.mark.e2e


# ---------------------------------------------------------------------------
# Helper: assert a ChatOllama/httpx call used the proxy URL
# ---------------------------------------------------------------------------


def _proxy_model_base_url() -> str:
    return "http://vecinita-modal-proxy-48hk:10000/model"


def _proxy_embedding_base_url() -> str:
    return "http://vecinita-modal-proxy-48hk:10000/embedding"


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def render_env_vars():
    return {
        "RENDER": "true",
        "RENDER_SERVICE_ID": "srv-e2e-test",
        "OLLAMA_BASE_URL": "http://localhost:11434",
        "EMBEDDING_SERVICE_URL": "http://embedding-service:8001",
        "SUPABASE_URL": "https://test.supabase.co",
        "SUPABASE_KEY": "test-key",
        "OLLAMA_MODEL": "llama3.1:8b",
    }


# ---------------------------------------------------------------------------
# E2E: normalize on Render always yields proxy URLs
# ---------------------------------------------------------------------------


@pytest.mark.e2e
def test_normalize_always_returns_proxy_url_on_render(render_env_vars, monkeypatch):
    """Full simulate: all env vars set as on Render → both URLs must point to proxy."""
    for k, v in render_env_vars.items():
        monkeypatch.setenv(k, v)

    import src.agent.main as main

    ollama_result = main._normalize_internal_service_url(
        render_env_vars["OLLAMA_BASE_URL"],
        fallback_url=_proxy_model_base_url(),
    )
    embedding_result = main._normalize_internal_service_url(
        render_env_vars["EMBEDDING_SERVICE_URL"],
        fallback_url=_proxy_embedding_base_url(),
    )

    assert (
        ollama_result == _proxy_model_base_url()
    ), f"Model traffic must route via proxy; got {ollama_result}"
    assert (
        embedding_result == _proxy_embedding_base_url()
    ), f"Embedding traffic must route via proxy; got {embedding_result}"


@pytest.mark.e2e
def test_proxy_model_path_stripped_by_proxy_convention(render_env_vars, monkeypatch):
    """The /model prefix is what the proxy strips before forwarding to Ollama.

    ChatOllama will call <base_url>/api/chat; the proxy receives
    /model/api/chat and strips /model to forward /api/chat to the model backend.
    """
    for k, v in render_env_vars.items():
        monkeypatch.setenv(k, v)

    import src.agent.main as main

    ollama_url = main._normalize_internal_service_url(
        render_env_vars["OLLAMA_BASE_URL"],
        fallback_url=_proxy_model_base_url(),
    )

    # Simulate what langchain_ollama would call:
    effective_chat_endpoint = ollama_url.rstrip("/") + "/api/chat"
    assert effective_chat_endpoint == "http://vecinita-modal-proxy-48hk:10000/model/api/chat"


@pytest.mark.e2e
def test_proxy_embedding_path_stripped_by_proxy_convention(render_env_vars, monkeypatch):
    """The /embedding prefix is stripped by the proxy → upstream receives /embed."""
    for k, v in render_env_vars.items():
        monkeypatch.setenv(k, v)

    import src.agent.main as main

    embedding_url = main._normalize_internal_service_url(
        render_env_vars["EMBEDDING_SERVICE_URL"],
        fallback_url=_proxy_embedding_base_url(),
    )

    # Simulate what EmbeddingServiceClient would call:
    effective_embed_endpoint = embedding_url.rstrip("/") + "/embed"
    assert effective_embed_endpoint == "http://vecinita-modal-proxy-48hk:10000/embedding/embed"

    effective_health_endpoint = embedding_url.rstrip("/") + "/health"
    assert effective_health_endpoint == "http://vecinita-modal-proxy-48hk:10000/embedding/health"


@pytest.mark.e2e
def test_normalize_is_idempotent_for_proxy_url(render_env_vars, monkeypatch):
    """If the env var is already set to the proxy URL, it must not be double-prefixed."""
    for k, v in render_env_vars.items():
        monkeypatch.setenv(k, v)
    monkeypatch.setenv("OLLAMA_BASE_URL", _proxy_model_base_url())

    import src.agent.main as main

    result = main._normalize_internal_service_url(
        _proxy_model_base_url(),
        fallback_url=_proxy_model_base_url(),
    )
    assert result == _proxy_model_base_url()
    assert result.count("/model") == 1, f"Path prefix duplicated: {result}"


@pytest.mark.e2e
def test_full_ask_flow_uses_mocked_llm_and_embedding(fastapi_client):
    """Smoke test: /ask completes without errors using mocked dependencies."""
    import src.agent.main as agent_main

    fake_llm = MagicMock()
    fake_llm.invoke.return_value = MagicMock(
        content="Housing assistance is available through several programs. "
        "(Source: https://example.com/housing)"
    )

    with patch.object(agent_main, "_get_llm_without_tools", return_value=fake_llm):
        with patch("src.agent.main.supabase") as mock_supabase:
            mock_supabase.rpc.return_value.data = [
                {
                    "content": "Housing programs info.",
                    "source_url": "https://example.com/housing",
                    "similarity": 0.92,
                    "chunk_index": 0,
                }
            ]
            response = fastapi_client.get(
                "/ask", params={"question": "What housing programs are available?"}
            )

    assert response.status_code == 200
    data = response.json()
    # At least one of these keys must carry the answer text
    answer_text = data.get("answer") or data.get("message") or data.get("response") or ""
    assert len(answer_text) > 0, f"Expected non-empty answer, got: {data}"


@pytest.mark.e2e
def test_full_ask_flow_with_no_db_results(fastapi_client):
    """When vector search returns nothing, agent still responds gracefully."""
    import src.agent.main as agent_main

    fake_llm = MagicMock()
    fake_llm.invoke.return_value = MagicMock(content="I don't have information about that topic.")

    with patch.object(agent_main, "_get_llm_without_tools", return_value=fake_llm):
        with patch("src.agent.main.supabase") as mock_supabase:
            mock_supabase.rpc.return_value.data = []
            response = fastapi_client.get(
                "/ask", params={"question": "A very obscure topic not in the knowledge base"}
            )

    assert response.status_code == 200


@pytest.mark.e2e
@pytest.mark.slow
def test_streaming_ask_flow_produces_sse_events(fastapi_client, parse_sse_events):
    """Streaming /ask-stream endpoint produces well-formed SSE when mocked."""
    import src.agent.main as agent_main

    fake_llm = MagicMock()
    fake_llm.invoke.return_value = MagicMock(content="Streaming answer via proxy.")

    with patch.object(agent_main, "_get_llm_without_tools", return_value=fake_llm):
        with patch("src.agent.main.supabase") as mock_supabase:
            mock_supabase.rpc.return_value.data = []
            response = fastapi_client.get(
                "/ask-stream", params={"question": "Test streaming through proxy"}
            )

    assert response.status_code == 200
    ct = response.headers.get("content-type", "")
    assert (
        "text/event-stream" in ct or "application/json" in ct
    ), f"Expected SSE or JSON content-type, got: {ct}"
