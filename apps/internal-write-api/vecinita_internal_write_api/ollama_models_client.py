"""HTTP client for Modal LLM model list + pull API (ADR-037 — vecinita-llm)."""

from __future__ import annotations

import logging
import os
from http import HTTPStatus
from typing import Final, Protocol

import httpx
from vecinita_shared_schemas.ollama_models import (
    OllamaModelListResponse,
    OllamaModelPullRequest,
    OllamaModelPullResponse,
)

logger = logging.getLogger(__name__)

_ENV_LLM_URL: Final[str] = "VECINITA_MODAL_LLM_URL"
_ENV_OLLAMA_URL: Final[str] = "VECINITA_MODAL_OLLAMA_URL"
_ENV_PROXY_KEY: Final[str] = "VECINITA_MODAL_PROXY_KEY"


class OllamaModelsClientError(RuntimeError):
    """Raised when Modal LLM model API requests fail."""


class OllamaModelsClientProtocol(Protocol):
    """List and pull playground models on Modal (mockable in tests)."""

    def list_models(self) -> OllamaModelListResponse: ...  # noqa: D102

    def start_pull(self, model_id: str) -> OllamaModelPullResponse: ...  # noqa: D102

    def close(self) -> None: ...  # noqa: D102


class OllamaModelsClient:
    """Proxy to vecinita-llm Modal ASGI model routes (path compat: /models/ollama)."""

    def __init__(
        self,
        base_url: str | None = None,
        proxy_key: str | None = None,
        *,
        http_client: httpx.Client | None = None,
        timeout: float = 120.0,
    ) -> None:
        """Resolve Modal LLM URL and proxy key from args or environment."""
        legacy_ollama = os.environ.get(_ENV_OLLAMA_URL)
        if legacy_ollama:
            logger.warning(
                "%s is deprecated (ADR-037); use %s only",
                _ENV_OLLAMA_URL,
                _ENV_LLM_URL,
            )
        resolved_url = base_url or os.environ.get(_ENV_LLM_URL) or legacy_ollama
        resolved_key = proxy_key or os.environ.get(_ENV_PROXY_KEY)
        if not resolved_url or not resolved_key:
            msg = f"{_ENV_LLM_URL} and {_ENV_PROXY_KEY} are required"
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
        """Fetch models staged on the Modal llm-models volume."""
        response = self._client.get(
            "/models/ollama",
            headers={"X-Vecinita-Proxy-Key": self._proxy_key},
        )
        if response.status_code >= HTTPStatus.BAD_REQUEST:
            msg = f"list_models failed: {response.status_code} {response.text}"
            raise OllamaModelsClientError(msg)
        return OllamaModelListResponse.model_validate(response.json())

    def start_pull(self, model_id: str) -> OllamaModelPullResponse:
        """Enqueue a background HF download for a playground model tag."""
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
