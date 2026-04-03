"""Integration tests for embedding endpoint normalization and Render env contract.

Current behavior prefers explicit non-local endpoints and falls back to local
defaults when endpoint env vars are absent or local-only in Render.
"""

from __future__ import annotations

import importlib

import pytest

pytestmark = pytest.mark.integration

_DIRECT_MODAL_EMBEDDING_URL = "https://vecinita--vecinita-embedding-web-app.modal.run"
_DIRECT_EMBEDDING_URL = "http://embedding-service:8001"
_DOCKER_LOCAL_URL = "http://localhost:8001"


@pytest.fixture(autouse=True)
def _clear_embedding_endpoint_env(monkeypatch):
    """Avoid inherited process env forcing modal endpoints across tests."""
    monkeypatch.delenv("VECINITA_EMBEDDING_API_URL", raising=False)


def _reload_config():
    """Re-import config.py so module-level constants re-evaluate under patched env."""
    import src.config as cfg

    return importlib.reload(cfg)


# ---------------------------------------------------------------------------
# URL normalisation on Render
# ---------------------------------------------------------------------------


class TestEmbeddingUrlNormalisationOnRender:
    def test_local_hostname_is_replaced_by_proxy_fallback(self, monkeypatch):
        monkeypatch.setenv("RENDER", "true")
        monkeypatch.setenv("EMBEDDING_SERVICE_URL", _DOCKER_LOCAL_URL)
        monkeypatch.delenv("MODAL_EMBEDDING_ENDPOINT", raising=False)

        cfg = _reload_config()
        assert cfg.EMBEDDING_SERVICE_URL == _DOCKER_LOCAL_URL

    def test_docker_embedding_service_hostname_is_replaced_on_render(self, monkeypatch):
        monkeypatch.setenv("RENDER", "true")
        monkeypatch.setenv("EMBEDDING_SERVICE_URL", _DIRECT_EMBEDDING_URL)
        monkeypatch.delenv("MODAL_EMBEDDING_ENDPOINT", raising=False)

        cfg = _reload_config()
        assert cfg.EMBEDDING_SERVICE_URL == _DOCKER_LOCAL_URL

    def test_modal_embedding_endpoint_takes_precedence_over_embedding_service_url(
        self, monkeypatch
    ):
        monkeypatch.setenv("RENDER", "true")
        monkeypatch.setenv("MODAL_EMBEDDING_ENDPOINT", _DIRECT_MODAL_EMBEDDING_URL)
        monkeypatch.setenv("EMBEDDING_SERVICE_URL", _DOCKER_LOCAL_URL)

        cfg = _reload_config()
        assert cfg.EMBEDDING_SERVICE_URL == _DIRECT_MODAL_EMBEDDING_URL

    def test_external_embedding_url_is_preserved_on_render(self, monkeypatch):
        """A non-local, non-Docker URL (e.g. an external service) is kept as-is on Render."""
        external_url = "https://my-external-embedding.example.com/v1"
        monkeypatch.setenv("RENDER", "true")
        monkeypatch.setenv("EMBEDDING_SERVICE_URL", external_url)
        monkeypatch.delenv("MODAL_EMBEDDING_ENDPOINT", raising=False)

        cfg = _reload_config()
        assert cfg.EMBEDDING_SERVICE_URL == external_url

    def test_no_render_env_uses_raw_embedding_service_url(self, monkeypatch):
        monkeypatch.delenv("RENDER", raising=False)
        monkeypatch.delenv("RENDER_SERVICE_ID", raising=False)
        monkeypatch.setenv("EMBEDDING_SERVICE_URL", _DIRECT_EMBEDDING_URL)
        monkeypatch.delenv("MODAL_EMBEDDING_ENDPOINT", raising=False)

        cfg = _reload_config()
        assert cfg.EMBEDDING_SERVICE_URL == _DIRECT_EMBEDDING_URL

    def test_no_env_vars_falls_back_to_proxy_on_render(self, monkeypatch):
        monkeypatch.setenv("RENDER", "true")
        monkeypatch.delenv("EMBEDDING_SERVICE_URL", raising=False)
        monkeypatch.delenv("MODAL_EMBEDDING_ENDPOINT", raising=False)

        cfg = _reload_config()
        assert cfg.EMBEDDING_SERVICE_URL == _DOCKER_LOCAL_URL

    def test_no_env_vars_off_render_falls_back_to_local_default(self, monkeypatch):
        monkeypatch.delenv("RENDER", raising=False)
        monkeypatch.delenv("RENDER_SERVICE_ID", raising=False)
        monkeypatch.delenv("EMBEDDING_SERVICE_URL", raising=False)
        monkeypatch.delenv("MODAL_EMBEDDING_ENDPOINT", raising=False)

        cfg = _reload_config()
        assert cfg.EMBEDDING_SERVICE_URL == _DOCKER_LOCAL_URL


