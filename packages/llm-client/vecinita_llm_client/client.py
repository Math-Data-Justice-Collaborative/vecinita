"""HTTP client for vecinita-llm Modal app."""

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


class LlmClientError(RuntimeError):
    """LLM service request or response validation failed."""


class LlmClient:
    """Call vecinita-llm `/generate` and `/generate/stream` endpoints."""

    def __init__(
        self,
        base_url: str | None = None,
        *,
        timeout: float = 120.0,
        http_client: httpx.Client | None = None,
    ) -> None:
        """Initialize the client from ``base_url`` or ``VECINITA_MODAL_LLM_URL``."""
        resolved = base_url or os.environ.get(_ENV_LLM_URL)
        if not resolved:
            msg = f"{_ENV_LLM_URL} or base_url is required"
            raise LlmClientError(msg)
        self._base_url = resolved.rstrip("/")
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

    def __enter__(self) -> Self:
        """Return this client for use as a context manager."""
        return self

    def __exit__(self, *args: object) -> None:
        """Close the client on context manager exit."""
        self.close()

    def generate(
        self,
        prompt: str,
        *,
        max_tokens: int = 512,
        temperature: float = 0.2,
    ) -> str:
        """Generate a completion for ``prompt`` and return the full text."""
        response = self._client.post(
            "/generate",
            json={
                "prompt": prompt,
                "max_tokens": max_tokens,
                "temperature": temperature,
            },
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

    def generate_stream(
        self,
        prompt: str,
        *,
        max_tokens: int = 512,
        temperature: float = 0.2,
    ) -> Iterator[str]:
        """Stream completion tokens for ``prompt`` as they are generated."""
        with self._client.stream(
            "POST",
            "/generate/stream",
            json={
                "prompt": prompt,
                "max_tokens": max_tokens,
                "temperature": temperature,
            },
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
