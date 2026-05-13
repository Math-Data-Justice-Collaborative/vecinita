from __future__ import annotations

import sys
from types import ModuleType

from fastapi.testclient import TestClient

import vecinita.app as modal_app
from tests.fakes import FakeEmbedder
from vecinita.api import create_app
from vecinita.service import EmbeddingService


def test_create_text_embedding_uses_default_configuration(monkeypatch) -> None:
    captured: dict[str, str] = {}

    class FakeTextEmbedding:
        def __init__(self, model_name: str, cache_dir: str) -> None:
            captured["model_name"] = model_name
            captured["cache_dir"] = cache_dir

    fake_fastembed = ModuleType("fastembed")
    fake_fastembed.TextEmbedding = FakeTextEmbedding
    monkeypatch.setitem(sys.modules, "fastembed", fake_fastembed)

    model = modal_app.create_text_embedding()

    assert isinstance(model, FakeTextEmbedding)
    assert captured == {
        "model_name": modal_app.DEFAULT_MODEL,
        "cache_dir": modal_app.MODEL_DIR,
    }


def test_warmup_embedding_model_runs_warmup_query() -> None:
    seen_queries: list[list[str]] = []

    class FakeModel:
        def embed(self, queries: list[str]) -> list[list[float]]:
            seen_queries.append(list(queries))
            return [[0.1, 0.2, 0.3]]

    model = FakeModel()

    warmed = modal_app.warmup_embedding_model(model)

    assert warmed is model
    assert seen_queries == [["warmup"]]


def test_load_runtime_model_composes_creation_and_warmup(monkeypatch) -> None:
    model = object()

    monkeypatch.setattr(modal_app, "create_text_embedding", lambda: model)
    monkeypatch.setattr(
        modal_app, "warmup_embedding_model", lambda value: (value, "ok")
    )

    warmed = modal_app.load_runtime_model()

    assert warmed == (model, "ok")


def test_create_app_with_service_exposes_health_metadata() -> None:
    app = create_app(
        EmbeddingService(
            FakeEmbedder(vectors=[[0.1, 0.2, 0.3]]),
            default_model=modal_app.DEFAULT_MODEL,
        )
    )
    client = TestClient(app)

    response = client.get("/")

    assert response.status_code == 200
    assert response.json()["model"] == modal_app.DEFAULT_MODEL


def test_embed_query_function_returns_embedding_payload(monkeypatch) -> None:
    monkeypatch.setattr(
        modal_app,
        "load_runtime_model",
        lambda: FakeEmbedder(vectors=[[0.11, 0.22, 0.33]]),
    )
    payload = modal_app._embed_query_impl("hello")
    assert payload["model"] == modal_app.DEFAULT_MODEL
    assert payload["dimension"] == 3
    assert payload["embedding"] == [0.11, 0.22, 0.33]


def test_embed_batch_function_returns_embeddings_payload(monkeypatch) -> None:
    monkeypatch.setattr(
        modal_app,
        "load_runtime_model",
        lambda: FakeEmbedder(vectors=[[0.1, 0.2], [0.3, 0.4]]),
    )
    payload = modal_app._embed_batch_impl(["a", "b"])
    assert payload["model"] == modal_app.DEFAULT_MODEL
    assert payload["dimension"] == 2
    assert payload["embeddings"] == [[0.1, 0.2], [0.3, 0.4]]


def test_preview_text_truncates_long_input() -> None:
    long_text = "x" * 300
    preview = modal_app._preview_text(long_text, max_chars=50)
    assert "…" in preview
    assert "300 chars total" in preview


def test_preview_floats_respects_head() -> None:
    assert modal_app._preview_floats([1.0, 2.0, 3.0, 4.0, 5.0], head=2) == [1.0, 2.0]


def test_ensure_vecinita_loggers_visible_is_idempotent() -> None:
    modal_app._ensure_vecinita_loggers_visible()
    modal_app._ensure_vecinita_loggers_visible()
