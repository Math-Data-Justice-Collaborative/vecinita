"""Integration tests: agent API endpoints with Render direct endpoint URL wiring.

Verifies that:
- /health and /config endpoints respond correctly.
- When RENDER env is set, local/docker URLs resolve to direct Modal endpoints.
- The /ask endpoint succeeds when LLM/embedding are replaced with mocks.
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
# Direct endpoint wiring assertions (on Render environment)
# ---------------------------------------------------------------------------


@pytest.mark.api
def test_ollama_base_url_uses_direct_modal_endpoint_on_render(render_env):
    """On Render, ollama base URL should resolve away from local URL to direct Modal endpoint."""
    import src.agent.main as m

    result = m._normalize_internal_service_url(
        "http://localhost:11434",
        fallback_url="https://vecinita--vecinita-model-api.modal.run",
    )
    assert result == "https://vecinita--vecinita-model-api.modal.run"


@pytest.mark.api
def test_embedding_url_uses_direct_modal_endpoint_on_render(render_env):
    """On Render, embedding URL should resolve away from local URL to direct Modal endpoint."""
    import src.agent.main as m

    result = m._normalize_internal_service_url(
        "http://embedding-service:8001",
        fallback_url="https://vecinita--vecinita-embedding-web-app.modal.run",
    )
    assert result == "https://vecinita--vecinita-embedding-web-app.modal.run"


@pytest.mark.api
def test_direct_modal_fallback_host_is_public_modal_domain(render_env):
    """Direct endpoint mode should use Modal domains instead of internal proxy hostnames."""
    import src.agent.main as m

    result = m._normalize_internal_service_url(
        "http://localhost:11434",
        fallback_url="https://vecinita--vecinita-model-api.modal.run",
    )
    assert "modal.run" in result
    assert "vecinita-modal-proxy" not in result


@pytest.mark.api
def test_nonlocal_explicit_url_preserved_on_render(render_env):
    """On Render, explicitly configured non-local endpoints must be preserved."""
    import src.agent.main as m

    result = m._normalize_internal_service_url(
        "https://vecinita--vecinita-model-api.modal.run",
        fallback_url="https://vecinita--vecinita-model-api.modal.run",
    )
    assert result == "https://vecinita--vecinita-model-api.modal.run"


@pytest.mark.api
def test_off_render_url_uses_env_var_value(monkeypatch):
    """Not on Render: the raw env var value must be preserved unchanged."""
    monkeypatch.delenv("RENDER", raising=False)
    monkeypatch.delenv("RENDER_SERVICE_ID", raising=False)

    import src.agent.main as m

    result = m._normalize_internal_service_url(
        "http://localhost:11434",
        fallback_url="https://vecinita--vecinita-model-api.modal.run",
    )
    assert result == "http://localhost:11434"
