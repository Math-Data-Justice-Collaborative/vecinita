"""Integration tests for local-only model selection and config behavior."""

import json

import pytest

pytestmark = pytest.mark.integration


@pytest.mark.fallback
def test_config_endpoint_lists_only_local_provider(fastapi_client):
    response = fastapi_client.get("/config")

    assert response.status_code == 200
    data = response.json()
    providers = data["providers"]

    assert [p.get("key") for p in providers] == ["ollama"]
    assert "ollama" in str(providers[0].get("label", "")).lower()


@pytest.mark.fallback
def test_provider_order_is_stable(fastapi_client):
    response = fastapi_client.get("/config")
    data = response.json()

    assert [p["key"] for p in data["providers"]] == ["ollama"]


@pytest.mark.fallback
def test_config_default_provider_matches_current_selection(fastapi_client, monkeypatch):
    import src.agent.main as agent_main

    monkeypatch.setitem(agent_main.CURRENT_SELECTION, "provider", "ollama")
    monkeypatch.setitem(agent_main.CURRENT_SELECTION, "model", "llama3.1:8b")

    response = fastapi_client.get("/config")
    assert response.status_code == 200
    data = response.json()

    assert data.get("defaultProvider") == "ollama"
    assert data.get("defaultModel") == "llama3.1:8b"


@pytest.mark.fallback
def test_unsupported_provider_selection_resets_to_local_default(monkeypatch):
    import src.agent.main as agent_main

    monkeypatch.setitem(agent_main.CURRENT_SELECTION, "provider", "deepseek")
    monkeypatch.setitem(agent_main.CURRENT_SELECTION, "model", "deepseek-chat")

    agent_main._validate_or_resolve_selection()

    assert agent_main.CURRENT_SELECTION["provider"] == "ollama"
    assert agent_main.CURRENT_SELECTION["model"] == agent_main.ollama_model


@pytest.mark.fallback
def test_model_names_available_for_local_provider(fastapi_client):
    response = fastapi_client.get("/config")
    data = response.json()

    assert list(data["models"]) == ["ollama"]
    assert len(data["models"]["ollama"]) > 0


@pytest.mark.fallback
@pytest.mark.parametrize(
    "provider_key,should_find",
    [("ollama", True), ("local", False), ("invalid_provider", False)],
)
def test_get_provider_from_config(fastapi_client, provider_key, should_find):
    response = fastapi_client.get("/config")
    data = response.json()
    found = any(p["key"] == provider_key for p in data["providers"])

    assert found is should_find


@pytest.mark.fallback
def test_local_provider_has_model(fastapi_client):
    response = fastapi_client.get("/config")
    data = response.json()

    assert isinstance(data["models"], dict)
    assert len(data["models"]["ollama"]) > 0


@pytest.mark.fallback
def test_streaming_uses_local_provider_metadata(fastapi_client):
    response = fastapi_client.get("/ask-stream", params={"question": "Test streaming?"})

    assert response.status_code == 200

    events = []
    for line in response.text.split("\n"):
        if line.startswith("data: "):
            try:
                events.append(json.loads(line[6:]))
            except json.JSONDecodeError:
                pass

    complete = next((e for e in events if e.get("type") == "complete"), None)
    if complete and "metadata" in complete:
        model_used = complete["metadata"].get("model_used", "")
        assert ":" in model_used


@pytest.mark.fallback
def test_non_local_provider_request_is_ignored():
    import src.agent.main as agent_main

    resolved_provider, resolved_model = agent_main._resolve_effective_provider_model(
        "deepseek", "deepseek-chat"
    )

    assert resolved_provider == "ollama"
    assert resolved_model == agent_main.CURRENT_SELECTION["model"]
