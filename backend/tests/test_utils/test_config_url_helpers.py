"""Unit tests for URL helpers in ``src.config`` (Render / Modal integration)."""

from __future__ import annotations

import pytest

from src.config import normalize_agent_service_url, rewrite_deprecated_modal_embedding_host

pytestmark = pytest.mark.unit


class TestRewriteDeprecatedModalEmbeddingHost:
    @pytest.mark.parametrize(
        ("input_url", "expected_suffix"),
        [
            (
                "https://vecinita--vecinita-embedding-embeddingservicecontainer-api.modal.run",
                "https://vecinita--vecinita-embedding-embedding-web-app.modal.run",
            ),
            (
                "https://vecinita--vecinita-embedding-embeddingservicecontainer-api.modal.run/",
                "https://vecinita--vecinita-embedding-embedding-web-app.modal.run",
            ),
        ],
    )
    def test_rewrites_legacy_container_host_to_web_app(self, input_url: str, expected_suffix: str):
        out = rewrite_deprecated_modal_embedding_host(input_url)
        assert out is not None
        assert out.rstrip("/") == expected_suffix.rstrip("/")

    def test_preserves_non_default_port(self):
        url = "https://vecinita--vecinita-embedding-embeddingservicecontainer-api.modal.run:443"
        out = rewrite_deprecated_modal_embedding_host(url)
        assert out is not None
        assert ":443" in out
        assert "embedding-web-app" in out

    @pytest.mark.parametrize(
        "input_url",
        [
            "https://vecinita--vecinita-embedding-embedding-web-app.modal.run",
            "https://other--other-api.modal.run",
            "https://example.com/embed",
            "",
        ],
    )
    def test_returns_none_when_no_rewrite_applies(self, input_url: str):
        assert rewrite_deprecated_modal_embedding_host(input_url) is None


class TestNormalizeAgentServiceUrl:
    def test_empty_uses_default(self):
        assert normalize_agent_service_url(None) == "http://localhost:8000"
        assert normalize_agent_service_url("") == "http://localhost:8000"
        assert normalize_agent_service_url("   ") == "http://localhost:8000"

    def test_custom_default(self):
        assert normalize_agent_service_url(None, default="http://agent:9000") == "http://agent:9000"

    @pytest.mark.parametrize(
        ("raw", "expected"),
        [
            ("http://localhost:8000", "http://localhost:8000"),
            ("https://agent.onrender.com", "https://agent.onrender.com"),
            ("vecinita-agent:10000", "http://vecinita-agent:10000"),
            ("gateway-internal", "http://gateway-internal"),
        ],
    )
    def test_prepends_http_when_scheme_missing(self, raw: str, expected: str):
        assert normalize_agent_service_url(raw) == expected
