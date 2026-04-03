from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

pytestmark = pytest.mark.unit


@pytest.fixture
def preflight_module(env_vars, monkeypatch):
    for key, value in env_vars.items():
        monkeypatch.setenv(key, value)

    from src.agent import main

    return main


def test_run_startup_preflight_ok(preflight_module, monkeypatch):
    """Test startup preflight succeeds when all checks pass."""
    monkeypatch.setattr(preflight_module, "_probe_guardrails_loaded", lambda: (True, "ok"))
    monkeypatch.setattr(preflight_module, "_probe_postgres_connectivity", lambda: (True, "ok"))

    with patch("src.config.resolve_data_db_mode", return_value="postgres"):
        result = preflight_module._run_startup_preflight()

    assert result["status"] == "ok"
    assert result["data_mode"] == "postgres"
    assert result["checks"]["guardrails"]["ok"] is True
    assert result["checks"]["data_backend"]["ok"] is True
    assert result["checks"]["data_backend"]["backend"] == "postgres"


def test_run_startup_preflight_ok_supabase(preflight_module, monkeypatch):
    """Test startup preflight succeeds with Supabase backend."""
    monkeypatch.setattr(preflight_module, "_probe_guardrails_loaded", lambda: (True, "ok"))
    monkeypatch.setattr(preflight_module, "_probe_supabase_connectivity", lambda: (True, "ok"))

    with patch("src.config.resolve_data_db_mode", return_value="supabase"):
        result = preflight_module._run_startup_preflight()

    assert result["status"] == "ok"
    assert result["data_mode"] == "supabase"
    assert result["checks"]["guardrails"]["ok"] is True
    assert result["checks"]["data_backend"]["ok"] is True
    assert result["checks"]["data_backend"]["backend"] == "supabase"


def test_run_startup_preflight_degraded_postgres(preflight_module, monkeypatch):
    """Test startup preflight shows degraded status when postgres probe fails."""
    monkeypatch.setattr(preflight_module, "_probe_guardrails_loaded", lambda: (True, "ok"))
    monkeypatch.setattr(
        preflight_module,
        "_probe_postgres_connectivity",
        lambda: (False, "database_url_not_configured"),
    )

    with patch("src.config.resolve_data_db_mode", return_value="postgres"):
        result = preflight_module._run_startup_preflight()

    assert result["status"] == "degraded"
    assert result["data_mode"] == "postgres"
    assert result["checks"]["data_backend"]["ok"] is False
    assert result["checks"]["data_backend"]["backend"] == "postgres"


def test_probe_postgres_sentinel_url_is_rejected(preflight_module, monkeypatch):
    """Test that the test placeholder URL is rejected early with clear message."""
    monkeypatch.setenv("DATABASE_URL", "postgresql://test")
    
    ok, detail = preflight_module._probe_postgres_connectivity()

    assert ok is False
    assert detail == "database_url_is_test_placeholder"


def test_run_startup_preflight_degraded_when_db_url_is_placeholder(preflight_module, monkeypatch):
    """Regression test: Ensure placeholder DATABASE_URL causes degraded status.
    
    This reproduces the original `make dev` failure where backend/.env had
    DATABASE_URL=postgresql://test, causing startup to fail with a confusing
    DNS error.
    """
    monkeypatch.setenv("DATABASE_URL", "postgresql://test")
    monkeypatch.setattr(preflight_module, "_probe_guardrails_loaded", lambda: (True, "ok"))

    with patch("src.config.resolve_data_db_mode", return_value="postgres"):
        result = preflight_module._run_startup_preflight()

    assert result["status"] == "degraded"
    assert result["data_mode"] == "postgres"
    assert result["checks"]["data_backend"]["ok"] is False
    assert result["checks"]["data_backend"]["detail"] == "database_url_is_test_placeholder"


def test_run_startup_preflight_degraded_dns_error(preflight_module, monkeypatch):
    """Test degraded status when postgres probe returns DNS error."""
    monkeypatch.setattr(preflight_module, "_probe_guardrails_loaded", lambda: (True, "ok"))
    monkeypatch.setattr(
        preflight_module,
        "_probe_postgres_connectivity",
        lambda: (False, 'error: could not translate host name "unknown" to address: Temporary failure in name resolution'),
    )

    with patch("src.config.resolve_data_db_mode", return_value="postgres"):
        result = preflight_module._run_startup_preflight()

    assert result["status"] == "degraded"
    assert result["checks"]["data_backend"]["ok"] is False
    assert "could not translate host name" in result["checks"]["data_backend"]["detail"]


def test_health_exposes_readiness(preflight_module):
    """Test that /health endpoint exposes preflight readiness status."""
    client = TestClient(preflight_module.app)

    response = client.get("/health")

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ok"
    assert "readiness" in payload
    assert "preflight" in payload


def test_probe_guardrails_strict_requires_hub(preflight_module, monkeypatch):
    """Test guardrails strict mode requires hub validator."""
    monkeypatch.setenv("GUARDRAILS_REQUIRE_HUB_VALIDATOR", "true")
    with patch("src.agent.guardrails_config._get_hub_guards", return_value=(None, None)):
        ok, detail = preflight_module._probe_guardrails_loaded()

    assert ok is False
    assert detail == "hub_validator_required_but_unavailable"


def test_probe_guardrails_allows_local_fallback_when_not_strict(preflight_module, monkeypatch):
    """Test guardrails allows local fallback when hub is not required."""
    monkeypatch.setenv("GUARDRAILS_REQUIRE_HUB_VALIDATOR", "false")
    with patch("src.agent.guardrails_config._get_hub_guards", return_value=(None, None)):
        ok, detail = preflight_module._probe_guardrails_loaded()

    assert ok is True
    assert detail == "local_fallback"

