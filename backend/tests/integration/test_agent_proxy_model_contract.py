"""Integration tests: Agent → modal-proxy model endpoint contract.

Verifies the full proxy routing chain from LocalLLMClientManager:
- base_url detection correctly identifies proxy vs direct endpoints
- headers() omits auth when routing via proxy (proxy injects Modal credentials)
- headers() includes X-Proxy-Token when proxy_auth_token is provided
- validate_runtime() raises when enforce_proxy=True and non-proxy URL is set
- validate_runtime() passes when enforce_proxy=True and proxy URL is set
- uses_modal_native_chat_api() returns True for proxy model path
- Proxy hostname forms (Render private network and localhost:10000) are both detected
"""

from __future__ import annotations

import pytest

from src.services.llm.client_manager import LocalLLMClientManager

pytestmark = pytest.mark.integration

# ---------------------------------------------------------------------------
# Canonical proxy endpoints
# ---------------------------------------------------------------------------

_RENDER_PROXY_MODEL_URL = "http://vecinita-modal-proxy-v1:10000/model"
_LOCAL_PROXY_MODEL_URL = "http://localhost:10000/model"
_DIRECT_OLLAMA_URL = "http://localhost:11434"


def _manager(base_url: str, **kwargs) -> LocalLLMClientManager:
    """Construct a manager without file-based selection side-effects."""
    return LocalLLMClientManager(
        base_url=base_url,
        default_model="llama3.1:8b",
        selection_file_path=None,
        **kwargs,
    )


# ---------------------------------------------------------------------------
# _via_proxy detection
# ---------------------------------------------------------------------------


class TestViaProxyDetection:
    def test_render_private_network_url_is_detected_as_proxy(self):
        mgr = _manager(_RENDER_PROXY_MODEL_URL)
        assert mgr._via_proxy() is True

    def test_localhost_10000_model_path_is_detected_as_proxy(self):
        mgr = _manager(_LOCAL_PROXY_MODEL_URL)
        assert mgr._via_proxy() is True

    def test_direct_ollama_url_is_not_proxy(self):
        mgr = _manager(_DIRECT_OLLAMA_URL)
        assert mgr._via_proxy() is False

    def test_empty_base_url_is_not_proxy(self):
        mgr = _manager("")
        assert mgr._via_proxy() is False

    def test_modal_proxy_with_different_port_variant_detected(self):
        """Any hostname containing 'modal-proxy' must resolve as proxy."""
        mgr = _manager("http://vecinita-modal-proxy:8080/model")
        assert mgr._via_proxy() is True


# ---------------------------------------------------------------------------
# headers() — proxy path must not forward Authorization or Modal credentials
# ---------------------------------------------------------------------------


class TestProxyHeaders:
    def test_headers_are_empty_dict_when_via_proxy_and_no_token(self):
        """Proxy injects Modal-Key/Secret server-side; client must send nothing."""
        mgr = _manager(
            _RENDER_PROXY_MODEL_URL,
            api_key="should-not-appear",
            modal_proxy_key="key",
            modal_proxy_secret="secret",
        )
        h = mgr.headers()
        assert "Authorization" not in h, "Must not forward Bearer token via proxy"
        assert "Modal-Key" not in h, "Must not forward Modal-Key via proxy"
        assert "Modal-Secret" not in h, "Must not forward Modal-Secret via proxy"

    def test_headers_include_x_proxy_token_when_provided(self):
        mgr = _manager(
            _RENDER_PROXY_MODEL_URL,
            proxy_auth_token="my-proxy-token-abc",
        )
        h = mgr.headers()
        assert h.get("X-Proxy-Token") == "my-proxy-token-abc"

    def test_local_proxy_gets_fallback_token_when_no_token_configured(self):
        """localhost:10000 is treated as local dev proxy and gets a fallback token."""
        mgr = _manager(_LOCAL_PROXY_MODEL_URL)
        h = mgr.headers()
        assert h.get("X-Proxy-Token") == "vecinita-local-proxy-token"

    def test_headers_include_bearer_for_non_proxy_direct_url(self):
        mgr = _manager(_DIRECT_OLLAMA_URL, api_key="my-api-key")
        h = mgr.headers()
        assert h.get("Authorization") == "Bearer my-api-key"

    def test_headers_empty_for_non_proxy_without_credentials(self):
        mgr = _manager(_DIRECT_OLLAMA_URL)
        h = mgr.headers()
        assert h == {}


# ---------------------------------------------------------------------------
# validate_runtime() — enforce_proxy=True blocks non-proxy URLs
# ---------------------------------------------------------------------------


class TestEnforceProxyRuntime:
    def test_validate_runtime_passes_with_proxy_url_and_enforce_proxy(self):
        mgr = _manager(_RENDER_PROXY_MODEL_URL, enforce_proxy=True)
        # Should not raise.
        mgr.validate_runtime()

    def test_validate_runtime_passes_with_local_proxy_and_enforce_proxy(self):
        mgr = _manager(_LOCAL_PROXY_MODEL_URL, enforce_proxy=True)
        mgr.validate_runtime()

    def test_validate_runtime_raises_with_direct_url_and_enforce_proxy(self):
        mgr = _manager(_DIRECT_OLLAMA_URL, enforce_proxy=True)
        with pytest.raises(RuntimeError, match="modal-proxy"):
            mgr.validate_runtime()

    def test_validate_runtime_raises_with_no_base_url_and_enforce_proxy(self):
        """Empty base_url raises: endpoint not configured and also not via proxy."""
        mgr = _manager("", enforce_proxy=False)
        with pytest.raises(RuntimeError, match="No local LLM endpoint"):
            mgr.validate_runtime()

    def test_validate_runtime_passes_with_direct_url_when_enforce_proxy_false(self):
        mgr = _manager(_DIRECT_OLLAMA_URL, enforce_proxy=False)
        # Should not raise (allows direct URL when proxy not enforced).
        mgr.validate_runtime()


# ---------------------------------------------------------------------------
# uses_modal_native_chat_api() — proxy model path uses native /chat API
# ---------------------------------------------------------------------------


class TestModalNativeApiDetection:
    def test_render_proxy_model_url_uses_native_api(self):
        mgr = _manager(_RENDER_PROXY_MODEL_URL)
        assert mgr.uses_modal_native_chat_api() is True

    def test_local_proxy_model_url_uses_native_api(self):
        mgr = _manager(_LOCAL_PROXY_MODEL_URL)
        assert mgr.uses_modal_native_chat_api() is True

    def test_direct_ollama_url_does_not_use_native_api(self):
        mgr = _manager(_DIRECT_OLLAMA_URL)
        assert mgr.uses_modal_native_chat_api() is False

    def test_modal_run_url_uses_native_api(self):
        mgr = _manager("https://my-app--llm.modal.run")
        assert mgr.uses_modal_native_chat_api() is True


# ---------------------------------------------------------------------------
# config_payload() — reflects proxy routing in provider label
# ---------------------------------------------------------------------------


class TestConfigPayload:
    def test_config_payload_provider_label_indicates_modal(self):
        mgr = _manager(_RENDER_PROXY_MODEL_URL)
        payload = mgr.config_payload()
        providers = payload["providers"]
        assert len(providers) == 1
        label = providers[0].get("label", "")
        assert "Modal" in label, f"Expected 'Modal' in provider label, got: {label!r}"

    def test_config_payload_default_provider_is_ollama(self):
        mgr = _manager(_RENDER_PROXY_MODEL_URL)
        payload = mgr.config_payload()
        assert payload["defaultProvider"] == "ollama"
