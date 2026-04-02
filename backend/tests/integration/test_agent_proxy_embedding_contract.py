"""Integration tests: Agent → modal-proxy embedding endpoint contract.

Verifies the embedding routing chain from config.py URL normalization
through to request/response shape expectations:
- _normalize_internal_service_url forces proxy URL on Render for local hostnames
- Services with external (non-local) URLs are passed through unchanged on Render
- Embedding URL must contain /embedding path suffix when routed via proxy
- MODAL_EMBEDDING_ENDPOINT takes precedence over EMBEDDING_SERVICE_URL
- Strict-mode env vars prevent silent fallback to local embedding services
"""

from __future__ import annotations

import importlib

import pytest

pytestmark = pytest.mark.integration

_RENDER_PROXY_EMBEDDING_URL = "http://vecinita-modal-proxy-v1:10000/embedding"
_LOCAL_PROXY_EMBEDDING_URL = "http://localhost:10000/embedding"
_DIRECT_EMBEDDING_URL = "http://embedding-service:8001"
_DOCKER_LOCAL_URL = "http://localhost:8001"


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
        assert cfg.EMBEDDING_SERVICE_URL == _RENDER_PROXY_EMBEDDING_URL

    def test_docker_embedding_service_hostname_is_replaced_on_render(self, monkeypatch):
        monkeypatch.setenv("RENDER", "true")
        monkeypatch.setenv("EMBEDDING_SERVICE_URL", _DIRECT_EMBEDDING_URL)
        monkeypatch.delenv("MODAL_EMBEDDING_ENDPOINT", raising=False)

        cfg = _reload_config()
        assert cfg.EMBEDDING_SERVICE_URL == _RENDER_PROXY_EMBEDDING_URL

    def test_modal_embedding_endpoint_takes_precedence_over_embedding_service_url(
        self, monkeypatch
    ):
        monkeypatch.setenv("RENDER", "true")
        monkeypatch.setenv("MODAL_EMBEDDING_ENDPOINT", _RENDER_PROXY_EMBEDDING_URL)
        monkeypatch.setenv("EMBEDDING_SERVICE_URL", _DOCKER_LOCAL_URL)

        cfg = _reload_config()
        assert cfg.EMBEDDING_SERVICE_URL == _RENDER_PROXY_EMBEDDING_URL

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
        assert cfg.EMBEDDING_SERVICE_URL == _RENDER_PROXY_EMBEDDING_URL

    def test_no_env_vars_off_render_falls_back_to_proxy_default(self, monkeypatch):
        monkeypatch.delenv("RENDER", raising=False)
        monkeypatch.delenv("RENDER_SERVICE_ID", raising=False)
        monkeypatch.delenv("EMBEDDING_SERVICE_URL", raising=False)
        monkeypatch.delenv("MODAL_EMBEDDING_ENDPOINT", raising=False)

        cfg = _reload_config()
        assert cfg.EMBEDDING_SERVICE_URL == _RENDER_PROXY_EMBEDDING_URL


# ---------------------------------------------------------------------------
# Path suffix contract: /embedding must be present for proxy routing
# ---------------------------------------------------------------------------


class TestEmbeddingPathContract:
    def test_proxy_url_ends_with_embedding_path(self, monkeypatch):
        monkeypatch.setenv("RENDER", "true")
        monkeypatch.delenv("EMBEDDING_SERVICE_URL", raising=False)
        monkeypatch.delenv("MODAL_EMBEDDING_ENDPOINT", raising=False)

        cfg = _reload_config()
        url = cfg.EMBEDDING_SERVICE_URL
        assert (
            "/embedding" in url
        ), f"Proxy embedding URL must contain '/embedding' path; got: {url!r}"

    def test_proxy_hostname_present_in_render_embedding_url(self, monkeypatch):
        monkeypatch.setenv("RENDER", "true")
        monkeypatch.delenv("EMBEDDING_SERVICE_URL", raising=False)
        monkeypatch.delenv("MODAL_EMBEDDING_ENDPOINT", raising=False)

        cfg = _reload_config()
        url = cfg.EMBEDDING_SERVICE_URL
        assert "modal-proxy" in url, f"Proxy embedding URL must contain 'modal-proxy'; got: {url!r}"


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
                "DATABASE_URL": "postgresql://user:pass@host/db",
                "SUPABASE_URL": "https://test.supabase.co",
                "SUPABASE_KEY": "key",
                "MODAL_OLLAMA_ENDPOINT": "http://vecinita-modal-proxy-v1:10000/model",
                "MODAL_EMBEDDING_ENDPOINT": "http://vecinita-modal-proxy-v1:10000/embedding",
                "OLLAMA_BASE_URL": "http://vecinita-modal-proxy-v1:10000/model",
                "EMBEDDING_SERVICE_URL": "http://vecinita-modal-proxy-v1:10000/embedding",
                "PROXY_AUTH_TOKEN": "tok",
                "VITE_BACKEND_URL": "https://vecinita-gateway.onrender.com",
                "VITE_GATEWAY_URL": "https://vecinita-gateway.onrender.com",
                "ALLOWED_ORIGINS": "https://vecinita-frontend.onrender.com",
            }
        )
        # Remove strict flags entirely so the validator must error on them.
        base_env.pop("AGENT_ENFORCE_PROXY", None)
        base_env.pop("RENDER_REMOTE_INFERENCE_ONLY", None)

        result = validate_shared_render_env(base_env)
        assert not result.ok
        err_text = " ".join(result.errors)
        assert "AGENT_ENFORCE_PROXY" in err_text
        assert "RENDER_REMOTE_INFERENCE_ONLY" in err_text

    def test_render_env_contract_accepts_strict_flags_set(self):
        """render_env_contract is OK when all required keys and strict flags are present."""
        from src.utils.render_env_contract import REQUIRED_KEYS, validate_shared_render_env

        # Build a minimal env dict satisfying all REQUIRED_KEYS with proxy-consistent values.
        base_env = dict.fromkeys(REQUIRED_KEYS, "placeholder")
        base_env.update(
            {
                "DATABASE_URL": "postgresql://user:pass@host/db",
                "SUPABASE_URL": "https://test.supabase.co",
                "SUPABASE_KEY": "key",
                "MODAL_OLLAMA_ENDPOINT": "http://vecinita-modal-proxy-v1:10000/model",
                "MODAL_EMBEDDING_ENDPOINT": "http://vecinita-modal-proxy-v1:10000/embedding",
                "OLLAMA_BASE_URL": "http://vecinita-modal-proxy-v1:10000/model",
                "EMBEDDING_SERVICE_URL": "http://vecinita-modal-proxy-v1:10000/embedding",
                "PROXY_AUTH_TOKEN": "tok",
                "VITE_BACKEND_URL": "https://vecinita-gateway.onrender.com",
                "VITE_GATEWAY_URL": "https://vecinita-gateway.onrender.com",
                "ALLOWED_ORIGINS": "https://vecinita-frontend.onrender.com",
                "AGENT_ENFORCE_PROXY": "true",
                "RENDER_REMOTE_INFERENCE_ONLY": "true",
            }
        )
        result = validate_shared_render_env(base_env)
        assert result.ok, f"Expected OK; errors: {result.errors}"
