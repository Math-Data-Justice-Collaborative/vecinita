"""HTTP client for Modal Ollama model list + pull API (RD-140-141)."""

from __future__ import annotations

import os
from http import HTTPStatus
from typing import Final, Protocol

import httpx
from vecinita_shared_schemas.ollama_models import (
    OllamaModelListResponse,
    OllamaModelPullRequest,
    OllamaModelPullResponse,
)

_ENV_OLLAMA_URL: Final[str] = "VECINITA_MODAL_OLLAMA_URL"
_ENV_PROXY_KEY: Final[str] = "VECINITA_MODAL_PROXY_KEY"


class OllamaModelsClientError(RuntimeError):
    """Raised when Modal Ollama model API requests fail."""


class OllamaModelsClientProtocol(Protocol):
    """List and pull Ollama models on Modal (mockable in tests)."""

    def list_models(self) -> OllamaModelListResponse: ...  # noqa: D102

    def start_pull(self, model_id: str) -> OllamaModelPullResponse: ...  # noqa: D102

    def close(self) -> None: ...  # noqa: D102


class OllamaModelsClient:
    """Proxy to vecinita-ollama Modal ASGI routes."""

    def __init__(
        self,
        base_url: str | None = None,
        proxy_key: str | None = None,
        *,
        http_client: httpx.Client | None = None,
        timeout: float = 120.0,
    ) -> None:
        """Resolve Modal Ollama URL and proxy key from args or environment."""
        resolved_url = base_url or os.environ.get(_ENV_OLLAMA_URL)
        resolved_key = proxy_key or os.environ.get(_ENV_PROXY_KEY)
        if not resolved_url or not resolved_key:
            msg = f"{_ENV_OLLAMA_URL} and {_ENV_PROXY_KEY} are required"
            raise OllamaModelsClientError(msg)
        self._base_url = resolved_url.rstrip("/")
        self._proxy_key = resolved_key
        self._owns = http_client is None
        self._client = http_client or httpx.Client(base_url=self._base_url, timeout=timeout)

    def close(self) -> None:
        """Close the owned HTTP client when this wrapper created it."""
        if self._owns:
            self._client.close()

    def list_models(self) -> OllamaModelListResponse:
        """Fetch models stashed on the Modal Ollama volume."""
        response = self._client.get(
            "/models/ollama",
            headers={"X-Vecinita-Proxy-Key": self._proxy_key},
        )
        if response.status_code >= HTTPStatus.BAD_REQUEST:
            msg = f"list_models failed: {response.status_code} {response.text}"
            raise OllamaModelsClientError(msg)
        return OllamaModelListResponse.model_validate(response.json())

    def start_pull(self, model_id: str) -> OllamaModelPullResponse:
        """Enqueue a background pull for a missing Ollama model tag."""
        body = OllamaModelPullRequest(model_id=model_id)
        response = self._client.post(
            "/models/ollama/pull",
            json=body.model_dump(mode="json"),
            headers={"X-Vecinita-Proxy-Key": self._proxy_key},
        )
        if response.status_code >= HTTPStatus.BAD_REQUEST:
            msg = f"start_pull failed: {response.status_code} {response.text}"
            raise OllamaModelsClientError(msg)
        return OllamaModelPullResponse.model_validate(response.json())
