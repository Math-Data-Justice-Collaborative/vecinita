"""Unit tests for Modal Ollama models HTTP client (RD-140-141)."""

from __future__ import annotations

import json as json_lib
from typing import cast
from unittest.mock import patch
from uuid import uuid4

import httpx
import pytest
from vecinita_internal_write_api.ollama_models_client import (
    OllamaModelsClient,
    OllamaModelsClientError,
)
from vecinita_shared_schemas.json_types import as_json_object


def test_client_requires_url_and_proxy_key(monkeypatch: pytest.MonkeyPatch) -> None:
    """Constructor raises when Modal Ollama env vars are missing."""
    monkeypatch.delenv("VECINITA_MODAL_OLLAMA_URL", raising=False)
    monkeypatch.delenv("VECINITA_MODAL_PROXY_KEY", raising=False)
    with pytest.raises(OllamaModelsClientError, match="VECINITA_MODAL_OLLAMA_URL"):
        OllamaModelsClient()


def test_list_models_returns_parsed_response() -> None:
    """list_models GETs /models/ollama with proxy auth."""

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/models/ollama"
        assert request.headers.get("X-Vecinita-Proxy-Key") == "proxy-secret"
        return httpx.Response(
            200,
            json={"items": [{"model_id": "qwen2.5:1.5b-instruct", "available": True}]},
        )

    transport = httpx.MockTransport(handler)
    client = OllamaModelsClient(
        base_url="http://ollama.test/",
        proxy_key="proxy-secret",
        http_client=httpx.Client(transport=transport, base_url="http://ollama.test"),
    )
    listing = client.list_models()
    assert listing.items[0].model_id == "qwen2.5:1.5b-instruct"
    client.close()


def test_list_models_raises_on_http_error() -> None:
    """list_models wraps non-2xx responses as OllamaModelsClientError."""

    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(503, text="upstream unavailable")

    transport = httpx.MockTransport(handler)
    client = OllamaModelsClient(
        base_url="http://ollama.test",
        proxy_key="proxy-secret",
        http_client=httpx.Client(transport=transport, base_url="http://ollama.test"),
    )
    with pytest.raises(OllamaModelsClientError, match="list_models failed"):
        client.list_models()
    client.close()


def test_start_pull_posts_model_id() -> None:
    """start_pull POSTs /models/ollama/pull with the requested model id."""
    job_id = uuid4()

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/models/ollama/pull"
        payload = as_json_object(cast("object", json_lib.loads(request.content.decode())))
        assert payload["model_id"] == "mistral:7b"
        return httpx.Response(
            202,
            json={
                "job_id": str(job_id),
                "model_id": "mistral:7b",
                "status": "pulling",
            },
        )

    transport = httpx.MockTransport(handler)
    client = OllamaModelsClient(
        base_url="http://ollama.test",
        proxy_key="proxy-secret",
        http_client=httpx.Client(transport=transport, base_url="http://ollama.test"),
    )
    response = client.start_pull("mistral:7b")
    assert response.job_id == job_id
    assert response.status == "pulling"
    client.close()


def test_start_pull_raises_on_http_error() -> None:
    """start_pull wraps non-2xx responses as OllamaModelsClientError."""

    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(500, text="pull failed")

    transport = httpx.MockTransport(handler)
    client = OllamaModelsClient(
        base_url="http://ollama.test",
        proxy_key="proxy-secret",
        http_client=httpx.Client(transport=transport, base_url="http://ollama.test"),
    )
    with pytest.raises(OllamaModelsClientError, match="start_pull failed"):
        client.start_pull("missing:tag")
    client.close()


def test_close_closes_owned_http_client() -> None:
    """close() closes internally created httpx clients."""
    closed: list[bool] = []

    class TrackingClient(httpx.Client):
        def close(self) -> None:
            closed.append(True)
            super().close()

    def tracking_client_factory(**kwargs: object) -> TrackingClient:
        base_url = kwargs.get("base_url")
        return TrackingClient(base_url=str(base_url) if base_url is not None else "http://ollama.test")

    with patch(
        "vecinita_internal_write_api.ollama_models_client.httpx.Client",
        side_effect=tracking_client_factory,
    ):
        client = OllamaModelsClient(
            base_url="http://ollama.test",
            proxy_key="proxy-secret",
        )
        client.close()
    assert closed == [True]


def test_close_skips_externally_owned_http_client() -> None:
    """close() only closes clients created by OllamaModelsClient itself."""
    closed: list[bool] = []

    class TrackingClient(httpx.Client):
        def close(self) -> None:
            closed.append(True)
            super().close()

    tracking = TrackingClient(base_url="http://ollama.test")
    wrapper = OllamaModelsClient(
        base_url="http://ollama.test",
        proxy_key="proxy-secret",
        http_client=tracking,
    )
    wrapper.close()
    assert closed == []
