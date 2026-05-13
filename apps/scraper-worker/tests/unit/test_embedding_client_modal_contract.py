"""Contract: ``EmbeddingClient`` Modal-aware paths used by scraper workers (``_modal_request``)."""

from __future__ import annotations

import sys
import types
from typing import Any

import pytest

from vecinita_scraper.clients.embedding_client import EmbeddingClient


def _modal_stub_config(
    *,
    app_name: str = "vecinita-embedding",
    single_fn: str = "embed_query",
    batch_fn: str = "embed_batch",
    env_name: str = "",
) -> Any:
    return types.SimpleNamespace(
        modal_function_invocation=True,
        modal_embedding_app_name=app_name,
        modal_embedding_single_function=single_fn,
        modal_embedding_batch_function=batch_fn,
        modal_environment_name=env_name,
    )


@pytest.mark.unit
@pytest.mark.contract
@pytest.mark.asyncio
async def test_modal_get_root_embed_query_health(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Config probe: ``GET /`` calls ``embed_query`` with the ``health`` literal."""
    calls: list[tuple[str, Any]] = []

    class _Remote:
        async def aio(self, arg: Any) -> dict[str, Any]:
            calls.append(("embed_query", arg))
            return {"model": "probe-model", "dimension": 512}

    class _Fn:
        remote = _Remote()

    def _from_name(app: str, name: str, environment_name: str | None = None) -> _Fn:
        assert app == "vecinita-embedding"
        assert name == "embed_query"
        return _Fn()

    modal_stub = types.SimpleNamespace(Function=types.SimpleNamespace(from_name=_from_name))
    monkeypatch.setitem(sys.modules, "modal", modal_stub)
    monkeypatch.setattr(
        "vecinita_scraper.clients.embedding_client._api_config",
        lambda: _modal_stub_config(),
    )

    client = EmbeddingClient(base_url="https://embedding-ignored.example")
    payload = await client._request("GET", "/")

    assert calls == [("embed_query", "health")]
    assert payload["model"] == "probe-model"
    assert payload["dimensions"] == 512
    assert payload["embedding_dimensions"] == 512


@pytest.mark.unit
@pytest.mark.contract
@pytest.mark.asyncio
async def test_modal_post_batch_embed_batch_queries(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """``POST /embed/batch`` calls ``embed_batch`` with the query strings list."""
    calls: list[Any] = []

    class _Remote:
        async def aio(self, queries: Any) -> dict[str, Any]:
            calls.append(queries)
            return {"embeddings": [[1.0, 0.0], [0.0, 1.0]], "model": "m", "dimension": 2}

    class _Fn:
        remote = _Remote()

    def _from_name(app: str, name: str, environment_name: str | None = None) -> _Fn:
        assert name == "embed_batch"
        return _Fn()

    modal_stub = types.SimpleNamespace(Function=types.SimpleNamespace(from_name=_from_name))
    monkeypatch.setitem(sys.modules, "modal", modal_stub)
    monkeypatch.setattr(
        "vecinita_scraper.clients.embedding_client._api_config",
        lambda: _modal_stub_config(),
    )

    client = EmbeddingClient(base_url="https://embedding-ignored.example")
    out = await client._request("POST", "/embed/batch", json={"queries": ["a", "b"], "model": None})

    assert calls == [["a", "b"]]
    assert out["dimensions"] == 2
    assert "dimension" in out
    assert len(out["embeddings"]) == 2


@pytest.mark.unit
@pytest.mark.contract
@pytest.mark.asyncio
async def test_modal_request_rejects_unsupported_shape(monkeypatch: pytest.MonkeyPatch) -> None:
    from vecinita_scraper.core.errors import EmbeddingError

    modal_stub = types.SimpleNamespace(
        Function=types.SimpleNamespace(from_name=lambda *a, **k: object()),
    )
    monkeypatch.setitem(sys.modules, "modal", modal_stub)
    monkeypatch.setattr(
        "vecinita_scraper.clients.embedding_client._api_config",
        lambda: _modal_stub_config(),
    )

    client = EmbeddingClient(base_url="https://embedding-ignored.example")
    with pytest.raises(EmbeddingError, match="Unsupported modal embedding request"):
        await client._request("DELETE", "/embed/batch", json={})
