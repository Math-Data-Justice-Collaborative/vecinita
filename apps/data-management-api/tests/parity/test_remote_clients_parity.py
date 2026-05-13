"""Parity anchors: service clients round-trip the same JSON as normalized fixtures (T021)."""

from __future__ import annotations

import json
from typing import Any

import httpx
import pytest

import service_clients.embedding_client as embedding_mod
import service_clients.model_client as model_mod
import service_clients.modal_invoker as modal_invoker_mod
import service_clients.scraper_client as scraper_mod

from service_clients.embedding_client import EmbeddingClient
from service_clients.model_client import ModelClient
from service_clients.scraper_client import ScraperClient


def _norm(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, default=str)


@pytest.mark.asyncio
async def test_scraper_response_matches_fixture(monkeypatch: pytest.MonkeyPatch) -> None:
    fixture = {"url": "https://example.com/p", "title": "T", "text": None, "metadata": {}}

    async def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=fixture)

    transport = httpx.MockTransport(handler)

    def _async_client(*, timeout: float = 60.0, **_kw: object) -> httpx.AsyncClient:
        return httpx.AsyncClient(transport=transport, timeout=timeout)

    monkeypatch.setattr(scraper_mod, "AsyncClient", _async_client)
    got = await ScraperClient("https://scraper").scrape("https://example.com/p")
    assert _norm(got.model_dump(mode="json")) == _norm(fixture)


@pytest.mark.asyncio
async def test_embedding_response_matches_fixture(monkeypatch: pytest.MonkeyPatch) -> None:
    fixture = {"embedding": [0.25, -0.25], "model_version": None}

    async def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=fixture)

    transport = httpx.MockTransport(handler)

    def _async_client(*, timeout: float = 60.0, **_kw: object) -> httpx.AsyncClient:
        return httpx.AsyncClient(transport=transport, timeout=timeout)

    monkeypatch.setattr(embedding_mod, "AsyncClient", _async_client)
    got = await EmbeddingClient("https://emb").embed("hello")
    assert _norm(got.model_dump(mode="json")) == _norm(fixture)


@pytest.mark.asyncio
async def test_model_response_matches_fixture(monkeypatch: pytest.MonkeyPatch) -> None:
    fixture = {"label": "housing_intake", "score": 0.9, "model_version": "v1"}

    async def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=fixture)

    transport = httpx.MockTransport(handler)

    def _async_client(*, timeout: float = 60.0, **_kw: object) -> httpx.AsyncClient:
        return httpx.AsyncClient(transport=transport, timeout=timeout)

    monkeypatch.setattr(model_mod, "AsyncClient", _async_client)
    got = await ModelClient("https://mdl").predict("tenant notice", model_version="v1")
    assert _norm(got.model_dump(mode="json")) == _norm(fixture)


@pytest.mark.asyncio
async def test_embedding_modal_branch_matches_http_fixture_shape(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fixture = {"embedding": [0.25, -0.25], "model_version": None}
    monkeypatch.setenv("MODAL_FUNCTION_INVOCATION", "1")
    monkeypatch.setenv("MODAL_TOKEN_ID", "id")
    monkeypatch.setenv("MODAL_TOKEN_SECRET", "secret")

    async def _fake_modal(_text: str, _mv: str | None) -> dict:
        return fixture

    monkeypatch.setattr(modal_invoker_mod, "embedding_embed_single_modal", _fake_modal)
    got = await EmbeddingClient("https://ignored").embed("hello")
    assert _norm(got.model_dump(mode="json")) == _norm(fixture)


@pytest.mark.asyncio
async def test_model_modal_branch_matches_http_fixture_shape(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fixture = {"label": "housing_intake", "score": 0.9, "model_version": "v1"}
    monkeypatch.setenv("MODAL_FUNCTION_INVOCATION", "1")
    monkeypatch.setenv("MODAL_TOKEN_ID", "id")
    monkeypatch.setenv("MODAL_TOKEN_SECRET", "secret")

    async def _fake_modal(_text: str, _mv: str | None) -> dict:
        return fixture

    monkeypatch.setattr(modal_invoker_mod, "model_predict_modal", _fake_modal)
    got = await ModelClient("https://ignored").predict("tenant notice", model_version="v1")
    assert _norm(got.model_dump(mode="json")) == _norm(fixture)
