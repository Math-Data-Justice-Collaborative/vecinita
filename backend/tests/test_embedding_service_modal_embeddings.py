"""Unit tests for ModalSdkEmbeddings."""

from __future__ import annotations

import pytest

from src.embedding_service.modal_embeddings import ModalSdkEmbeddings

pytestmark = pytest.mark.unit


def test_base_url_defaults_to_modal_scheme(monkeypatch):
    monkeypatch.setenv("MODAL_EMBEDDING_APP_NAME", "vecinita-embedding")
    emb = ModalSdkEmbeddings()
    assert emb.base_url == "modal://vecinita-embedding/embed_query"


def test_validate_connection_calls_embed_query(monkeypatch):
    monkeypatch.setattr(
        "src.embedding_service.modal_embeddings.invoke_modal_embedding_single",
        lambda _text: {"embedding": [0.1], "model": "m", "dimension": 1},
    )
    emb = ModalSdkEmbeddings(logical_url="modal://test/embed_query")
    assert emb.validate_connection() == "modal://test/embed_query"


def test_embed_query_returns_embedding(monkeypatch):
    monkeypatch.setattr(
        "src.embedding_service.modal_embeddings.invoke_modal_embedding_single",
        lambda _text: {"embedding": [0.1, 0.2]},
    )
    emb = ModalSdkEmbeddings()
    assert emb.embed_query("hello") == [0.1, 0.2]


def test_embed_query_raises_when_embedding_missing(monkeypatch):
    monkeypatch.setattr(
        "src.embedding_service.modal_embeddings.invoke_modal_embedding_single",
        lambda _text: {"model": "m"},
    )
    emb = ModalSdkEmbeddings()
    with pytest.raises(RuntimeError, match="no embedding list"):
        emb.embed_query("hello")


def test_embed_documents_returns_empty_for_empty_input():
    emb = ModalSdkEmbeddings()
    assert emb.embed_documents([]) == []


def test_embed_documents_returns_embeddings(monkeypatch):
    monkeypatch.setattr(
        "src.embedding_service.modal_embeddings.invoke_modal_embedding_batch",
        lambda _texts: {"embeddings": [[1.0], [2.0]]},
    )
    emb = ModalSdkEmbeddings()
    assert emb.embed_documents(["a", "b"]) == [[1.0], [2.0]]


def test_embed_documents_raises_when_embeddings_missing(monkeypatch):
    monkeypatch.setattr(
        "src.embedding_service.modal_embeddings.invoke_modal_embedding_batch",
        lambda _texts: {"model": "m"},
    )
    emb = ModalSdkEmbeddings()
    with pytest.raises(RuntimeError, match="no embeddings list"):
        emb.embed_documents(["a"])


@pytest.mark.asyncio
async def test_async_embed_query_delegates(monkeypatch):
    monkeypatch.setattr(
        "src.embedding_service.modal_embeddings.invoke_modal_embedding_single",
        lambda _text: {"embedding": [0.9]},
    )
    emb = ModalSdkEmbeddings()
    assert await emb.aembed_query("hello") == [0.9]


@pytest.mark.asyncio
async def test_async_embed_documents_delegates(monkeypatch):
    monkeypatch.setattr(
        "src.embedding_service.modal_embeddings.invoke_modal_embedding_batch",
        lambda _texts: {"embeddings": [[0.7]]},
    )
    emb = ModalSdkEmbeddings()
    assert await emb.aembed_documents(["x"]) == [[0.7]]
