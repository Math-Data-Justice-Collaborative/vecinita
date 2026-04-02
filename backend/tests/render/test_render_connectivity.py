"""Render connectivity configuration tests.

These tests verify that service-to-service wiring is correctly declared
in render.yaml and that the backend config produces no localhost URLs
when running on Render.  All tests are offline — no running services
or secrets needed.
"""

from __future__ import annotations

import os
from pathlib import Path
from unittest.mock import patch

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parents[3]
RENDER_YAML = REPO_ROOT / "render.yaml"

pytestmark = pytest.mark.render_connectivity


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _load_render_yaml() -> dict:
    return yaml.safe_load(RENDER_YAML.read_text())


def _find_service(data: dict, name: str) -> dict | None:
    for svc in data.get("services", []):
        if svc.get("name") == name:
            return svc
    return None


def _find_env_entry(svc: dict, key: str) -> dict | None:
    for entry in svc.get("envVars", []):
        if entry.get("key") == key:
            return entry
    return None


# ---------------------------------------------------------------------------
# 1. Gateway binds AGENT_SERVICE_URL via fromService (private network)
# ---------------------------------------------------------------------------


def test_gateway_agent_service_url_is_from_service_binding():
    """vecinita-gateway must bind AGENT_SERVICE_URL via fromService (not hardcoded)."""
    data = _load_render_yaml()
    gw = _find_service(data, "vecinita-gateway")
    assert gw is not None, "vecinita-gateway not found in render.yaml"

    agent_entry = _find_env_entry(gw, "AGENT_SERVICE_URL")
    assert agent_entry is not None, "AGENT_SERVICE_URL not declared in vecinita-gateway"
    assert (
        "fromService" in agent_entry
    ), "AGENT_SERVICE_URL must use fromService binding, not a hardcoded value"
    assert (
        agent_entry["fromService"]["name"] == "vecinita-agent"
    ), "AGENT_SERVICE_URL fromService.name must be 'vecinita-agent'"
    assert (
        agent_entry["fromService"]["property"] == "hostport"
    ), "AGENT_SERVICE_URL fromService.property must be 'hostport'"


# ---------------------------------------------------------------------------
# 2. Both agent and gateway bind DATABASE_URL from the Postgres service
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("service_name", ["vecinita-agent", "vecinita-gateway"])
def test_database_url_bound_from_postgres(service_name: str):
    """Agent and gateway must bind DATABASE_URL via fromDatabase."""
    data = _load_render_yaml()
    svc = _find_service(data, service_name)
    assert svc is not None, f"{service_name} not found in render.yaml"

    db_entry = _find_env_entry(svc, "DATABASE_URL")
    assert db_entry is not None, f"DATABASE_URL not declared in {service_name}"
    assert (
        "fromDatabase" in db_entry
    ), f"DATABASE_URL in {service_name} must use fromDatabase binding"
    assert (
        db_entry["fromDatabase"]["name"] == "vecinita-postgres"
    ), f"DATABASE_URL in {service_name} must bind from 'vecinita-postgres'"


# ---------------------------------------------------------------------------
# 3. With RENDER=true, MODEL_ENDPOINT and EMBEDDING_ENDPOINT contain no localhost
# ---------------------------------------------------------------------------


def test_model_and_embedding_endpoints_no_localhost_on_render():
    """On Render, resolved MODEL_ENDPOINT and EMBEDDING_ENDPOINT must not be localhost."""
    render_env = {
        "RENDER": "true",
        "VECINITA_MODEL_API_URL": "http://vecinita-modal-proxy-v1:10000/model",
        "VECINITA_EMBEDDING_API_URL": "http://vecinita-modal-proxy-v1:10000/embedding",
    }
    # Reload the module with Render env vars set so _running_on_render() returns True
    import sys

    with patch.dict(os.environ, render_env, clear=False):
        # Force re-import of config and service_endpoints
        for mod_name in list(sys.modules.keys()):
            if "src.config" in mod_name or "src.service_endpoints" in mod_name:
                del sys.modules[mod_name]
        from src.service_endpoints import EMBEDDING_ENDPOINT, MODEL_ENDPOINT  # noqa: PLC0415

        assert (
            "localhost" not in MODEL_ENDPOINT.lower()
        ), f"MODEL_ENDPOINT must not contain localhost on Render; got: {MODEL_ENDPOINT}"
        assert (
            "localhost" not in EMBEDDING_ENDPOINT.lower()
        ), f"EMBEDDING_ENDPOINT must not contain localhost on Render; got: {EMBEDDING_ENDPOINT}"


