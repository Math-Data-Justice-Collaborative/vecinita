"""HTTP client for vecinita-llm and vecinita-ollama Modal apps."""

from __future__ import annotations

import json
import os
from http import HTTPStatus
from typing import TYPE_CHECKING, Final, Self, cast

import httpx
from vecinita_shared_schemas.json_types import as_json_object

if TYPE_CHECKING:
    from collections.abc import Iterator

_ENV_LLM_URL: Final[str] = "VECINITA_MODAL_LLM_URL"
_ENV_OLLAMA_URL: Final[str] = "VECINITA_MODAL_OLLAMA_URL"
_ENV_PROXY_KEY: Final[str] = "VECINITA_MODAL_PROXY_KEY"
_ENV_OLLAMA_MODEL_ID: Final[str] = "VECINITA_OLLAMA_MODEL_ID"
_PROXY_HEADER: Final[str] = "X-Vecinita-Proxy-Key"


class LlmClientError(RuntimeError):
    """LLM service request or response validation failed."""


class LlmClient:
    """Call Modal `/generate` and `/generate/stream` endpoints (vLLM or Ollama)."""

    def __init__(
        self,
        base_url: str | None = None,
        *,
        model_id: str | None = None,
        proxy_key: str | None = None,
        timeout: float = 120.0,
        http_client: httpx.Client | None = None,
    ) -> None:
        """Initialize the client from ``base_url`` or ``VECINITA_MODAL_*_URL`` env vars."""
        resolved = base_url or os.environ.get(_ENV_OLLAMA_URL) or os.environ.get(_ENV_LLM_URL)
        if not resolved:
            msg = f"{_ENV_OLLAMA_URL}, {_ENV_LLM_URL}, or base_url is required"
            raise LlmClientError(msg)
        self._base_url = resolved.rstrip("/")
        self._model_id = model_id or os.environ.get(_ENV_OLLAMA_MODEL_ID)
        self._proxy_key = proxy_key or os.environ.get(_ENV_PROXY_KEY)
        self._owns_client = http_client is None
        self._client = http_client or httpx.Client(
            base_url=self._base_url,
            timeout=timeout,
            follow_redirects=True,
        )

    def close(self) -> None:
        """Close the underlying HTTP client when owned by this instance."""
        if self._owns_client:
            self._client.close()

    @property
    def default_model_id(self) -> str | None:
        """Configured default Ollama model tag, if any."""
        return self._model_id

    def __enter__(self) -> Self:
        """Return this client for use as a context manager."""
        return self

    def __exit__(self, *args: object) -> None:
        """Close the client on context manager exit."""
        self.close()

    def _request_headers(self) -> dict[str, str]:
        if self._proxy_key:
            return {_PROXY_HEADER: self._proxy_key}
        return {}

    def _supports_model_id_in_body(self) -> bool:
        """Ollama `/generate` accepts model_id; vecinita-llm (vLLM) rejects it."""
        ollama_url = os.environ.get(_ENV_OLLAMA_URL)
        if not ollama_url:
            return False
        return self._base_url.rstrip("/") == ollama_url.rstrip("/")

    def _generate_body(
        self,
        prompt: str,
        *,
        max_tokens: int,
        temperature: float,
        model_id: str | None,
    ) -> dict[str, object]:
        body: dict[str, object] = {
            "prompt": prompt,
            "max_tokens": max_tokens,
            "temperature": temperature,
        }
        resolved_model = model_id or self._model_id
        if resolved_model and self._supports_model_id_in_body():
            body["model_id"] = resolved_model
        return body

    def generate(
        self,
        prompt: str,
        *,
        max_tokens: int = 512,
        temperature: float = 0.2,
        model_id: str | None = None,
    ) -> str:
        """Generate a completion for ``prompt`` and return the full text."""
        response = self._client.post(
            "/generate",
            json=self._generate_body(
                prompt,
                max_tokens=max_tokens,
                temperature=temperature,
                model_id=model_id,
            ),
            headers=self._request_headers(),
        )
        if response.status_code >= HTTPStatus.BAD_REQUEST:
            msg = f"generate failed with status {response.status_code}: {response.text}"
            raise LlmClientError(msg)
        data = as_json_object(cast("object", response.json()))
        text = data.get("text")
        if not isinstance(text, str):
            msg = "generate response missing 'text' string"
            raise LlmClientError(msg)
        return text

    def warm(self) -> None:
        """Best-effort POST ``/warm`` to reduce cold-start latency."""
        self._client.post("/warm", timeout=120.0, headers=self._request_headers())

    def generate_stream(
        self,
        prompt: str,
        *,
        max_tokens: int = 512,
        temperature: float = 0.2,
        model_id: str | None = None,
    ) -> Iterator[str]:
        """Stream completion tokens for ``prompt`` as they are generated."""
        with self._client.stream(
            "POST",
            "/generate/stream",
            json=self._generate_body(
                prompt,
                max_tokens=max_tokens,
                temperature=temperature,
                model_id=model_id,
            ),
            headers=self._request_headers(),
        ) as response:
            if response.status_code >= HTTPStatus.BAD_REQUEST:
                msg = f"generate_stream failed with status {response.status_code}"
                raise LlmClientError(msg)
            for line in response.iter_lines():
                if not line or not line.startswith("data: "):
                    continue
                payload = as_json_object(
                    cast("object", json.loads(line.removeprefix("data: ").strip()))
                )
                if payload.get("done"):
                    break
                token = payload.get("token")
                if isinstance(token, str) and token:
                    yield token
