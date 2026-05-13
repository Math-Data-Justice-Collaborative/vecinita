"""Unit tests for the canonical Modal embedding entrypoint (``modal-apps/embedding-modal``)."""

from __future__ import annotations

import importlib
import sys
from collections.abc import Sequence
from pathlib import Path
from types import ModuleType
from typing import Any
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

pytestmark = pytest.mark.unit

# One level deeper than ``tests/integration/`` (``test_services/embedding/``) → extra ``.parent``.
REPO_ROOT = Path(__file__).resolve().parents[5]
EMBEDDING_MODAL_SRC = REPO_ROOT / "modal-apps" / "embedding-modal" / "src"


class _FakeVector:
    def __init__(self, values: Sequence[float]) -> None:
        self._values = list(values)

    def tolist(self) -> list[float]:
        return list(self._values)


class _FakeEmbedder:
    """Minimal stand-in for fastembed models (mirrors embedding-modal tests)."""

    def __init__(self, vectors: Sequence[Sequence[float]] | None = None) -> None:
        self.calls: list[list[str]] = []
        self._vectors = list(vectors or ([0.1, 0.2, 0.3], [0.4, 0.5, 0.6]))

    def embed(self, texts: Sequence[str]) -> list[_FakeVector]:
        self.calls.append(list(texts))
        if len(texts) > len(self._vectors):
            raise RuntimeError("not enough fake vectors configured")
        return [_FakeVector(self._vectors[i]) for i, _ in enumerate(texts)]


@pytest.fixture
def modal_mock(monkeypatch: pytest.MonkeyPatch) -> MagicMock:
    path = str(EMBEDDING_MODAL_SRC)
    if path not in sys.path:
        sys.path.insert(0, path)
    for key in list(sys.modules):
        if key == "vecinita" or key.startswith("vecinita."):
            monkeypatch.delitem(sys.modules, key, raising=False)

    mock_modal = MagicMock()

    app_instance = MagicMock()
    mock_modal.App.return_value = app_instance

    image_instance = MagicMock()
    mock_modal.Image.debian_slim.return_value = image_instance
    image_instance.pip_install.return_value = image_instance

    mock_modal.Volume.from_name.return_value = MagicMock()

    def _identity_decorator(*_args: object, **_kwargs: object):
        def _wrap(fn: object) -> object:
            return fn

        return _wrap

    app_instance.function.side_effect = _identity_decorator
    mock_modal.asgi_app.side_effect = _identity_decorator

    monkeypatch.setitem(sys.modules, "modal", mock_modal)
    return mock_modal


class TestEmbeddingModalApp:
    def test_no_modal_asgi_export(self, modal_mock: MagicMock) -> None:
        import vecinita.app as modal_app

        modal_app = importlib.reload(modal_app)
        assert not hasattr(modal_app, "web_app")
        assert hasattr(modal_app, "embed_query")

    def test_module_loads(self, modal_mock: MagicMock) -> None:
        import vecinita.app as modal_app

        modal_app = importlib.reload(modal_app)

        assert hasattr(modal_app, "app")
        assert hasattr(modal_app, "image")

    def test_app_name_constant(self, modal_mock: MagicMock) -> None:
        import vecinita.app as modal_app

        modal_app = importlib.reload(modal_app)

        assert modal_app.APP_NAME == "vecinita-embedding"
        modal_mock.App.assert_called_with("vecinita-embedding")

    def test_image_declares_fastembed_only(self, modal_mock: MagicMock) -> None:
        import vecinita.app as modal_app

        importlib.reload(modal_app)

        image_instance = modal_mock.Image.debian_slim.return_value
        assert image_instance.pip_install.call_count >= 1
        first_args = image_instance.pip_install.call_args_list[0][0]
        joined = " ".join(str(x) for x in first_args[0])
        assert "fastembed" in joined


def _reload_modal_app(modal_mock: MagicMock) -> Any:
    import vecinita.app as modal_app

    return importlib.reload(modal_app)


