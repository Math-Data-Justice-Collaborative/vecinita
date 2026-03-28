"""Unit tests for src.embedding_service.modal_app."""

import importlib
import sys
from unittest.mock import MagicMock

import pytest

pytestmark = pytest.mark.unit


@pytest.fixture
def modal_mock(monkeypatch):
    mock_modal = MagicMock()

    app_instance = MagicMock()
    mock_modal.App.return_value = app_instance

    image_instance = MagicMock()
    mock_modal.Image.debian_slim.return_value = image_instance
    image_instance.pip_install.return_value = image_instance

    mock_modal.Secret.from_name.return_value = MagicMock()

    def _identity_decorator(*_args, **_kwargs):
        def _wrap(fn):
            return fn

        return _wrap

    app_instance.function.side_effect = _identity_decorator
    mock_modal.asgi_app.side_effect = _identity_decorator

    monkeypatch.setitem(sys.modules, "modal", mock_modal)
    return mock_modal


class TestEmbeddingModalApp:
    def test_module_loads(self, modal_mock):
        import src.embedding_service.modal_app as modal_app

        modal_app = importlib.reload(modal_app)

        assert hasattr(modal_app, "app")
        assert hasattr(modal_app, "image")

    def test_mount_and_secret_configuration(self, modal_mock):
        import src.embedding_service.modal_app as modal_app

        modal_app = importlib.reload(modal_app)

        assert modal_app.APP_NAME == "vecinita-embedding"
        modal_mock.App.assert_called_with("vecinita-embedding")
        modal_mock.Secret.from_name.assert_called()

    def test_web_app_callable(self, modal_mock):
        import src.embedding_service.modal_app as modal_app

        modal_app = importlib.reload(modal_app)

        app = modal_app.web_app()
        assert app is not None
