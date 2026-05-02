"""Consumer Pact: gateway -> agent internal HTTP contract (`AGENT_SERVICE_URL`).

Generates:
    apis/gateway/pacts/vecinita-gateway-vecinita-agent.json
"""

from __future__ import annotations

from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from pact import Pact

pytestmark = [pytest.mark.integration, pytest.mark.contract]


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[4]


def _pact_output_dir() -> Path:
    return _repo_root() / "apis" / "gateway" / "pacts"


def _build_gateway_ask_client(agent_base_url: str, monkeypatch: pytest.MonkeyPatch) -> TestClient:
    monkeypatch.setenv("AGENT_SERVICE_URL", agent_base_url)
    monkeypatch.setenv("DEMO_MODE", "false")

    # Ensure each pact interaction uses a fresh upstream client bound to the mock server URL.
    from src.api import router_ask

    router_ask._AGENT_CLIENT = None

    app = FastAPI()
    app.include_router(router_ask.router, prefix="/api/v1")
    return TestClient(app)


def test_gateway_writes_agent_consumer_pact(monkeypatch: pytest.MonkeyPatch) -> None:
    pact = Pact("vecinita-gateway", "vecinita-agent").with_specification("V4")

    (
        pact.upon_receiving("an ask request forwarded by the gateway")
        .with_request("GET", "/ask")
        .with_query_parameters(
            {
                "question": "what is vecinita?",
                "thread_id": "thread-1",
                "lang": "en",
                "provider": "ollama",
                "model": "gemma3",
                "tag_match_mode": "any",
                "include_untagged_fallback": "true",
                "rerank": "false",
                "rerank_top_k": "10",
            }
        )
        .will_respond_with(200)
        .with_header("Content-Type", "application/json", part="Response")
        .with_body(
            {
                "answer": "Vecinita is a community-oriented retrieval assistant.",
                "sources": [
                    {
                        "title": "About Vecinita",
                        "url": "https://example.com/about",
                    }
                ],
                "thread_id": "thread-1",
                "language": "en",
                "model": "gemma3",
                "response_time_ms": 120,
            },
            content_type="application/json",
            part="Response",
        )
    )

    (
        pact.upon_receiving("an ask config request forwarded by the gateway")
        .with_request("GET", "/config")
        .will_respond_with(200)
        .with_header("Content-Type", "application/json", part="Response")
        .with_body(
            {
                "providers": [{"name": "ollama", "models": ["gemma3"], "default": True}],
                "models": {"ollama": ["gemma3"]},
                "defaultProvider": "ollama",
                "defaultModel": "gemma3",
            },
            content_type="application/json",
            part="Response",
        )
    )

    with pact.serve(raises=True, verbose=False) as mock_agent:
        with _build_gateway_ask_client(mock_agent.url, monkeypatch) as gateway_client:
            ask = gateway_client.get(
                "/api/v1/ask",
                params={
                    "question": "what is vecinita?",
                    "thread_id": "thread-1",
                    "lang": "en",
                    "provider": "ollama",
                    "model": "gemma3",
                },
                headers={"Accept": "application/json"},
            )
            assert ask.status_code == 200
            assert ask.json()["answer"] == "Vecinita is a community-oriented retrieval assistant."

            config = gateway_client.get("/api/v1/ask/config")
            assert config.status_code == 200
            assert config.json()["defaultProvider"] == "ollama"

    pact.write_file(_pact_output_dir(), overwrite=True)
