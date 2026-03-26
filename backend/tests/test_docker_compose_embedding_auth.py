"""Regression tests for mandatory embedding auth in production compose."""

from pathlib import Path

import yaml


def test_prod_compose_sets_embedding_auth_token_for_required_services():
    compose_path = Path(__file__).resolve().parents[2].joinpath("docker-compose.yml")
    compose = yaml.safe_load(compose_path.read_text())

    services = compose.get("services") or {}

    # Service names in the YAML (without trailing colon)
    for service_name in ("embedding-service", "vecinita-agent", "vecinita-gateway"):
        service_cfg = services.get(service_name)
        assert service_cfg is not None, f"Service '{service_name}' not found in docker-compose.yml"

        environment = service_cfg.get("environment")
        assert environment is not None, f"Service '{service_name}' has no environment configuration"

        has_token = False
        if isinstance(environment, dict):
            has_token = "EMBEDDING_SERVICE_AUTH_TOKEN" in environment
        elif isinstance(environment, list):
            has_token = any(
                isinstance(item, str) and item.startswith("EMBEDDING_SERVICE_AUTH_TOKEN=")
                for item in environment
            )

        assert (
            has_token
        ), f"Service '{service_name}' is missing EMBEDDING_SERVICE_AUTH_TOKEN in environment"
