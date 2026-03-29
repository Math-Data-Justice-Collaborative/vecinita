"""Integration tests: agent API endpoints with Render proxy URL wiring.

Verifies that:
- /health and /config endpoints respond correctly.
- When RENDER env is set, the agent's ollama_base_url and embedding_service_url
  contain the correct proxy path prefixes (/model, /embedding).
- The /ask endpoint succeeds when LLM/embedding are replaced with mocks
  whose base_url reflects the proxy path.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

pytestmark = pytest.mark.integration


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def render_env(monkeypatch):
    """Apply env vars simulating a Render deployment."""
    monkeypatch.setenv("RENDER", "true")
    monkeypatch.setenv("RENDER_SERVICE_ID", "srv-integ-test")
    monkeypatch.setenv("OLLAMA_BASE_URL", "http://localhost:11434")
    monkeypatch.setenv("EMBEDDING_SERVICE_URL", "http://embedding-service:8001")
    monkeypatch.setenv("SUPABASE_URL", "https://test.supabase.co")
    monkeypatch.setenv("SUPABASE_KEY", "test-key")


# ---------------------------------------------------------------------------
# /health
# ---------------------------------------------------------------------------


@pytest.mark.api
def test_agent_health_endpoint_returns_200(fastapi_client):
    response = fastapi_client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data.get("status") in ("ok", "healthy", "degraded")


@pytest.mark.api
def test_agent_health_endpoint_returns_json(fastapi_client):
    response = fastapi_client.get("/health")
    assert response.headers.get("content-type", "").startswith("application/json")


# ---------------------------------------------------------------------------
# /config
# ---------------------------------------------------------------------------


@pytest.mark.api
def test_config_endpoint_returns_200(fastapi_client):
    response = fastapi_client.get("/config")
    assert response.status_code == 200


@pytest.mark.api
def test_config_endpoint_has_providers_list(fastapi_client):
    response = fastapi_client.get("/config")
    data = response.json()
    assert "providers" in data
    assert isinstance(data["providers"], list)
    assert len(data["providers"]) >= 1


@pytest.mark.api
def test_config_endpoint_provider_has_required_fields(fastapi_client):
    response = fastapi_client.get("/config")
    data = response.json()
    for provider in data["providers"]:
        assert "key" in provider or "name" in provider, f"Provider missing key/name: {provider}"


@pytest.mark.api
def test_config_default_provider_is_ollama(fastapi_client):
    response = fastapi_client.get("/config")
    data = response.json()
    providers = data.get("providers", [])
    keys = [p.get("key") or p.get("name") for p in providers]
    assert "ollama" in keys


# ---------------------------------------------------------------------------
# /ask — basic non-streaming
# ---------------------------------------------------------------------------


@pytest.mark.api
def test_ask_endpoint_returns_200_with_mocked_llm(fastapi_client):
    import src.agent.main as agent_main

    fake_llm = MagicMock()
    fake_llm.invoke.return_value = MagicMock(content="Test answer from mock LLM.")

    with patch.object(agent_main, "_get_llm_without_tools", return_value=fake_llm):
        with patch("src.agent.main.supabase") as mock_supabase:
            mock_supabase.rpc.return_value.data = []
            response = fastapi_client.get("/ask", params={"question": "What is housing?"})

    assert response.status_code == 200


@pytest.mark.api
def test_ask_endpoint_returns_answer_field(fastapi_client):
    import src.agent.main as agent_main

    fake_llm = MagicMock()
    fake_llm.invoke.return_value = MagicMock(content="Community housing is available.")

    with patch.object(agent_main, "_get_llm_without_tools", return_value=fake_llm):
        with patch("src.agent.main.supabase") as mock_supabase:
            mock_supabase.rpc.return_value.data = []
            response = fastapi_client.get("/ask", params={"question": "housing programs"})

    data = response.json()
    assert (
        "answer" in data or "message" in data or "response" in data
    ), f"No answer field in response: {data}"


@pytest.mark.api
def test_ask_endpoint_rejects_empty_question(fastapi_client):
    response = fastapi_client.get("/ask", params={"question": ""})
    assert response.status_code in (400, 422)


@pytest.mark.api
def test_ask_endpoint_rejects_missing_question(fastapi_client):
    response = fastapi_client.get("/ask")
    assert response.status_code in (400, 422)


# ---------------------------------------------------------------------------
# Proxy URL wiring assertions (on Render environment)
# ---------------------------------------------------------------------------


@pytest.mark.api
def test_ollama_base_url_uses_model_proxy_prefix_on_render(render_env):
    """On Render, ollama_base_url must end with /model (proxy routing prefix)."""
    import src.agent.main as m

    result = m._normalize_internal_service_url(
        "http://localhost:11434",
        fallback_url="http://vecinita-modal-proxy-48hk:10000/model",
    )
    assert (
        "/model" in result
    ), f"ollama_base_url should contain /model prefix for proxy routing, got: {result}"


@pytest.mark.api
def test_embedding_url_uses_embedding_proxy_prefix_on_render(render_env):
    """On Render, embedding URL must end with /embedding (proxy routing prefix)."""
    import src.agent.main as m

    result = m._normalize_internal_service_url(
        "http://embedding-service:8001",
        fallback_url="http://vecinita-modal-proxy-48hk:10000/embedding",
    )
    assert (
        "/embedding" in result
    ), f"embedding_service_url should contain /embedding prefix, got: {result}"


@pytest.mark.api
def test_proxy_fallback_host_is_internal_render_hostname(render_env):
    """The proxy host must be the Render private-network hostname, not public HTTPS."""
    import src.agent.main as m

    result = m._normalize_internal_service_url(
        "http://localhost:11434",
        fallback_url="http://vecinita-modal-proxy-48hk:10000/model",
    )
    assert "vecinita-modal-proxy" in result
    assert (
        "onrender.com" not in result
    ), "Should use Render private hostname not public URL to avoid egress"


@pytest.mark.api
def test_off_render_url_uses_env_var_value(monkeypatch):
    """Not on Render: the raw env var value must be preserved unchanged."""
    monkeypatch.delenv("RENDER", raising=False)
    monkeypatch.delenv("RENDER_SERVICE_ID", raising=False)

    import src.agent.main as m

    result = m._normalize_internal_service_url(
        "http://localhost:11434",
        fallback_url="http://vecinita-modal-proxy-48hk:10000/model",
    )
    assert result == "http://localhost:11434"
