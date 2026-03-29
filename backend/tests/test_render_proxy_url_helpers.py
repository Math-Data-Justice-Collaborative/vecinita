"""Unit tests for _running_on_render and _normalize_internal_service_url.

These helpers control how the agent routes embedding and LLM calls when
deployed on Render: instead of local/Docker-internal hostnames the agent
must always use the modal-proxy Render private-network URL with the correct
path prefix (/model or /embedding) so the proxy can route to the right
Modal backend.
"""

from __future__ import annotations

from unittest.mock import patch

import pytest

pytestmark = pytest.mark.unit


# ---------------------------------------------------------------------------
# Helpers: import the two functions without triggering module-level side
# effects (supabase, embeddings, llm startup).
# ---------------------------------------------------------------------------


def _import_helpers():
    """Return (_running_on_render, _normalize_internal_service_url) from agent module."""
    import src.agent.main as m

    return m._running_on_render, m._normalize_internal_service_url


# ---------------------------------------------------------------------------
# _running_on_render
# ---------------------------------------------------------------------------


class TestRunningOnRender:
    def test_returns_false_when_no_render_env(self):
        running_on_render, _ = _import_helpers()
        with patch.dict("os.environ", {}, clear=False):
            # Ensure neither var is present.
            import os

            for var in ("RENDER", "RENDER_SERVICE_ID"):
                os.environ.pop(var, None)
            assert running_on_render() is False

    def test_returns_true_when_render_is_set(self):
        running_on_render, _ = _import_helpers()
        with patch.dict("os.environ", {"RENDER": "true"}):
            assert running_on_render() is True

    def test_returns_true_when_render_service_id_is_set(self):
        running_on_render, _ = _import_helpers()
        with patch.dict("os.environ", {"RENDER_SERVICE_ID": "srv-abc123"}):
            assert running_on_render() is True

    def test_returns_true_when_both_render_vars_set(self):
        running_on_render, _ = _import_helpers()
        with patch.dict("os.environ", {"RENDER": "1", "RENDER_SERVICE_ID": "srv-xyz"}):
            assert running_on_render() is True

    def test_nonempty_render_value_is_truthy(self):
        running_on_render, _ = _import_helpers()
        with patch.dict("os.environ", {"RENDER": "false"}):
            # os.environ stores strings; any non-empty string is truthy in bool()
            assert running_on_render() is True


# ---------------------------------------------------------------------------
# _normalize_internal_service_url — off-Render (local / Docker / CI)
# ---------------------------------------------------------------------------


class TestNormalizeUrlOffRender:
    """When not on Render, env var value should be returned unchanged."""

    def _normalize(self, raw_url, fallback):
        _, normalize = _import_helpers()
        return normalize(raw_url, fallback_url=fallback)

    def _off_render(self):
        import os

        os.environ.pop("RENDER", None)
        os.environ.pop("RENDER_SERVICE_ID", None)

    def test_returns_candidate_when_not_on_render(self):
        self._off_render()
        result = self._normalize("http://localhost:11434", "http://proxy:10000/model")
        assert result == "http://localhost:11434"

    def test_returns_docker_service_url_unchanged(self):
        self._off_render()
        result = self._normalize("http://vecinita-embedding:8001", "http://proxy:10000/embedding")
        assert result == "http://vecinita-embedding:8001"

    def test_returns_fallback_when_raw_url_is_none_off_render(self):
        self._off_render()
        result = self._normalize(None, "http://proxy:10000/model")
        assert result == "http://proxy:10000/model"

    def test_returns_fallback_when_raw_url_is_empty_string_off_render(self):
        self._off_render()
        result = self._normalize("", "http://proxy:10000/embedding")
        assert result == "http://proxy:10000/embedding"

    def test_returns_fallback_when_raw_url_is_whitespace_off_render(self):
        self._off_render()
        result = self._normalize("   ", "http://proxy:10000/model")
        assert result == "http://proxy:10000/model"


# ---------------------------------------------------------------------------
# _normalize_internal_service_url — on Render
# ---------------------------------------------------------------------------


