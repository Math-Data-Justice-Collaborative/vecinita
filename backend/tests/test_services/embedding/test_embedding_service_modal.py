"""Unit tests for the canonical Modal embedding entrypoint (``services/embedding-modal``)."""

from __future__ import annotations

import importlib
import sys
from pathlib import Path
from unittest.mock import MagicMock

import pytest

pytestmark = pytest.mark.unit

REPO_ROOT = Path(__file__).resolve().parents[4]
EMBEDDING_MODAL_SRC = REPO_ROOT / "services" / "embedding-modal" / "src"


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

    def test_image_declares_fastembed_and_fastapi(self, modal_mock: MagicMock) -> None:
        import vecinita.app as modal_app

        importlib.reload(modal_app)

        image_instance = modal_mock.Image.debian_slim.return_value
        assert image_instance.pip_install.call_count >= 1
        first_args = image_instance.pip_install.call_args_list[0][0]
        joined = " ".join(str(x) for x in first_args[0])
        assert "fastembed" in joined
        assert "fastapi" in joined

    def test_asgi_app_uses_modal_sdk_without_deprecated_kwargs(self, modal_mock: MagicMock) -> None:
        import vecinita.app as modal_app

        importlib.reload(modal_app)

        assert modal_mock.asgi_app.call_args.kwargs == {}

    def test_web_app_callable(self, modal_mock: MagicMock, monkeypatch: pytest.MonkeyPatch) -> None:
        import vecinita.app as modal_app

        modal_app = importlib.reload(modal_app)
        sentinel = object()
        monkeypatch.setattr(modal_app, "load_runtime_model", lambda: sentinel)
        monkeypatch.setattr(
            modal_app,
            "build_web_app",
            lambda _model: MagicMock(name="FastAPIStub"),
        )

        assert modal_app.web_app() is not None