class TestEmbeddingPathContract:
    def test_default_url_has_no_required_embedding_path_suffix(self, monkeypatch):
        monkeypatch.setenv("RENDER", "true")
        monkeypatch.delenv("EMBEDDING_SERVICE_URL", raising=False)
        monkeypatch.delenv("MODAL_EMBEDDING_ENDPOINT", raising=False)

        cfg = _reload_config()
        url = cfg.EMBEDDING_SERVICE_URL
        assert url == _DOCKER_LOCAL_URL

    def test_modal_hostname_preserved_when_modal_endpoint_is_configured(self, monkeypatch):
        monkeypatch.setenv("RENDER", "true")
        monkeypatch.setenv("MODAL_EMBEDDING_ENDPOINT", _DIRECT_MODAL_EMBEDDING_URL)
        monkeypatch.delenv("EMBEDDING_SERVICE_URL", raising=False)

        cfg = _reload_config()
        url = cfg.EMBEDDING_SERVICE_URL
        assert "modal.run" in url


# ---------------------------------------------------------------------------
# Strict-mode flags prevent silent local fallback
# ---------------------------------------------------------------------------


class TestEmbeddingStrictModeFlags:
    def test_render_env_contract_flags_missing_strict_mode(self):
        """render_env_contract validator errors if strict flags absent."""
        from src.utils.render_env_contract import REQUIRED_KEYS, validate_shared_render_env

        base_env = dict.fromkeys(REQUIRED_KEYS, "placeholder")
        base_env.update(
            {
                "DATABASE_URL": "postgresql://user:pass@host/db?sslmode=require",
                "SUPABASE_URL": "https://test.supabase.co",
                "SUPABASE_KEY": "key",
                "VECINITA_MODEL_API_URL": "https://vecinita--vecinita-model-api.modal.run",
                "VECINITA_EMBEDDING_API_URL": "https://vecinita--vecinita-embedding-api.modal.run",
                "VECINITA_SCRAPER_API_URL": "https://vecinita--vecinita-scraper-api.modal.run",
                "VITE_BACKEND_URL": "https://vecinita-gateway.onrender.com",
                "VITE_GATEWAY_URL": "https://vecinita-gateway.onrender.com",
                "ALLOWED_ORIGINS": "https://vecinita-frontend.onrender.com",
            }
        )
        # Remove strict flags entirely so the validator must error on them.
        base_env.pop("RENDER_REMOTE_INFERENCE_ONLY", None)

        result = validate_shared_render_env(base_env)
        assert not result.ok
        err_text = " ".join(result.errors)
        assert "RENDER_REMOTE_INFERENCE_ONLY" in err_text

    def test_render_env_contract_accepts_strict_flags_set(self):
        """render_env_contract is OK when all required keys and strict flags are present."""
        from src.utils.render_env_contract import REQUIRED_KEYS, validate_shared_render_env

        # Build a minimal env dict satisfying all REQUIRED_KEYS with proxy-consistent values.
        base_env = dict.fromkeys(REQUIRED_KEYS, "placeholder")
        base_env.update(
            {
                "DATABASE_URL": "postgresql://user:pass@host/db?sslmode=require",
                "SUPABASE_URL": "https://test.supabase.co",
                "SUPABASE_KEY": "key",
                "VECINITA_MODEL_API_URL": "https://vecinita--vecinita-model-api.modal.run",
                "VECINITA_EMBEDDING_API_URL": "https://vecinita--vecinita-embedding-api.modal.run",
                "VECINITA_SCRAPER_API_URL": "https://vecinita--vecinita-scraper-api.modal.run",
                "MODAL_TOKEN_SECRET": "secret",
                "VITE_BACKEND_URL": "https://vecinita-gateway.onrender.com",
                "VITE_GATEWAY_URL": "https://vecinita-gateway.onrender.com",
                "ALLOWED_ORIGINS": "https://vecinita-frontend.onrender.com",
                "DB_DATA_MODE": "postgres",
                "OLLAMA_MODEL": "llama3.1:8b",
                "RENDER_REMOTE_INFERENCE_ONLY": "true",
            }
        )
        result = validate_shared_render_env(base_env)
        assert result.ok, f"Expected OK; errors: {result.errors}"
