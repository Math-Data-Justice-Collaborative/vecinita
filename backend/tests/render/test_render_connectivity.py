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
RENDER_STAGING_YAML = REPO_ROOT / "render.staging.yaml"
RENDER_BLUEPRINT_YAML = REPO_ROOT / "render.blueprint.yaml"
GATEWAY_DOCKERFILE = REPO_ROOT / "backend" / "Dockerfile.gateway"
GATEWAY_START_SCRIPT = REPO_ROOT / "backend" / "scripts" / "start_gateway_render.sh"

pytestmark = pytest.mark.render_connectivity


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _load_yaml(path: Path) -> dict:
    return yaml.safe_load(path.read_text())


def _load_render_yaml() -> dict:
    return _load_yaml(RENDER_YAML)


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


@pytest.mark.parametrize(
    "service_name",
    [
        "vecinita-agent",
        "vecinita-gateway",
        "vecinita-data-management-api-v1",
    ],
)
def test_database_url_bound_from_postgres(service_name: str):
    """Core web services must bind DATABASE_URL via fromDatabase."""
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


def test_staging_data_management_api_database_url_bound_from_postgres_staging():
    """Staging scraper API must bind DATABASE_URL to the staging Postgres instance."""
    data = _load_yaml(RENDER_STAGING_YAML)
    svc = _find_service(data, "vecinita-data-management-api-v1-staging")
    assert (
        svc is not None
    ), "vecinita-data-management-api-v1-staging not found in render.staging.yaml"
    db_entry = _find_env_entry(svc, "DATABASE_URL")
    assert db_entry is not None
    assert "fromDatabase" in db_entry
    assert db_entry["fromDatabase"]["name"] == "vecinita-postgres-staging"


# ---------------------------------------------------------------------------
# 3. With RENDER=true, MODEL_ENDPOINT and EMBEDDING_ENDPOINT contain no localhost
# ---------------------------------------------------------------------------


def test_model_and_embedding_endpoints_no_localhost_on_render():
    """On Render, resolved MODEL_ENDPOINT and EMBEDDING_ENDPOINT must not be localhost."""
    render_env = {
        "RENDER": "true",
        "VECINITA_MODEL_API_URL": "https://vecinita--vecinita-model-api.modal.run",
        "VECINITA_EMBEDDING_API_URL": "https://vecinita--vecinita-embedding-api.modal.run",
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
# 4. Endpoints must point to direct Modal hosts
# ---------------------------------------------------------------------------


def test_modal_endpoints_use_direct_modal_hosts():
    """Canonical endpoint URLs must point to direct Modal hosts."""
    render_env = {
        "RENDER": "true",
        "VECINITA_MODEL_API_URL": "https://vecinita--vecinita-model-api.modal.run",
        "VECINITA_EMBEDDING_API_URL": "https://vecinita--vecinita-embedding-api.modal.run",
    }
    import sys

    with patch.dict(os.environ, render_env, clear=False):
        for mod_name in list(sys.modules.keys()):
            if "src.config" in mod_name or "src.service_endpoints" in mod_name:
                del sys.modules[mod_name]
        from src.service_endpoints import EMBEDDING_ENDPOINT, MODEL_ENDPOINT  # noqa: PLC0415

        assert (
            "modal.run" in MODEL_ENDPOINT
        ), f"MODEL_ENDPOINT must be direct Modal URL; got: {MODEL_ENDPOINT}"
        assert (
            "modal.run" in EMBEDDING_ENDPOINT
        ), f"EMBEDDING_ENDPOINT must be direct Modal URL; got: {EMBEDDING_ENDPOINT}"


# ---------------------------------------------------------------------------
# 5. ALLOWED_ORIGINS env var (not CORS_ORIGINS) is used for CORS
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


# ---------------------------------------------------------------------------
# 6. Gateway blueprint must use the dedicated gateway image and safe start script
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("render_yaml_path", "service_name"),
    [
        (RENDER_YAML, "vecinita-gateway"),
        (RENDER_STAGING_YAML, "vecinita-gateway-staging"),
        (RENDER_BLUEPRINT_YAML, "vecinita-gateway"),
    ],
)
def test_gateway_services_use_gateway_dockerfile_with_safe_start_script(
    render_yaml_path: Path, service_name: str
):
    data = _load_yaml(render_yaml_path)
    svc = _find_service(data, service_name)
    assert svc is not None, f"{service_name} not found in {render_yaml_path.name}"
    assert svc.get("runtime") == "docker"
    assert svc.get("dockerfilePath") == "./backend/Dockerfile.gateway"
    assert svc.get("dockerContext") == "./backend"
    assert (
        svc.get("dockerCommand") == "/bin/sh ./scripts/start_gateway_render.sh"
    ), f"{service_name} must use the dedicated gateway start script to avoid Render Docker command quoting issues"


def test_gateway_dockerfile_cmd_starts_uvicorn_on_render_port():
    dockerfile_text = GATEWAY_DOCKERFILE.read_text()
    assert 'CMD ["sh", "./scripts/start_gateway_render.sh"]' in dockerfile_text


def test_gateway_start_script_execs_uvicorn_on_render_port():
    script_text = GATEWAY_START_SCRIPT.read_text()
    assert "exec uvicorn src.api.main:app" in script_text
    assert "--host 0.0.0.0" in script_text
    assert '--port "${PORT:-10000}"' in script_text