# ---------------------------------------------------------------------------
# 4. Proxy hostname is the expected Render internal DNS format
# ---------------------------------------------------------------------------


def test_proxy_endpoints_use_render_internal_hostname():
    """Canonical endpoint URLs must use the vecinita-modal-proxy-v1 private hostname."""
    render_env = {
        "RENDER": "true",
        "VECINITA_MODEL_API_URL": "http://vecinita-modal-proxy-v1:10000/model",
        "VECINITA_EMBEDDING_API_URL": "http://vecinita-modal-proxy-v1:10000/embedding",
    }
    import sys

    with patch.dict(os.environ, render_env, clear=False):
        for mod_name in list(sys.modules.keys()):
            if "src.config" in mod_name or "src.service_endpoints" in mod_name:
                del sys.modules[mod_name]
        from src.service_endpoints import EMBEDDING_ENDPOINT, MODEL_ENDPOINT  # noqa: PLC0415

        assert (
            "vecinita-modal-proxy-v1" in MODEL_ENDPOINT
        ), f"MODEL_ENDPOINT must route through vecinita-modal-proxy-v1; got: {MODEL_ENDPOINT}"
        assert (
            "vecinita-modal-proxy-v1" in EMBEDDING_ENDPOINT
        ), f"EMBEDDING_ENDPOINT must route via vecinita-modal-proxy-v1; got: {EMBEDDING_ENDPOINT}"


# ---------------------------------------------------------------------------
# 5. PROXY_AUTH_TOKEN reads only the canonical key (no aliases)
# ---------------------------------------------------------------------------


def test_proxy_auth_token_reads_canonical_key_only():
    """service_endpoints.PROXY_AUTH_TOKEN must read PROXY_AUTH_TOKEN, not deprecated aliases."""
    import sys

    # Ensure PROXY_AUTH_TOKEN is set, aliases are absent
    env_override = {
        "PROXY_AUTH_TOKEN": "canonical-value",
    }
    remove_keys = ["MODAL_PROXY_AUTH_TOKEN", "X_PROXY_TOKEN"]

    cleaned = {k: v for k, v in os.environ.items() if k not in remove_keys}
    cleaned.update(env_override)

    with patch.dict(os.environ, cleaned, clear=True):
        for mod_name in list(sys.modules.keys()):
            if "src.config" in mod_name or "src.service_endpoints" in mod_name:
                del sys.modules[mod_name]
        from src.service_endpoints import PROXY_AUTH_TOKEN  # noqa: PLC0415

        assert PROXY_AUTH_TOKEN == "canonical-value"


def test_deprecated_proxy_auth_alias_not_picked_up():
    """MODAL_PROXY_AUTH_TOKEN must NOT be read by service_endpoints after Phase 0."""
    import sys

    env_override = {
        "MODAL_PROXY_AUTH_TOKEN": "alias-value",
    }
    cleaned = {
        k: v for k, v in os.environ.items() if k not in ("PROXY_AUTH_TOKEN", "X_PROXY_TOKEN")
    }
    cleaned.update(env_override)

    with patch.dict(os.environ, cleaned, clear=True):
        for mod_name in list(sys.modules.keys()):
            if "src.config" in mod_name or "src.service_endpoints" in mod_name:
                del sys.modules[mod_name]
        from src.service_endpoints import PROXY_AUTH_TOKEN  # noqa: PLC0415

        assert (
            PROXY_AUTH_TOKEN != "alias-value"
        ), "MODAL_PROXY_AUTH_TOKEN alias must no longer be read by service_endpoints"


# ---------------------------------------------------------------------------
# 6. ALLOWED_ORIGINS env var (not CORS_ORIGINS) is used for CORS
# ---------------------------------------------------------------------------


def test_allowed_origins_read_from_correct_env_key():
    """get_allowed_origins() must read ALLOWED_ORIGINS, not CORS_ORIGINS."""
    import sys

    env_override = {
        "ALLOWED_ORIGINS": "https://app.example.com",
        "CORS_ORIGINS": "https://wrong.example.com",
    }

    with patch.dict(os.environ, env_override, clear=False):
        for mod_name in list(sys.modules.keys()):
            if "src.config" in mod_name or "src.service_endpoints" in mod_name:
                del sys.modules[mod_name]
        from src.service_endpoints import get_allowed_origins  # noqa: PLC0415

        origins = get_allowed_origins()
        assert "https://app.example.com" in origins
        assert "https://wrong.example.com" not in origins
