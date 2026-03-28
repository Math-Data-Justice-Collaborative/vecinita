"""Unit tests for src.scraper.modal_app."""

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

    image = MagicMock()
    mock_modal.Image.debian_slim.return_value = image
    image.pip_install_from_requirements.return_value = image
    image.env.return_value = image

    mock_modal.Mount.from_local_dir.return_value = MagicMock()
    mock_modal.Secret.from_name.return_value = MagicMock()
    mock_modal.Cron.return_value = MagicMock()

    def _identity_decorator(*_args, **_kwargs):
        def _wrap(fn):
            return fn

        return _wrap

    app_instance.function.side_effect = _identity_decorator
    mock_modal.asgi_app.side_effect = _identity_decorator

    monkeypatch.setitem(sys.modules, "modal", mock_modal)
    return mock_modal


def test_scraper_modal_app_loads(modal_mock):
    import src.scraper.modal_app as modal_app

    modal_app = importlib.reload(modal_app)

    assert hasattr(modal_app, "app")
    assert hasattr(modal_app, "run_reindex")
    assert hasattr(modal_app, "weekly_reindex")


def test_scraper_modal_schedule_default(modal_mock):
    import src.scraper.modal_app as modal_app

    modal_app = importlib.reload(modal_app)

    assert modal_app.REINDEX_CRON_SCHEDULE == "0 2 * * 0"
    modal_mock.Cron.assert_called_with("0 2 * * 0")
