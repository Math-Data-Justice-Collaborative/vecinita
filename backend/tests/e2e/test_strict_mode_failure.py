"""End-to-end tests: strict-mode failure behavior.

These tests verify that when AGENT_ENFORCE_PROXY=true and
RENDER_REMOTE_INFERENCE_ONLY=true are set, the system fails fast rather
than silently falling back to local model or embedding services.

Scenarios:
1. LocalLLMClientManager.validate_runtime() raises when enforce_proxy=True
   and base_url points to a non-proxy direct endpoint.
2. LocalLLMClientManager.validate_runtime() raises when enforce_proxy=True
   and base_url is empty/missing.
3. render_env_contract validator blocks deploy if strict flags absent.
4. service_endpoints.is_render_strict_mode() correctly gates strict behavior.
5. Startup-critical code path: agent refuses to build LLM client for
   direct URL in strict mode.
"""

from __future__ import annotations

import importlib

import pytest

from src.services.llm.client_manager import LocalLLMClientManager

pytestmark = pytest.mark.e2e

_PROXY_URL = "http://vecinita-modal-proxy-v1:10000/model"
_DIRECT_OLLAMA = "http://localhost:11434"
_DIRECT_EMBEDDING = "http://embedding-service:8001"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _manager_strict(base_url: str) -> LocalLLMClientManager:
    return LocalLLMClientManager(
        base_url=base_url,
        default_model="llama3.1:8b",
        selection_file_path=None,
        enforce_proxy=True,
    )


# ---------------------------------------------------------------------------
# Scenario 1: validate_runtime raises for direct model URL in strict mode
# ---------------------------------------------------------------------------


class TestStrictModeModelFailFast:
    def test_direct_ollama_url_raises_in_strict_mode(self):
        """Startup must fail (not silently fallback) when direct URL configured."""
        mgr = _manager_strict(_DIRECT_OLLAMA)
        with pytest.raises(RuntimeError, match="modal-proxy"):
            mgr.validate_runtime()

    def test_empty_base_url_raises_in_strict_mode(self):
        """Missing endpoint raises a clear error — no silent local init."""
        mgr = LocalLLMClientManager(
            base_url="",
            default_model="llama3.1:8b",
            selection_file_path=None,
            enforce_proxy=False,  # enforce_proxy not needed; empty URL always fails
        )
        with pytest.raises(RuntimeError, match="No local LLM endpoint"):
            mgr.validate_runtime()

    def test_proxy_url_does_not_raise_in_strict_mode(self):
        """Proxy URL passes strict validation — normal Render startup path."""
        mgr = _manager_strict(_PROXY_URL)
        mgr.validate_runtime()

    def test_error_message_names_expected_pattern(self):
        """Error message must be actionable: name the expected URL pattern."""
        mgr = _manager_strict(_DIRECT_OLLAMA)
        with pytest.raises(RuntimeError) as exc_info:
            mgr.validate_runtime()
        msg = str(exc_info.value)
        assert (
            "modal-proxy" in msg or "localhost:10000/model" in msg
        ), f"Error should name expected URL pattern; got: {msg!r}"


# ---------------------------------------------------------------------------
# Scenario 2: Env contract validator blocks deploy for missing strict flags
# ---------------------------------------------------------------------------


