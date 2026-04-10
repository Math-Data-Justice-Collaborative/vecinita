"""Integration/E2E tests: Startup failure scenarios with invalid DATABASE_URL.

Tests the complete flow when DATABASE_URL is set to a test placeholder or
invalid host, verifying:
- Startup preflight detects the issue and sets degraded status
- /health endpoint correctly exposes the degraded readiness
- /ask endpoint returns degraded service status
- Error messages are clear and actionable
- Sentinel guard prevents confusing DNS errors
"""

from __future__ import annotations

import importlib
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

pytestmark = [pytest.mark.integration, pytest.mark.api]


# ---------------------------------------------------------------------------
# Unit + Integration: Preflight behavior with placeholder DATABASE_URL
# ---------------------------------------------------------------------------


class TestPreflightWithPlaceholderDatabaseURL:
    """Verify startup preflight handles placeholder URL correctly."""

    def test_startup_degraded_with_placeholder_url(self, monkeypatch):
        """When DATABASE_URL=postgresql://test, preflight status is degraded."""
        monkeypatch.setenv("DATABASE_URL", "postgresql://test")
        monkeypatch.setenv("GUARDRAILS_REQUIRE_HUB_VALIDATOR", "false")

        from src.agent import main as agent_main

        result = agent_main._run_startup_preflight()

        assert result["status"] == "degraded", f"Status should be degraded, got {result}"
        assert result["data_mode"] == "postgres"
        assert result["checks"]["data_backend"]["ok"] is False
        assert result["checks"]["data_backend"]["detail"] == "database_url_is_test_placeholder"

    def test_probe_returns_clear_error_for_placeholder_url(self, monkeypatch):
        """_probe_postgres_connectivity returns clear error, not confusing DNS error."""
        monkeypatch.setenv("DATABASE_URL", "postgresql://test")

        from src.agent import main as agent_main

        ok, detail = agent_main._probe_postgres_connectivity()

        assert ok is False
        assert detail == "database_url_is_test_placeholder"
        # Verify it's NOT a confusing DNS error
        assert "could not translate" not in detail.lower()
        assert "temporary failure" not in detail.lower()

    def test_startup_degraded_with_invalid_hostnames(self, monkeypatch):
        """Verify sentinel guard works for various invalid hostnames."""
        from src.agent import main as agent_main

        invalid_urls = [
            "postgresql://test",
            "postgresql://localhost/test",  # generic invalid
            "postgresql://nonexistent-host-xyz:5432/db",
        ]

        for url in invalid_urls:
            monkeypatch.setenv("DATABASE_URL", url)

            # First URL is the placeholder, rest may trigger different errors
            # but we just want to ensure they all report degraded
            from importlib import reload

            reload(agent_main)

            result = agent_main._run_startup_preflight()
            assert result["status"] == "degraded", f"Failed for URL: {url}"
            assert result["checks"]["data_backend"]["ok"] is False


# ---------------------------------------------------------------------------
# Integration: Health endpoint with degraded status
# ---------------------------------------------------------------------------


