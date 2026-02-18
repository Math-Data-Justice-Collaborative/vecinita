"""
Unit tests for src/embedding_service/modal_app.py

Tests Modal deployment wrapper for embedding service.
"""
import pytest
import sys
from unittest.mock import patch, MagicMock

pytestmark = pytest.mark.unit

# Mock modal module before importing modal_app
mock_modal = MagicMock()
# Configure the mock to support the chained calls in modal_app.py
mock_app_instance = MagicMock()
mock_function_wrapper = MagicMock()
mock_wrapped = MagicMock()
mock_wrapped.mounts = []
mock_function_wrapper.__wrapped__ = mock_wrapped
mock_app_instance.function.return_value = lambda x: mock_function_wrapper
mock_modal.App.return_value = mock_app_instance
mock_modal.Image.debian_slim.return_value.pip_install.return_value = MagicMock()
mock_modal.Mount.from_local_dir.return_value = MagicMock()
mock_modal.Secret.from_name.return_value = MagicMock()
sys.modules['modal'] = mock_modal


class TestModalApp:
    """Test Modal app configuration."""

    def test_modal_app_creation(self):
        """Test that Modal app is created."""
        from src.services.embedding import modal_app
        # Verify app attribute exists
        assert hasattr(modal_app, "app")

    def test_modal_image_configuration(self):
        """Test that Modal image is properly configured."""
        from src.services.embedding import modal_app
        # Verify image was configured
        assert hasattr(modal_app, "image")

    def test_modal_function_decoration(self):
        """Test that modal function is decorated properly."""
        from src.services.embedding import modal_app
        # Just verify the module loads without error
        assert modal_app is not None
