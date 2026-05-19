"""HTTP client for vecinita-llm Modal app."""

from __future__ import annotations

import json
import os
from collections.abc import Iterator
from typing import Final

import httpx

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
        resolved = base_url or os.environ.get(_ENV_LLM_URL)
        if not resolved:
            raise LlmClientError(f"{_ENV_LLM_URL} or base_url is required")
        self._base_url = resolved.rstrip("/")
        self._owns_client = http_client is None
        self._client = http_client or httpx.Client(base_url=self._base_url, timeout=timeout)

    def close(self) -> None:
        if self._owns_client:
            self._client.close()

    def __enter__(self) -> LlmClient:
        return self

    def __exit__(self, *args: object) -> None:
        self.close()

    def generate(
        self,
        prompt: str,
        *,
        max_tokens: int = 512,
        temperature: float = 0.2,
    ) -> str:
        response = self._client.post(
            "/generate",
            json={
                "prompt": prompt,
                "max_tokens": max_tokens,
                "temperature": temperature,
            },
        )
        if response.status_code >= 400:
            raise LlmClientError(
                f"generate failed with status {response.status_code}: {response.text}"
            )
        data = response.json()
        text = data.get("text")
        if not isinstance(text, str):
            raise LlmClientError("generate response missing 'text' string")
        return text

    def generate_stream(
        self,
        prompt: str,
        *,
        max_tokens: int = 512,
        temperature: float = 0.2,
    ) -> Iterator[str]:
        with self._client.stream(
            "POST",
            "/generate/stream",
            json={
                "prompt": prompt,
                "max_tokens": max_tokens,
                "temperature": temperature,
            },
        ) as response:
            if response.status_code >= 400:
                raise LlmClientError(
                    f"generate_stream failed with status {response.status_code}"
                )
            for line in response.iter_lines():
                if not line or not line.startswith("data: "):
                    continue
                payload = json.loads(line.removeprefix("data: ").strip())
                if payload.get("done"):
                    break
                token = payload.get("token")
                if isinstance(token, str) and token:
                    yield token