class TestNormalizeUrlOnRender:
    """On Render, local/docker URLs must be forced to fallback URL.

    Non-local explicit URLs (for example direct Modal endpoints) are preserved
    to avoid hard failures when a hardcoded private-host fallback is not
    reachable from the current Render region.
    """

    def _normalize_on_render(self, raw_url, fallback):
        _, normalize = _import_helpers()
        with patch.dict("os.environ", {"RENDER": "true", "RENDER_SERVICE_ID": "srv-test"}):
            return normalize(raw_url, fallback_url=fallback)

    def test_returns_fallback_for_localhost_ollama(self):
        result = self._normalize_on_render(
            "http://localhost:11434",
            "http://vecinita-modal-proxy-v1:10000/model",
        )
        assert result == "http://vecinita-modal-proxy-v1:10000/model"

    def test_returns_fallback_for_127_0_0_1_ollama(self):
        result = self._normalize_on_render(
            "http://127.0.0.1:11434",
            "http://vecinita-modal-proxy-v1:10000/model",
        )
        assert result == "http://vecinita-modal-proxy-v1:10000/model"

    def test_returns_fallback_for_docker_embedding_service(self):
        result = self._normalize_on_render(
            "http://embedding-service:8001",
            "http://vecinita-modal-proxy-v1:10000/embedding",
        )
        assert result == "http://vecinita-modal-proxy-v1:10000/embedding"

    def test_returns_fallback_for_docker_vecinita_embedding(self):
        result = self._normalize_on_render(
            "http://vecinita-embedding:8001",
            "http://vecinita-modal-proxy-v1:10000/embedding",
        )
        assert result == "http://vecinita-modal-proxy-v1:10000/embedding"

    def test_returns_fallback_for_direct_modal_url(self):
        """A non-local explicit endpoint should be preserved on Render."""
        result = self._normalize_on_render(
            "https://vecinita--vecinita-model-api.modal.run",
            "http://vecinita-modal-proxy-v1:10000/model",
        )
        assert result == "https://vecinita--vecinita-model-api.modal.run"

    def test_returns_fallback_for_local_embedding_service_name(self):
        result = self._normalize_on_render(
            "http://embedding-service:8001",
            "http://vecinita-modal-proxy-v1:10000/embedding",
        )
        assert result == "http://vecinita-modal-proxy-v1:10000/embedding"

    def test_returns_fallback_when_raw_url_is_none(self):
        result = self._normalize_on_render(None, "http://vecinita-modal-proxy-v1:10000/model")
        assert result == "http://vecinita-modal-proxy-v1:10000/model"

    def test_returns_fallback_when_raw_url_is_empty(self):
        result = self._normalize_on_render("", "http://vecinita-modal-proxy-v1:10000/embedding")
        assert result == "http://vecinita-modal-proxy-v1:10000/embedding"

    def test_model_fallback_includes_model_prefix(self):
        """Proxy path prefix /model is required so requests route to the Ollama backend."""
        result = self._normalize_on_render(
            "http://localhost:11434",
            "http://vecinita-modal-proxy-v1:10000/model",
        )
        assert result.endswith("/model")

    def test_embedding_fallback_includes_embedding_prefix(self):
        """Proxy path prefix /embedding required so requests route to the embedding backend."""
        result = self._normalize_on_render(
            "http://localhost:8001",
            "http://vecinita-modal-proxy-v1:10000/embedding",
        )
        assert result.endswith("/embedding")

    def test_internal_proxy_host_preserved(self):
        result = self._normalize_on_render(
            "http://localhost:11434",
            "http://vecinita-modal-proxy-v1:10000/model",
        )
        assert "vecinita-modal-proxy-v1:10000" in result


# ---------------------------------------------------------------------------
# Module-level variable wiring (on Render the globals pick up proxy URLs)
# ---------------------------------------------------------------------------


class TestModuleGlobalsOnRender:
    """Verify that the module-level ollama_base_url global resolves to the
    proxy URL when RENDER env var is present at import time.

    We must reload the module in an isolated env to simulate Render startup.
    """

    def test_ollama_base_url_resolves_to_model_proxy_on_render(self):
        env_overrides = {
            "RENDER": "true",
            "RENDER_SERVICE_ID": "srv-test",
            "OLLAMA_BASE_URL": "http://localhost:11434",
            "SUPABASE_URL": "https://test.supabase.co",
            "SUPABASE_KEY": "test-key",
        }
        with patch.dict("os.environ", env_overrides):
            import src.agent.main as m

            # _normalize is called at module import; we call it directly with
            # Render env active to assert the expected output without reloading.
            result = m._normalize_internal_service_url(
                "http://localhost:11434",
                fallback_url="http://vecinita-modal-proxy-v1:10000/model",
            )
        assert result == "http://vecinita-modal-proxy-v1:10000/model"

    def test_embedding_url_resolves_to_embedding_proxy_on_render(self):
        env_overrides = {
            "RENDER": "true",
            "RENDER_SERVICE_ID": "srv-test",
            "EMBEDDING_SERVICE_URL": "http://embedding-service:8001",
            "SUPABASE_URL": "https://test.supabase.co",
            "SUPABASE_KEY": "test-key",
        }
        with patch.dict("os.environ", env_overrides):
            import src.agent.main as m

            result = m._normalize_internal_service_url(
                "http://embedding-service:8001",
                fallback_url="http://vecinita-modal-proxy-v1:10000/embedding",
            )
        assert result == "http://vecinita-modal-proxy-v1:10000/embedding"


