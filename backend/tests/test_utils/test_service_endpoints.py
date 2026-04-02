"""Unit tests for src.service_endpoints — centralized endpoint resolution.

Covers:
- MODEL_ENDPOINT / EMBEDDING_ENDPOINT / SCRAPER_ENDPOINT resolution
- is_render_strict_mode() flag logic
- is_render() detection
- get_allowed_origins() parsing
"""

from __future__ import annotations

import importlib
from unittest.mock import patch

import pytest

pytestmark = pytest.mark.unit


def _reload(monkeypatch_env: dict[str, str] | None = None):
    """Reload both config and service_endpoints so module-level constants re-evaluate."""
    import src.config as cfg_mod
    import src.service_endpoints as ep_mod

    if monkeypatch_env is not None:
        with patch.dict("os.environ", monkeypatch_env, clear=False):
            importlib.reload(cfg_mod)
            importlib.reload(ep_mod)
            return ep_mod
    importlib.reload(cfg_mod)
    importlib.reload(ep_mod)
    return ep_mod


# ---------------------------------------------------------------------------
# Endpoint resolution
# ---------------------------------------------------------------------------


class TestEndpointResolution:
    def test_model_endpoint_returns_proxy_on_render(self, monkeypatch):
        monkeypatch.setenv("RENDER", "true")
        monkeypatch.delenv("VECINITA_MODEL_API_URL", raising=False)
        monkeypatch.delenv("MODAL_OLLAMA_ENDPOINT", raising=False)
        monkeypatch.delenv("OLLAMA_BASE_URL", raising=False)

        ep = _reload()
        assert "modal-proxy" in ep.MODEL_ENDPOINT
        assert "/model" in ep.MODEL_ENDPOINT

    def test_embedding_endpoint_returns_proxy_on_render(self, monkeypatch):
        monkeypatch.setenv("RENDER", "true")
        monkeypatch.delenv("VECINITA_EMBEDDING_API_URL", raising=False)
        monkeypatch.delenv("MODAL_EMBEDDING_ENDPOINT", raising=False)
        monkeypatch.delenv("EMBEDDING_SERVICE_URL", raising=False)

        ep = _reload()
        assert "modal-proxy" in ep.EMBEDDING_ENDPOINT
        assert "/embedding" in ep.EMBEDDING_ENDPOINT

    def test_scraper_endpoint_falls_back_to_proxy_jobs(self, monkeypatch):
        monkeypatch.delenv("VECINITA_SCRAPER_API_URL", raising=False)
        monkeypatch.delenv("SCRAPER_SERVICE_URL", raising=False)
        monkeypatch.delenv("RENDER", raising=False)
        monkeypatch.delenv("RENDER_SERVICE_ID", raising=False)

        ep = _reload()
        assert "/jobs" in ep.SCRAPER_ENDPOINT

    def test_agent_service_url_default_localhost(self, monkeypatch):
        monkeypatch.delenv("AGENT_SERVICE_URL", raising=False)

        ep = _reload()
        assert ep.AGENT_SERVICE_URL == "http://localhost:8000"

    def test_agent_service_url_overridden_by_env(self, monkeypatch):
        monkeypatch.setenv("AGENT_SERVICE_URL", "http://vecinita-agent:8000")

        ep = _reload()
        assert ep.AGENT_SERVICE_URL == "http://vecinita-agent:8000"


# ---------------------------------------------------------------------------
# is_render_strict_mode()
# ---------------------------------------------------------------------------


class TestIsRenderStrictMode:
    def test_returns_true_when_both_flags_enabled(self, monkeypatch):
        monkeypatch.setenv("AGENT_ENFORCE_PROXY", "true")
        monkeypatch.setenv("RENDER_REMOTE_INFERENCE_ONLY", "true")

        import src.service_endpoints as ep

        importlib.reload(ep)
        assert ep.is_render_strict_mode() is True

    def test_returns_false_when_one_flag_missing(self, monkeypatch):
        monkeypatch.setenv("AGENT_ENFORCE_PROXY", "true")
        monkeypatch.delenv("RENDER_REMOTE_INFERENCE_ONLY", raising=False)

        import src.service_endpoints as ep

        importlib.reload(ep)
        assert ep.is_render_strict_mode() is False

    def test_returns_false_when_both_flags_absent(self, monkeypatch):
        monkeypatch.delenv("AGENT_ENFORCE_PROXY", raising=False)
        monkeypatch.delenv("RENDER_REMOTE_INFERENCE_ONLY", raising=False)

        import src.service_endpoints as ep

        importlib.reload(ep)
        assert ep.is_render_strict_mode() is False

    def test_accepts_numeric_truthy_values(self, monkeypatch):
        monkeypatch.setenv("AGENT_ENFORCE_PROXY", "1")
        monkeypatch.setenv("RENDER_REMOTE_INFERENCE_ONLY", "1")

        import src.service_endpoints as ep

        importlib.reload(ep)
        assert ep.is_render_strict_mode() is True

    def test_rejects_false_strings(self, monkeypatch):
        monkeypatch.setenv("AGENT_ENFORCE_PROXY", "false")
        monkeypatch.setenv("RENDER_REMOTE_INFERENCE_ONLY", "0")

        import src.service_endpoints as ep

        importlib.reload(ep)
        assert ep.is_render_strict_mode() is False


# ---------------------------------------------------------------------------
# is_render()
# ---------------------------------------------------------------------------


class TestIsRender:
    def test_returns_true_on_render(self, monkeypatch):
        monkeypatch.setenv("RENDER", "true")
        import src.service_endpoints as ep

        assert ep.is_render() is True

    def test_returns_false_off_render(self, monkeypatch):
        monkeypatch.delenv("RENDER", raising=False)
        monkeypatch.delenv("RENDER_SERVICE_ID", raising=False)
        import src.service_endpoints as ep

        assert ep.is_render() is False


# ---------------------------------------------------------------------------
# get_allowed_origins()
# ---------------------------------------------------------------------------


class TestGetAllowedOrigins:
    def test_parses_comma_separated_origins(self, monkeypatch):
        monkeypatch.setenv(
            "ALLOWED_ORIGINS",
            "https://vecinita-frontend.onrender.com,https://staging.vecinita.com",
        )
        import src.service_endpoints as ep

        importlib.reload(ep)
        origins = ep.get_allowed_origins()
        assert "https://vecinita-frontend.onrender.com" in origins
        assert "https://staging.vecinita.com" in origins

    def test_parses_space_separated_origins(self, monkeypatch):
        monkeypatch.setenv(
            "ALLOWED_ORIGINS",
            "https://a.example.com https://b.example.com",
        )
        import src.service_endpoints as ep

        importlib.reload(ep)
        origins = ep.get_allowed_origins()
        assert len(origins) == 2

    def test_returns_wildcard_when_not_set(self, monkeypatch):
        monkeypatch.delenv("ALLOWED_ORIGINS", raising=False)
        import src.service_endpoints as ep

        importlib.reload(ep)
        assert ep.get_allowed_origins() == ["*"]

    def test_strips_whitespace_from_entries(self, monkeypatch):
        monkeypatch.setenv("ALLOWED_ORIGINS", "  https://a.com , https://b.com  ")
        import src.service_endpoints as ep

        importlib.reload(ep)
        origins = ep.get_allowed_origins()
        assert all(o == o.strip() for o in origins)
        assert "https://a.com" in origins