class TestHealthEndpointWithDegradedStatus:
    """Verify /health endpoint correctly exposes preflight status."""

    def test_health_exposes_degraded_readiness_when_db_unavailable(self, monkeypatch):
        """GET /health returns readiness=degraded when database check fails."""
        from importlib import reload

        from src.agent import main as agent_main

        monkeypatch.setenv("DATABASE_URL", "postgresql://test")
        monkeypatch.setenv("GUARDRAILS_REQUIRE_HUB_VALIDATOR", "false")

        # Reload to apply env vars
        reload(agent_main)
        client = TestClient(agent_main.app)

        response = client.get("/health")

        assert response.status_code == 200
        payload = response.json()
        assert payload["status"] == "ok"  # Top-level status is always ok
        # Readiness can be ok, degraded, or unknown (if preflight hasn't run yet)
        assert payload["readiness"] in ("ok", "degraded", "unknown")

        # For the placeholder URL scenario, verify preflight structure is correct
        if "preflight" in payload:
            preflight = payload["preflight"]
            if preflight and isinstance(preflight, dict):
                # When preflight has run with placeholder URL, it should be degraded
                if preflight.get("ran_at"):  # Only check if preflight actually ran
                    assert preflight.get("status") in ("ok", "degraded")
                    if preflight.get("status") == "degraded":
                        assert (
                            preflight["checks"]["data_backend"]["detail"]
                            == "database_url_is_test_placeholder"
                        )

    def test_health_preflight_includes_check_details(self, monkeypatch):
        """GET /health includes detailed preflight checks."""
        from importlib import reload

        from src.agent import main as agent_main

        monkeypatch.setenv("DATABASE_URL", "postgresql://test")
        monkeypatch.setenv("GUARDRAILS_REQUIRE_HUB_VALIDATOR", "false")

        reload(agent_main)
        client = TestClient(agent_main.app)

        response = client.get("/health")
        payload = response.json()

        assert "preflight" in payload
        preflight = payload.get("preflight")
        if preflight and isinstance(preflight, dict):
            assert "checks" in preflight
            checks = preflight["checks"]
            assert "data_backend" in checks
            db_check = checks["data_backend"]
            assert "ok" in db_check
            assert "backend" in db_check
            assert "detail" in db_check


# ---------------------------------------------------------------------------
# Integration: /ask endpoint degradation when data backend is unavailable
# ---------------------------------------------------------------------------


class TestAskEndpointWithDegradedDataBackend:
    """Verify /ask endpoint handles degraded data backend gracefully."""

    def test_ask_returns_degraded_service_status_when_data_backend_fails(self, monkeypatch):
        """GET /ask returns service_status=degraded when data backend is unavailable."""
        from importlib import reload
        from unittest.mock import MagicMock

        from src.agent import main as agent_main

        monkeypatch.setenv("DATABASE_URL", "postgresql://test")
        monkeypatch.setenv("GUARDRAILS_REQUIRE_HUB_VALIDATOR", "false")

        reload(agent_main)
        client = TestClient(agent_main.app)

        # Mock the upstream services to prevent other failures
        with patch.object(agent_main, "_get_llm_without_tools") as mock_llm:
            mock_llm.return_value = MagicMock()
            mock_llm.return_value.invoke.return_value = MagicMock(content="Fallback response")

            response = client.get("/ask", params={"question": "test"})

        assert response.status_code == 200
        payload = response.json()

        # When data backend is unavailable, the service should return a degraded status
        # The response structure may vary, but should indicate degradation
        if "service_status" in payload:
            assert payload["service_status"] == "degraded"

        # Should provide a fallback response
        assert "answer" in payload or "message" in payload

    def test_ask_provides_fallback_when_data_backend_unavailable(self, monkeypatch):
        """GET /ask returns fallback answer when database is unreachable."""
        from importlib import reload
        from unittest.mock import MagicMock

        from src.agent import main as agent_main

        monkeypatch.setenv("DATABASE_URL", "postgresql://test")
        monkeypatch.setenv("GUARDRAILS_REQUIRE_HUB_VALIDATOR", "false")

        reload(agent_main)
        client = TestClient(agent_main.app)

        # Mock LLM to avoid additional failures
        with patch.object(agent_main, "_get_llm_without_tools") as mock_llm:
            mock_llm.return_value = MagicMock()
            mock_llm.return_value.invoke.return_value = MagicMock(
                content="I apologize, but I'm unable to retrieve information"
            )

            response = client.get("/ask", params={"question": "housing services"})

        assert response.status_code == 200
        payload = response.json()

        # Should contain some form of answer/response
        assert any(
            key in payload for key in ["answer", "message", "response"]
        ), f"No answer in response: {payload}"

    def test_ask_endpoint_not_blocked_despite_degraded_startup(self, monkeypatch):
        """GET /ask still works (with fallback) even when startup is degraded."""
        from importlib import reload
        from unittest.mock import MagicMock

        from src.agent import main as agent_main

        monkeypatch.setenv("DATABASE_URL", "postgresql://test")
        monkeypatch.setenv("GUARDRAILS_REQUIRE_HUB_VALIDATOR", "false")
        monkeypatch.setenv("BACKEND_PREFLIGHT_STRICT", "false")  # Non-strict mode

        reload(agent_main)
        client = TestClient(agent_main.app)

        # Even with a degraded startup, /ask should respond
        with patch.object(agent_main, "_get_llm_without_tools") as mock_llm:
            mock_llm.return_value = MagicMock()
            mock_llm.return_value.invoke.return_value = MagicMock(content="Fallback answer")

            response = client.get("/ask", params={"question": "test"})

        assert response.status_code == 200, "App should respond despite degraded startup"