class TestEmbeddingModalAppRuntimeCoverage:
    """Exercises ``vecinita.app`` helpers and Modal entrypoints for coverage (≥98% gate)."""

    def test_create_text_embedding_uses_default_configuration(
        self, modal_mock: MagicMock, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        captured: dict[str, str] = {}

        class FakeTextEmbedding:
            def __init__(self, model_name: str, cache_dir: str) -> None:
                captured["model_name"] = model_name
                captured["cache_dir"] = cache_dir

        fake_fastembed = ModuleType("fastembed")
        fake_fastembed.TextEmbedding = FakeTextEmbedding
        monkeypatch.setitem(sys.modules, "fastembed", fake_fastembed)

        modal_app = _reload_modal_app(modal_mock)
        model = modal_app.create_text_embedding()

        assert isinstance(model, FakeTextEmbedding)
        assert captured == {
            "model_name": modal_app.DEFAULT_MODEL,
            "cache_dir": modal_app.MODEL_DIR,
        }

    def test_warmup_embedding_model_runs_warmup_query(self, modal_mock: MagicMock) -> None:
        modal_app = _reload_modal_app(modal_mock)
        seen_queries: list[list[str]] = []

        class FakeModel:
            def embed(self, queries: list[str]) -> list[list[float]]:
                seen_queries.append(list(queries))
                return [[0.1, 0.2, 0.3]]

        inner = FakeModel()
        warmed = modal_app.warmup_embedding_model(inner)

        assert warmed is inner
        assert seen_queries == [["warmup"]]

    def test_load_runtime_model_composes_creation_and_warmup(
        self, modal_mock: MagicMock, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        modal_app = _reload_modal_app(modal_mock)
        model = object()
        monkeypatch.setattr(modal_app, "create_text_embedding", lambda: model)
        monkeypatch.setattr(modal_app, "warmup_embedding_model", lambda value: (value, "ok"))

        warmed = modal_app.load_runtime_model()

        assert warmed == (model, "ok")

    def test_create_app_with_service_exposes_health_metadata(self, modal_mock: MagicMock) -> None:
        path = str(EMBEDDING_MODAL_SRC)
        if path not in sys.path:
            sys.path.insert(0, path)
        from vecinita.api import create_app
        from vecinita.service import EmbeddingService

        modal_app = _reload_modal_app(modal_mock)
        app = create_app(
            EmbeddingService(
                _FakeEmbedder(vectors=[[0.1, 0.2, 0.3]]),
                default_model=modal_app.DEFAULT_MODEL,
            )
        )
        client = TestClient(app)

        response = client.get("/")

        assert response.status_code == 200
        assert response.json()["model"] == modal_app.DEFAULT_MODEL

    def test_embed_query_impl_returns_embedding_payload(
        self, modal_mock: MagicMock, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        modal_app = _reload_modal_app(modal_mock)
        monkeypatch.setattr(
            modal_app,
            "load_runtime_model",
            lambda: _FakeEmbedder(vectors=[[0.11, 0.22, 0.33]]),
        )
        payload = modal_app._embed_query_impl("hello")
        assert payload["model"] == modal_app.DEFAULT_MODEL
        assert payload["dimension"] == 3
        assert payload["embedding"] == [0.11, 0.22, 0.33]

    def test_embed_batch_impl_returns_embeddings_payload(
        self, modal_mock: MagicMock, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        modal_app = _reload_modal_app(modal_mock)
        monkeypatch.setattr(
            modal_app,
            "load_runtime_model",
            lambda: _FakeEmbedder(vectors=[[0.1, 0.2], [0.3, 0.4]]),
        )
        payload = modal_app._embed_batch_impl(["a", "b"])
        assert payload["model"] == modal_app.DEFAULT_MODEL
        assert payload["dimension"] == 2
        assert payload["embeddings"] == [[0.1, 0.2], [0.3, 0.4]]

    def test_embed_batch_impl_empty_queries_dimension_zero(
        self, modal_mock: MagicMock, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        modal_app = _reload_modal_app(modal_mock)

        class EmptyEmbedder:
            def embed(self, texts: Sequence[str]) -> list[_FakeVector]:
                assert list(texts) == []
                return []

        monkeypatch.setattr(modal_app, "load_runtime_model", lambda: EmptyEmbedder())
        payload = modal_app._embed_batch_impl([])
        assert payload["embeddings"] == []
        assert payload["dimension"] == 0
        assert payload["model"] == modal_app.DEFAULT_MODEL

    def test_modal_embed_query_and_embed_batch_entrypoints(
        self, modal_mock: MagicMock, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        modal_app = _reload_modal_app(modal_mock)
        fake = _FakeEmbedder(vectors=[[1.0], [2.0, 3.0], [4.0, 5.0]])
        monkeypatch.setattr(modal_app, "load_runtime_model", lambda: fake)

        single = modal_app.embed_query("only")
        assert single["embedding"] == [1.0]
        assert single["dimension"] == 1

        batch = modal_app.embed_batch(["x", "y"])
        assert batch["embeddings"] == [[1.0], [2.0, 3.0]]
        assert batch["dimension"] == 1  # len(first vector); rows can differ in length
