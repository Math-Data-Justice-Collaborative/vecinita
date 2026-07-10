"""HTTP client for vecinita-llm Modal app (ADR-037 unified LLM surface)."""

from __future__ import annotations

import json
from http import HTTPStatus
from typing import TYPE_CHECKING, Self, cast

import httpx
from vecinita_shared_schemas.json_types import as_json_object
from vecinita_shared_schemas.llm_http import (
    LlmHttpConfigError,
    resolve_llm_http_config,
)
from vecinita_shared_schemas.playground_models import (
    PlaygroundModelListResponse,
    PlaygroundModelPullRequest,
    PlaygroundModelPullResponse,
)

if TYPE_CHECKING:
    from collections.abc import Iterator

_PROXY_HEADER = "X-Vecinita-Proxy-Key"


class LlmClientError(RuntimeError):
    """LLM service request or response validation failed."""


class LlmClient:
    """Call Modal ``vecinita-llm`` generate/stream/warm and model list/pull endpoints."""

    def __init__(  # noqa: PLR0913  # shared resolver surface: url/proxy/timeout/model/http
        self,
        base_url: str | None = None,
        *,
        model_id: str | None = None,
        proxy_key: str | None = None,
        timeout: float = 120.0,
        http_client: httpx.Client | None = None,
        require_proxy_key: bool = False,
    ) -> None:
        """Initialize the client from ``base_url`` or ``VECINITA_MODAL_LLM_URL``."""
        try:
            config = resolve_llm_http_config(
                base_url=base_url,
                proxy_key=proxy_key,
                timeout=timeout,
                model_id=model_id,
                require_proxy_key=require_proxy_key,
            )
        except LlmHttpConfigError as exc:
            raise LlmClientError(str(exc)) from exc
        self._base_url = config.base_url
        self._model_id = config.model_id
        self._proxy_key = config.proxy_key
        self._owns_client = http_client is None
        self._client = http_client or httpx.Client(
            base_url=self._base_url,
            timeout=config.timeout,
            follow_redirects=True,
        )

    def close(self) -> None:
        """Close the underlying HTTP client when owned by this instance."""
        if self._owns_client:
            self._client.close()

    @property
    def default_model_id(self) -> str | None:
        """Configured default playground model tag, if any."""
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
        if resolved_model:
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
        """Best-effort POST ``/warm`` to preload the model and reduce cold-start latency."""
        body = {"model_id": self._model_id} if self._model_id else {}
        self._client.post("/warm", json=body, headers=self._request_headers())

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

    def list_models(self) -> PlaygroundModelListResponse:
        """Fetch models staged on the Modal llm-models volume (path alias ``/models/ollama``)."""
        response = self._client.get(
            "/models/ollama",
            headers=self._request_headers(),
        )
        if response.status_code >= HTTPStatus.BAD_REQUEST:
            msg = f"list_models failed: {response.status_code} {response.text}"
            raise LlmClientError(msg)
        return PlaygroundModelListResponse.model_validate(response.json())

    def start_pull(self, model_id: str) -> PlaygroundModelPullResponse:
        """Enqueue a background HF download for a playground model tag."""
        body = PlaygroundModelPullRequest(model_id=model_id)
        response = self._client.post(
            "/models/ollama/pull",
            json=body.model_dump(mode="json"),
            headers=self._request_headers(),
        )
        if response.status_code >= HTTPStatus.BAD_REQUEST:
            msg = f"start_pull failed: {response.status_code} {response.text}"
            raise LlmClientError(msg)
        return PlaygroundModelPullResponse.model_validate(response.json())
