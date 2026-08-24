"""HTTP client for Modal cross-encoder rerank service (F45 / EV-029)."""

from __future__ import annotations

import os
from http import HTTPStatus
from typing import TYPE_CHECKING, Final, Self, cast

import httpx
from vecinita_shared_schemas.json_types import as_json_object

if TYPE_CHECKING:
    from collections.abc import Sequence

_ENV_RERANK_URL: Final[str] = "VECINITA_MODAL_RERANK_URL"
_ENV_PROXY_KEY: Final[str] = "VECINITA_MODAL_PROXY_KEY"
_PROXY_HEADER: Final[str] = "Modal-Proxy-Authorization"


class RerankClientError(RuntimeError):
    """Rerank service request or response validation failed."""


class RerankClient:
    """Call vecinita-rerank Modal app ``/score`` endpoint."""

    def __init__(
        self,
        base_url: str | None = None,
        *,
        proxy_key: str | None = None,
        timeout: float = 60.0,
        http_client: httpx.Client | None = None,
    ) -> None:
        """Resolve base URL and optional proxy key; own httpx client unless injected."""
        resolved = base_url or os.environ.get(_ENV_RERANK_URL)
        if not resolved:
            msg = f"{_ENV_RERANK_URL} or base_url is required"
            raise RerankClientError(msg)
        self._base_url = resolved.rstrip("/")
        self._proxy_key = proxy_key if proxy_key is not None else os.environ.get(_ENV_PROXY_KEY)
        self._owns_client = http_client is None
        self._client = http_client or httpx.Client(
            base_url=self._base_url,
            timeout=timeout,
            follow_redirects=True,
        )

    def close(self) -> None:
        """Close owned httpx client."""
        if self._owns_client:
            self._client.close()

    def __enter__(self) -> Self:
        """Enter context manager."""
        return self

    def __exit__(self, *args: object) -> None:
        """Exit context manager and close owned client."""
        self.close()

    def _headers(self) -> dict[str, str]:
        if self._proxy_key:
            return {_PROXY_HEADER: self._proxy_key}
        return {}

    def score_pairs(self, query: str, passages: Sequence[str]) -> list[float]:
        """Score query/passage pairs; return one float per passage (aligned order)."""
        if not passages:
            return []
        response = self._client.post(
            "/score",
            json={"query": query, "passages": list(passages)},
            headers=self._headers(),
        )
        if response.status_code != HTTPStatus.OK:
            msg = f"/score returned {response.status_code}: {response.text[:200]}"
            raise RerankClientError(msg)
        data = as_json_object(cast("object", response.json()))
        scores_obj = data.get("scores")
        if not isinstance(scores_obj, list):
            msg = "score response missing 'scores' list"
            raise RerankClientError(msg)
        scores = [
            float(cast("int | float", score_item))
            for score_item in cast("list[object]", scores_obj)
        ]
        if len(scores) != len(passages):
            msg = f"score count {len(scores)} != passage count {len(passages)}"
            raise RerankClientError(msg)
        return scores
