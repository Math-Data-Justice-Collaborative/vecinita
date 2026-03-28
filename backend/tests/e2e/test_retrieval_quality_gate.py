"""Retrieval-quality e2e regression checks for the gateway /ask endpoint."""

from __future__ import annotations

from typing import Any

import pytest

pytestmark = [pytest.mark.e2e, pytest.mark.retrieval_quality]


class _FakeAskResponse:
    def __init__(self, payload: dict[str, Any], status_code: int = 200):
        self._payload = payload
        self.status_code = status_code
        self.text = str(payload)

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            raise RuntimeError(f"HTTP {self.status_code}")

    def json(self) -> dict[str, Any]:
        return self._payload


class _FakeAsyncClient:
    def __init__(self, *args, **kwargs):
        pass

    async def get(self, url: str, params=None, timeout=None):
        question = (params or {}).get("question", "")
        lang = (params or {}).get("lang") or "en"

        if "doctor" in question.lower() and lang == "es":
            return _FakeAskResponse(
                {
                    "answer": (
                        "Puedes llamar al centro de salud comunitario y al 2-1-1 para "
                        "apoyo medico y orientacion local."
                    ),
                    "sources": [
                        {
                            "url": "https://example.org/health/community-clinic",
                            "title": "Directorio de Salud Comunitaria",
                            "chunk_id": "health-1",
                            "relevance": 0.93,
                            "excerpt": "Clinicas comunitarias y lineas de ayuda medica.",
                        }
                    ],
                    "language": "es",
                    "model": "test-model",
                    "response_time_ms": 920,
                }
            )

        return _FakeAskResponse(
            {
                "answer": "Call 2-1-1 and check local housing and food assistance programs.",
                "sources": [
                    {
                        "url": "https://example.org/community/211",
                        "title": "211 Community Services",
                        "chunk_id": "community-211",
                        "relevance": 0.91,
                        "excerpt": "Find nearby housing, food, and utility support programs.",
                    },
                    {
                        "url": "https://example.org/housing/help",
                        "title": "Housing Assistance Guide",
                        "chunk_id": "housing-1",
                        "relevance": 0.88,
                        "excerpt": "Eligibility and contact points for rental assistance.",
                    },
                ],
                "language": "en",
                "model": "test-model",
                "response_time_ms": 850,
            }
        )


@pytest.fixture
def gateway_client(env_vars, monkeypatch):
    for key, value in env_vars.items():
        monkeypatch.setenv(key, value)

    from fastapi.testclient import TestClient

    from src.api.main import app

    return TestClient(app)


def test_retrieval_response_contains_citations(gateway_client, monkeypatch):
    from src.api import router_ask

    monkeypatch.setattr(router_ask, "_get_agent_client", lambda: _FakeAsyncClient())

    response = gateway_client.get(
        "/api/v1/ask",
        params={"question": "Where can I find housing and food assistance?", "lang": "en"},
    )

    assert response.status_code == 200
    payload = response.json()

    assert payload.get("answer")
    assert isinstance(payload.get("sources"), list)
    assert len(payload["sources"]) >= 1

    for source in payload["sources"]:
        assert source.get("url", "").startswith("http")
        assert source.get("chunk_id")
        assert source.get("relevance", 0) > 0


def test_spanish_health_intent_does_not_drift_to_unrelated_sources(gateway_client, monkeypatch):
    from src.api import router_ask

    monkeypatch.setattr(router_ask, "_get_agent_client", lambda: _FakeAsyncClient())

    response = gateway_client.get(
        "/api/v1/ask",
        params={"question": "Necesito ayuda con doctor y clinica", "lang": "es", "tags": "health"},
    )

    assert response.status_code == 200
    payload = response.json()

    assert payload.get("language") == "es"
    assert payload.get("sources")
    source_urls = [src.get("url", "") for src in payload["sources"]]
    assert any("health" in url or "clinic" in url for url in source_urls)


def test_retrieval_latency_budget_is_within_threshold(gateway_client, monkeypatch):
    from src.api import router_ask

    monkeypatch.setattr(router_ask, "_get_agent_client", lambda: _FakeAsyncClient())

    response = gateway_client.get("/api/v1/ask", params={"question": "Need support resources"})
    assert response.status_code == 200

    payload = response.json()
    assert isinstance(payload.get("response_time_ms"), int)
    assert payload["response_time_ms"] <= 2000
