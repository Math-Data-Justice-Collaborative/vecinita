"""Shared fixtures for model-modal tests."""

from __future__ import annotations

import os
from collections.abc import Generator
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

# ``DEFAULT_MODEL`` from a monorepo ``.env`` may not be a ``SUPPORTED_MODELS`` id here.
os.environ.pop("DEFAULT_MODEL", None)


@pytest.fixture
def mock_client() -> MagicMock:
    """Ollama client stub; tests configure ``list``, ``chat``, etc. on it."""
    return MagicMock()


@pytest.fixture
def http(mock_client: MagicMock) -> Generator[TestClient, None, None]:
    """TestClient for ``create_app`` with the Ollama client constructor patched."""
    with patch("vecinita.api.routes._ollama.Client", return_value=mock_client):
        from vecinita.api.routes import create_app

        yield TestClient(create_app(ollama_host="http://test-ollama.invalid"))
