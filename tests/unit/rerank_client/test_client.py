"""RerankClient HTTP contract (F45 / EV-029)."""

from __future__ import annotations

from http import HTTPStatus
from typing import TYPE_CHECKING

import httpx
from vecinita_rerank_client import RerankClient

if TYPE_CHECKING:
    import pytest


def test_score_pairs_does_not_send_modal_proxy_header(monkeypatch: pytest.MonkeyPatch) -> None:
    """Open rerank app rejects Modal-Proxy-Authorization (BUG-2026-08-24)."""
    monkeypatch.setenv("VECINITA_MODAL_PROXY_KEY", "secret-proxy-key")
    seen_headers: dict[str, str] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        for key, value in request.headers.items():
            seen_headers[key.lower()] = value
        return httpx.Response(
            HTTPStatus.OK,
            json={"scores": [0.9, 0.1]},
        )

    transport = httpx.MockTransport(handler)
    client = httpx.Client(base_url="http://rerank.test", transport=transport)
    rerank = RerankClient("http://rerank.test", http_client=client)
    scores = rerank.score_pairs("food pantry", ["food bank", "other"])
    assert scores == [0.9, 0.1]
    assert "modal-proxy-authorization" not in seen_headers
