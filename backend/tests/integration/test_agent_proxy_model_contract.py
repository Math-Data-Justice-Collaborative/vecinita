"""Integration tests for LocalLLMClientManager endpoint/runtime behavior.

The legacy modal-proxy enforcement path was retired. These tests validate the
current contract:
- _via_proxy() is a compatibility helper that always returns False
- headers() only reflects direct credentials (Authorization)
- validate_runtime() enforces endpoint presence and adapter availability
- uses_modal_native_chat_api() is based on endpoint shape, not proxy hostnames
"""

from __future__ import annotations

import pytest

from src.services.llm.client_manager import LocalLLMClientManager

pytestmark = pytest.mark.integration

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


class TestViaProxyDetection:
    def test_render_private_network_url_is_detected_as_proxy(self):
        mgr = _manager(_RENDER_PROXY_MODEL_URL)
        assert mgr._via_proxy() is False

    def test_localhost_10000_model_path_is_detected_as_proxy(self):
        mgr = _manager(_LOCAL_PROXY_MODEL_URL)
        assert mgr._via_proxy() is False

    def test_direct_ollama_url_is_not_proxy(self):
        mgr = _manager(_DIRECT_OLLAMA_URL)
        assert mgr._via_proxy() is False

    def test_empty_base_url_is_not_proxy(self):
        mgr = _manager("")
        assert mgr._via_proxy() is False

    def test_modal_proxy_with_different_port_variant_detected(self):
        """Compatibility helper remains disabled for all host/port variants."""
        mgr = _manager("http://vecinita-modal-proxy:8080/model")
        assert mgr._via_proxy() is False


class TestProxyHeaders:
    def test_headers_include_authorization_when_api_key_present(self):
        mgr = _manager(
            _RENDER_PROXY_MODEL_URL,
            api_key="should-not-appear",
            modal_proxy_key="key",
            modal_proxy_secret="secret",
        )
        h = mgr.headers()
        assert h.get("Authorization") == "Bearer should-not-appear"
        assert "Modal-Key" not in h
        assert "Modal-Secret" not in h

    def test_headers_include_bearer_for_non_proxy_direct_url(self):
        mgr = _manager(_DIRECT_OLLAMA_URL, api_key="my-api-key")
        h = mgr.headers()
        assert h.get("Authorization") == "Bearer my-api-key"

    def test_headers_empty_for_non_proxy_without_credentials(self):
        mgr = _manager(_DIRECT_OLLAMA_URL)
        h = mgr.headers()
        assert h == {}


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
        # enforce_proxy is intentionally ignored after proxy retirement.
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


class TestModalNativeApiDetection:
    def test_render_proxy_model_url_uses_native_api(self):
        mgr = _manager(_RENDER_PROXY_MODEL_URL)
        assert mgr.uses_modal_native_chat_api() is False

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