class TestStrictModeFlagsDeployGate:
    def _minimal_valid_env(self):
        from src.utils.render_env_contract import REQUIRED_KEYS

        env = dict.fromkeys(REQUIRED_KEYS, "placeholder")
        env.update(
            {
                "DATABASE_URL": "postgresql://user:pass@host/db",
                "SUPABASE_URL": "https://test.supabase.co",
                "SUPABASE_KEY": "key",
                "MODAL_OLLAMA_ENDPOINT": _PROXY_URL,
                "MODAL_EMBEDDING_ENDPOINT": "http://vecinita-modal-proxy-v1:10000/embedding",
                "OLLAMA_BASE_URL": _PROXY_URL,
                "EMBEDDING_SERVICE_URL": "http://vecinita-modal-proxy-v1:10000/embedding",
                "PROXY_AUTH_TOKEN": "tok",
                "VITE_BACKEND_URL": "https://vecinita-gateway.onrender.com",
                "VITE_GATEWAY_URL": "https://vecinita-gateway.onrender.com",
                "ALLOWED_ORIGINS": "https://vecinita-frontend.onrender.com",
                "AGENT_ENFORCE_PROXY": "true",
                "RENDER_REMOTE_INFERENCE_ONLY": "true",
            }
        )
        return env

    def test_deploy_gate_blocks_when_enforce_proxy_false(self):
        from src.utils.render_env_contract import validate_shared_render_env

        env = self._minimal_valid_env()
        env["AGENT_ENFORCE_PROXY"] = "false"
        result = validate_shared_render_env(env)
        assert not result.ok
        assert any("AGENT_ENFORCE_PROXY" in e for e in result.errors)

    def test_deploy_gate_blocks_when_remote_only_false(self):
        from src.utils.render_env_contract import validate_shared_render_env

        env = self._minimal_valid_env()
        env["RENDER_REMOTE_INFERENCE_ONLY"] = "false"
        result = validate_shared_render_env(env)
        assert not result.ok
        assert any("RENDER_REMOTE_INFERENCE_ONLY" in e for e in result.errors)

    def test_deploy_gate_passes_when_both_strict_flags_set(self):
        from src.utils.render_env_contract import validate_shared_render_env

        env = self._minimal_valid_env()
        result = validate_shared_render_env(env)
        assert result.ok, f"Deploy gate should pass; errors: {result.errors}"


# ---------------------------------------------------------------------------
# Scenario 3: service_endpoints strict mode gating
# ---------------------------------------------------------------------------


class TestServiceEndpointsStrictModeGating:
    def test_strict_mode_detected_from_env_flags(self, monkeypatch):
        monkeypatch.setenv("AGENT_ENFORCE_PROXY", "true")
        monkeypatch.setenv("RENDER_REMOTE_INFERENCE_ONLY", "true")

        import src.service_endpoints as ep

        importlib.reload(ep)
        assert ep.is_render_strict_mode() is True

    def test_no_strict_mode_when_flags_absent(self, monkeypatch):
        monkeypatch.delenv("AGENT_ENFORCE_PROXY", raising=False)
        monkeypatch.delenv("RENDER_REMOTE_INFERENCE_ONLY", raising=False)

        import src.service_endpoints as ep

        importlib.reload(ep)
        assert ep.is_render_strict_mode() is False

    def test_strict_mode_with_render_env_simulated(self, monkeypatch):
        """Simulate full Render env: both Render detection and strict flags set."""
        monkeypatch.setenv("RENDER", "true")
        monkeypatch.setenv("RENDER_SERVICE_ID", "srv-e2e-strict")
        monkeypatch.setenv("AGENT_ENFORCE_PROXY", "true")
        monkeypatch.setenv("RENDER_REMOTE_INFERENCE_ONLY", "true")

        import src.service_endpoints as ep

        importlib.reload(ep)
        assert ep.is_render() is True
        assert ep.is_render_strict_mode() is True


# ---------------------------------------------------------------------------
# Scenario 4: proxy endpoint consistent across config and service_endpoints
# ---------------------------------------------------------------------------


class TestProxyEndpointConsistency:
    def test_model_endpoint_consistent_between_config_and_service_endpoints(self, monkeypatch):
        """Config and service_endpoints must resolve MODEL_ENDPOINT identically."""
        monkeypatch.setenv("RENDER", "true")
        monkeypatch.delenv("MODAL_OLLAMA_ENDPOINT", raising=False)
        monkeypatch.delenv("OLLAMA_BASE_URL", raising=False)

        import src.config as cfg
        import src.service_endpoints as ep

        importlib.reload(cfg)
        importlib.reload(ep)

        assert ep.MODEL_ENDPOINT == cfg.OLLAMA_BASE_URL, (
            f"service_endpoints.MODEL_ENDPOINT ({ep.MODEL_ENDPOINT!r}) must match "
            f"config.OLLAMA_BASE_URL ({cfg.OLLAMA_BASE_URL!r})"
        )

    def test_embedding_endpoint_consistent_between_config_and_service_endpoints(self, monkeypatch):
        monkeypatch.setenv("RENDER", "true")
        monkeypatch.delenv("MODAL_EMBEDDING_ENDPOINT", raising=False)
        monkeypatch.delenv("EMBEDDING_SERVICE_URL", raising=False)

        import src.config as cfg
        import src.service_endpoints as ep

        importlib.reload(cfg)
        importlib.reload(ep)

        assert ep.EMBEDDING_ENDPOINT == cfg.EMBEDDING_SERVICE_URL
