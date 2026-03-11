"""Regression tests for mandatory embedding auth in production compose."""

from pathlib import Path


def test_prod_compose_sets_embedding_auth_token_for_required_services():
    compose_lines = Path(__file__).resolve().parents[2].joinpath("docker-compose.yml").read_text().splitlines()

    for service_name in ("embedding-service:", "vecinita-agent:", "vecinita-gateway:"):
        service_block: list[str] = []
        capture = False
        for line in compose_lines:
            if line.startswith(f"  {service_name}"):
                capture = True
            elif capture and line.startswith("  ") and not line.startswith("    "):
                break

            if capture:
                service_block.append(line)

        assert any("EMBEDDING_SERVICE_AUTH_TOKEN:" in line for line in service_block)