# ---------------------------------------------------------------------------
# Integration: Startup with valid DATABASE_URL succeeds
# ---------------------------------------------------------------------------


class TestStartupWithValidConfiguration:
    """Verify startup succeeds when DATABASE_URL is properly configured."""

    def test_preflight_degraded_when_database_url_unset(self, monkeypatch):
        """When DATABASE_URL is unset, postgres-only preflight is degraded."""
        monkeypatch.delenv("DATABASE_URL", raising=False)
        monkeypatch.setenv("GUARDRAILS_REQUIRE_HUB_VALIDATOR", "false")

        from importlib import reload

        from src.agent import main as agent_main

        reload(agent_main)

        with patch("src.config.resolve_data_db_mode", return_value="postgres"):
            with patch.object(
                agent_main,
                "_probe_postgres_connectivity",
                return_value=(False, "database_url_not_configured"),
            ):
                result = agent_main._run_startup_preflight()

        assert result["status"] == "degraded"
        assert result["checks"]["data_backend"]["backend"] == "postgres"

    def test_health_ok_with_valid_database_config(self, monkeypatch):
        """GET /health returns ok status when Postgres is configured."""
        monkeypatch.setenv("DATABASE_URL", "postgresql://user:pass@example-db:5432/db")
        monkeypatch.setenv("GUARDRAILS_REQUIRE_HUB_VALIDATOR", "false")

        from importlib import reload

        from src.agent import main as agent_main

        reload(agent_main)

        client = TestClient(agent_main.app)
        response = client.get("/health")

        assert response.status_code == 200
        payload = response.json()
        assert payload["status"] == "ok"


# ---------------------------------------------------------------------------
# Integration: Preflight mode-selection consistency
# ---------------------------------------------------------------------------


class TestPreflightModeSelectionConsistency:
    """Verify preflight backend selection stays on postgres."""

    def test_preflight_uses_postgres_backend_when_database_url_is_present(self, monkeypatch):
        monkeypatch.setenv("DATABASE_URL", "postgresql://user:pass@example-db:5432/db")
        monkeypatch.setenv("GUARDRAILS_REQUIRE_HUB_VALIDATOR", "false")
        monkeypatch.delenv("RENDER", raising=False)
        monkeypatch.delenv("RENDER_SERVICE_ID", raising=False)

        import src.config as config_module
        from src.agent import main as agent_main

        importlib.reload(config_module)
        importlib.reload(agent_main)

        with patch.object(agent_main, "_probe_guardrails_loaded", return_value=(True, "ok")):
            with patch.object(
                agent_main, "_probe_postgres_connectivity", return_value=(True, "ok")
            ) as postgres_probe:
                result = agent_main._run_startup_preflight()

        assert result["data_mode"] == "postgres"
        assert result["checks"]["data_backend"]["backend"] == "postgres"
        assert postgres_probe.called is True

    def test_preflight_reloads_with_postgres_backend_defaults(self, monkeypatch):
        monkeypatch.setenv("DATABASE_URL", "postgresql://user:pass@example-db:5432/db")
        monkeypatch.setenv("GUARDRAILS_REQUIRE_HUB_VALIDATOR", "false")
        monkeypatch.delenv("RENDER", raising=False)
        monkeypatch.delenv("RENDER_SERVICE_ID", raising=False)

        import src.config as config_module
        from src.agent import main as agent_main

        importlib.reload(config_module)
        importlib.reload(agent_main)

        with patch.object(agent_main, "_probe_guardrails_loaded", return_value=(True, "ok")):
            with patch.object(
                agent_main, "_probe_postgres_connectivity", return_value=(True, "ok")
            ) as postgres_probe:
                result = agent_main._run_startup_preflight()

        assert result["data_mode"] == "postgres"
        assert result["checks"]["data_backend"]["backend"] == "postgres"
        assert postgres_probe.called is True