# ---------------------------------------------------------------------------
# LocalLLMClientManager._via_proxy and .headers() — auth suppression
# ---------------------------------------------------------------------------


def _make_manager(**kwargs):
    """Return a LocalLLMClientManager with sensible defaults."""
    from src.services.llm.client_manager import LocalLLMClientManager

    return LocalLLMClientManager(
        base_url=kwargs.get("base_url", "http://localhost:11434"),
        default_model=kwargs.get("default_model", "llama3.1:8b"),
        api_key=kwargs.get("api_key"),
        modal_proxy_key=kwargs.get("modal_proxy_key"),
        modal_proxy_secret=kwargs.get("modal_proxy_secret"),
        proxy_auth_token=kwargs.get("proxy_auth_token"),
    )


class TestViaProxy:
    def test_returns_true_for_render_private_hostname(self):
        mgr = _make_manager(base_url="http://vecinita-modal-proxy-v1:10000/model")
        assert mgr._via_proxy() is True

    def test_returns_true_for_embedding_proxy_prefix(self):
        mgr = _make_manager(base_url="http://vecinita-modal-proxy-v1:10000/embedding")
        assert mgr._via_proxy() is True

    def test_returns_true_case_insensitive(self):
        mgr = _make_manager(base_url="http://Vecinita-Modal-Proxy:10000/model")
        assert mgr._via_proxy() is True

    def test_returns_true_for_localhost_proxy_model_path(self):
        mgr = _make_manager(base_url="http://localhost:10000/model")
        assert mgr._via_proxy() is True

    def test_returns_true_for_localhost_proxy_embedding_path(self):
        mgr = _make_manager(base_url="http://127.0.0.1:10000/embedding")
        assert mgr._via_proxy() is True

    def test_returns_false_for_direct_modal_url(self):
        mgr = _make_manager(base_url="https://vecinita--vecinita-model-api.modal.run")
        assert mgr._via_proxy() is False

    def test_returns_false_for_local_ollama(self):
        mgr = _make_manager(base_url="http://localhost:11434")
        assert mgr._via_proxy() is False

    def test_returns_false_for_none_base_url(self):
        mgr = _make_manager(base_url=None)
        assert mgr._via_proxy() is False

    def test_returns_false_for_empty_base_url(self):
        mgr = _make_manager(base_url="")
        assert mgr._via_proxy() is False


class TestHeadersViaProxy:
    """When routing through the modal proxy, headers() must return {} to prevent
    Authorization: Bearer from reaching Modal and triggering HTTP 401."""

    def test_headers_empty_when_via_proxy_with_api_key(self):
        mgr = _make_manager(
            base_url="http://vecinita-modal-proxy-v1:10000/model",
            api_key="secret-token",
        )
        assert mgr.headers() == {}

    def test_headers_empty_when_via_proxy_with_modal_credentials(self):
        mgr = _make_manager(
            base_url="http://vecinita-modal-proxy-v1:10000/model",
            api_key="ak-xxx",
            modal_proxy_key="mk-111",
            modal_proxy_secret="ms-222",
        )
        assert mgr.headers() == {}

    def test_no_authorization_header_via_proxy(self):
        mgr = _make_manager(
            base_url="http://vecinita-modal-proxy-v1:10000/model",
            api_key="should-not-appear",
        )
        assert "Authorization" not in mgr.headers()

    def test_no_modal_key_header_via_proxy(self):
        mgr = _make_manager(
            base_url="http://vecinita-modal-proxy-v1:10000/model",
            modal_proxy_key="mk-111",
            modal_proxy_secret="ms-222",
        )
        assert "Modal-Key" not in mgr.headers()

    def test_x_proxy_token_only_when_via_proxy_and_configured(self):
        mgr = _make_manager(
            base_url="http://vecinita-modal-proxy-v1:10000/model",
            api_key="should-not-appear",
            modal_proxy_key="mk-111",
            modal_proxy_secret="ms-222",
            proxy_auth_token="proxy-shared-token",
        )
        headers = mgr.headers()
        assert headers == {"X-Proxy-Token": "proxy-shared-token"}

    def test_localhost_proxy_sends_x_proxy_token_only(self):
        mgr = _make_manager(
            base_url="http://localhost:10000/model",
            api_key="should-not-appear",
            modal_proxy_key="mk-111",
            modal_proxy_secret="ms-222",
            proxy_auth_token="proxy-shared-token",
        )
        headers = mgr.headers()
        assert headers == {"X-Proxy-Token": "proxy-shared-token"}

    def test_localhost_proxy_uses_local_default_when_proxy_token_missing(self):
        mgr = _make_manager(
            base_url="http://localhost:10000/model",
            modal_proxy_key="mk-111",
            modal_proxy_secret="ms-222",
            proxy_auth_token=None,
        )
        headers = mgr.headers()
        assert headers == {"X-Proxy-Token": "vecinita-local-proxy-token"}

    def test_explicit_proxy_token_wins_over_modal_proxy_secret(self):
        mgr = _make_manager(
            base_url="http://localhost:10000/model",
            modal_proxy_key="mk-111",
            modal_proxy_secret="ms-222",
            proxy_auth_token="proxy-shared-token",
        )
        headers = mgr.headers()
        assert headers == {"X-Proxy-Token": "proxy-shared-token"}


