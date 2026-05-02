"""Regression test for generated gateway OpenAPI Python client imports.

This test follows the same enablement contract as quality-gate OpenAPI drift checks:
run only when all three schema URL env vars are set. Otherwise skip.
"""

from __future__ import annotations

import importlib
import os
import sys
from pathlib import Path

import pytest

pytestmark = pytest.mark.unit


def _all_schema_urls_configured() -> bool:
    required = ("GATEWAY_SCHEMA_URL", "DATA_MANAGEMENT_SCHEMA_URL", "AGENT_SCHEMA_URL")
    return all((os.getenv(name) or "").strip() for name in required)


@pytest.mark.unit
def test_generated_gateway_client_import_and_configuration_roundtrip() -> None:
    """Import generated package and verify a trivial Configuration round-trip."""
    if not _all_schema_urls_configured():
        pytest.skip(
            "OpenAPI generated-client regression skipped: set GATEWAY_SCHEMA_URL, "
            "DATA_MANAGEMENT_SCHEMA_URL, and AGENT_SCHEMA_URL to enable (matches CI gate)."
        )

    repo_root = Path(__file__).resolve().parents[2]
    generated_root = repo_root / "packages" / "openapi-clients" / "python" / "gateway"
    generated_pkg_dir = generated_root / "vecinita_openapi_gateway"
    if not generated_pkg_dir.exists():
        if os.getenv("CI", "").lower() in {"1", "true"}:
            pytest.fail(
                "Generated gateway client tree is missing. Run `make openapi-codegen` and commit output."
            )
        pytest.skip(
            "Generated gateway client tree is missing in local/dev checkout. "
            "CI with schema vars enabled must regenerate clients before this test can run."
        )

    sys.path.insert(0, str(generated_root))
    importlib.invalidate_caches()

    try:
        configuration_mod = importlib.import_module("vecinita_openapi_gateway.configuration")
    except Exception as exc:  # pragma: no cover - exercised in CI/generated environments
        pytest.fail(f"Failed to import generated gateway client package: {exc}")

    configuration_cls = getattr(configuration_mod, "Configuration", None)
    if configuration_cls is None:
        pytest.fail("Generated gateway client is missing Configuration class.")

    configured_host = "https://gateway.example.invalid/api/v1"
    cfg = configuration_cls(host=configured_host)
    assert getattr(cfg, "host", "") == configured_host
