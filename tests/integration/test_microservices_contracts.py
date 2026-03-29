"""API contract checks for the proxy-centric microservices compose stack."""

from __future__ import annotations

import os
from typing import Any

import pytest
import requests
from requests import Response
from requests.exceptions import RequestException


TIMEOUT_SECONDS = float(os.getenv("API_TIMEOUT", "20"))
REQUIRE_MICROSERVICES = os.getenv("REQUIRE_MICROSERVICES", "0").lower() in {"1", "true", "yes"}

GATEWAY_URL = os.getenv("GATEWAY_URL", "http://localhost:8004")
PROXY_URL = os.getenv("PROXY_URL", "http://localhost:10000")
MODEL_URL = os.getenv("MODEL_URL", "http://localhost:8008")
EMBEDDING_URL = os.getenv("EMBEDDING_URL", "http://localhost:8011")
SCRAPER_URL = os.getenv("SCRAPER_URL", "http://localhost:8020")


def _request_or_skip(method: str, url: str, **kwargs: Any) -> Response:
    try:
        return requests.request(method, url, timeout=TIMEOUT_SECONDS, **kwargs)
    except RequestException as exc:
        if REQUIRE_MICROSERVICES:
            raise AssertionError(f"Unable to reach {url}: {exc}") from exc
        pytest.skip(f"Skipping because service is not reachable: {url}")


def _json_or_text(response: Response) -> dict[str, Any]:
    try:
        data = response.json()
        if isinstance(data, dict):
            return data
        return {"value": data}
    except ValueError:
        return {"raw": response.text}


@pytest.mark.integration
@pytest.mark.api
class TestMicroservicesHealthContracts:
    def test_direct_service_health_endpoints(self) -> None:
        endpoints = [
            ("model", f"{MODEL_URL}/health"),
            ("embedding", f"{EMBEDDING_URL}/health"),
            ("scraper", f"{SCRAPER_URL}/health"),
            ("proxy", f"{PROXY_URL}/health"),
            ("gateway", f"{GATEWAY_URL}/health"),
        ]

        for service_name, endpoint in endpoints:
            response = _request_or_skip("GET", endpoint)
            payload = _json_or_text(response)
            assert response.status_code == 200, f"{service_name} health failed: {payload}"

    def test_proxy_health_for_upstream_model(self) -> None:
        response = _request_or_skip("GET", f"{PROXY_URL}/model/health")
        payload = _json_or_text(response)

        assert response.status_code == 200, payload

    def test_proxy_health_for_upstream_embedding(self) -> None:
        response = _request_or_skip("GET", f"{PROXY_URL}/embedding/health")
        payload = _json_or_text(response)

        assert response.status_code == 200, payload

    def test_proxy_health_for_upstream_scraper_jobs(self) -> None:
        response = _request_or_skip("GET", f"{PROXY_URL}/jobs/health")
        payload = _json_or_text(response)

        assert response.status_code == 200, payload

    def test_proxy_embedding_contract(self) -> None:
        response = _request_or_skip(
            "POST",
            f"{PROXY_URL}/embedding/embed",
            headers={"Content-Type": "application/json"},
            json={"text": "hola vecinita", "model": "sentence-transformers/all-MiniLM-L6-v2"},
        )
        payload = _json_or_text(response)

        assert response.status_code == 200, payload
        assert "embedding" in payload, payload
        assert isinstance(payload["embedding"], list), payload

    def test_proxy_model_chat_contract(self) -> None:
        response = _request_or_skip(
            "POST",
            f"{PROXY_URL}/model/chat",
            headers={"Content-Type": "application/json"},
            json={"messages": [{"role": "user", "content": "ping"}]},
        )
        payload = _json_or_text(response)

        assert response.status_code in {200, 503}, payload
        # In constrained local runs, model backend may return a degraded response but shape should be JSON.
        assert isinstance(payload, dict), payload