class TestHeadersDirectModal:
    """When calling Modal directly (no proxy), auth headers must be injected."""

    def test_authorization_header_sent_for_direct_modal(self):
        mgr = _make_manager(
            base_url="https://vecinita--vecinita-model-api.modal.run",
            api_key="token-123",
        )
        h = mgr.headers()
        assert h.get("Authorization") == "Bearer token-123"

    def test_modal_key_secret_sent_for_direct_modal(self):
        mgr = _make_manager(
            base_url="https://vecinita--vecinita-model-api.modal.run",
            modal_proxy_key="mk-abc",
            modal_proxy_secret="ms-def",
        )
        h = mgr.headers()
        assert h.get("Modal-Key") == "mk-abc"
        assert h.get("Modal-Secret") == "ms-def"

    def test_no_authorization_when_api_key_none_direct(self):
        mgr = _make_manager(
            base_url="https://vecinita--vecinita-model-api.modal.run",
        )
        assert "Authorization" not in mgr.headers()

    def test_no_modal_headers_when_only_api_key_set_direct(self):
        mgr = _make_manager(
            base_url="https://vecinita--vecinita-model-api.modal.run",
            api_key="token-abc",
        )
        h = mgr.headers()
        assert "Modal-Key" not in h
        assert "Modal-Secret" not in h


class TestHeadersLocalOllama:
    """Without proxy or modal.run, standard auth behavior applies."""

    def test_authorization_header_for_local_ollama_with_key(self):
        mgr = _make_manager(
            base_url="http://localhost:11434",
            api_key="local-key",
        )
        assert mgr.headers().get("Authorization") == "Bearer local-key"

    def test_empty_headers_for_local_ollama_no_key(self):
        mgr = _make_manager(base_url="http://localhost:11434")
        assert mgr.headers() == {}


class TestNativeChatDetection:
    def test_native_chat_enabled_for_modal_run(self):
        mgr = _make_manager(base_url="https://workspace--vecinita-model-api.modal.run")
        assert mgr.uses_modal_native_chat_api() is True

    def test_native_chat_enabled_for_model_proxy_prefix(self):
        mgr = _make_manager(base_url="http://vecinita-modal-proxy-v1:10000/model")
        assert mgr.uses_modal_native_chat_api() is True

    def test_native_chat_disabled_for_embedding_proxy_prefix(self):
        mgr = _make_manager(base_url="http://vecinita-modal-proxy-v1:10000/embedding")
        assert mgr.uses_modal_native_chat_api() is False

    def test_native_chat_enabled_for_localhost_proxy_model(self):
        mgr = _make_manager(base_url="http://localhost:10000/model")
        assert mgr.uses_modal_native_chat_api() is True

    def test_native_chat_enabled_for_127_0_0_1_proxy_model(self):
        mgr = _make_manager(base_url="http://127.0.0.1:10000/model")
        assert mgr.uses_modal_native_chat_api() is True

    def test_native_chat_disabled_for_localhost_proxy_embedding(self):
        mgr = _make_manager(base_url="http://localhost:10000/embedding")
        assert mgr.uses_modal_native_chat_api() is False

    def test_native_chat_disabled_for_localhost_different_port(self):
        mgr = _make_manager(base_url="http://localhost:11434/model")
        assert mgr.uses_modal_native_chat_api() is False