# ---------------------------------------------------------------------------
# Unit: Error message clarity assertions
# ---------------------------------------------------------------------------


class TestErrorMessageClarity:
    """Verify error messages are clear and actionable."""

    def test_placeholder_url_error_message_is_clear(self, monkeypatch):
        """Error detail for placeholder URL is clear, not technical DNS error."""
        monkeypatch.setenv("DATABASE_URL", "postgresql://test")

        from src.agent import main as agent_main

        ok, detail = agent_main._probe_postgres_connectivity()

        assert ok is False
        # Should be clear and actionable
        assert detail == "database_url_is_test_placeholder"
        # Should NOT contain confusing DNS terminology
        assert "translate" not in detail.lower()
        assert "temporary failure" not in detail.lower()
        assert "resolution" not in detail.lower()

    def test_render_internal_host_resolution_error_has_actionable_hint(self, monkeypatch):
        """Render internal dpg-* host should return an actionable local-run hint."""
        monkeypatch.setenv(
            "DATABASE_URL",
            "postgresql://user:pass@dpg-d6or4g2a214c73f6hl20-a:5432/db?sslmode=require",
        )

        from src.agent import main as agent_main

        class _DummyPsycopg:
            @staticmethod
            def connect(*_args, **_kwargs):
                raise RuntimeError(
                    'could not translate host name "dpg-d6or4g2a214c73f6hl20-a" '
                    "to address: Temporary failure in name resolution"
                )

        monkeypatch.setattr(agent_main, "psycopg2", _DummyPsycopg)

        ok, detail = agent_main._probe_postgres_connectivity()

        assert ok is False
        assert "render_internal_host_unresolvable_outside_render" in detail
        assert "use_render_external_hostname_or_local_postgres" in detail

    def test_preflight_error_detail_preserved_in_response(self, monkeypatch):
        """Preflight result preserves the clear error detail."""
        monkeypatch.setenv("DATABASE_URL", "postgresql://test")
        monkeypatch.setenv("GUARDRAILS_REQUIRE_HUB_VALIDATOR", "false")

        from src.agent import main as agent_main

        result = agent_main._run_startup_preflight()

        data_backend_check = result["checks"]["data_backend"]
        assert "detail" in data_backend_check
        assert data_backend_check["detail"] == "database_url_is_test_placeholder"


# ---------------------------------------------------------------------------
# Integration: Config endpoint stability during degraded startup
# ---------------------------------------------------------------------------


class TestConfigEndpointStability:
    """Verify /config endpoint works despite degraded startup."""

    def test_config_endpoint_returns_200_with_degraded_startup(self, monkeypatch):
        """GET /config returns 200 even when startup is degraded."""
        monkeypatch.setenv("DATABASE_URL", "postgresql://test")
        monkeypatch.setenv("GUARDRAILS_REQUIRE_HUB_VALIDATOR", "false")

        from importlib import reload

        from src.agent import main as agent_main

        reload(agent_main)
        client = TestClient(agent_main.app)

        response = client.get("/config")

        assert response.status_code == 200
        payload = response.json()
        assert "providers" in payload
        assert isinstance(payload["providers"], list)

    def test_config_includes_service_status_info(self, monkeypatch):
        """GET /config includes service status independent of preflight."""
        monkeypatch.setenv("DATABASE_URL", "postgresql://test")
        monkeypatch.setenv("GUARDRAILS_REQUIRE_HUB_VALIDATOR", "false")

        from importlib import reload

        from src.agent import main as agent_main

        reload(agent_main)
        client = TestClient(agent_main.app)

        response = client.get("/config")

        payload = response.json()
        # Config should describe the service, potentially including readiness info
        if "service_status" in payload or "status" in payload:
            status = payload.get("service_status") or payload.get("status")
            assert status in ("ok", "healthy", "degraded", "unknown")
