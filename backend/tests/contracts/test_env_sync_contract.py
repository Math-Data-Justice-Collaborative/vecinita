"""Contract tests for shared Render/local env templates."""

from __future__ import annotations

from pathlib import Path

import pytest

from src.utils.render_env_contract import parse_env_file, validate_shared_render_env

REPO_ROOT = Path(__file__).resolve().parents[3]


@pytest.mark.contract
def test_render_prod_template_satisfies_contract() -> None:
    env = parse_env_file(REPO_ROOT / ".env.prod.render.example")
    result = validate_shared_render_env(env)
    assert result.errors == []


@pytest.mark.contract
def test_render_staging_template_satisfies_contract() -> None:
    env = parse_env_file(REPO_ROOT / ".env.staging.render.example")
    result = validate_shared_render_env(env)
    assert result.errors == []


@pytest.mark.contract
def test_render_templates_key_parity() -> None:
    prod = parse_env_file(REPO_ROOT / ".env.prod.render.example")
    staging = parse_env_file(REPO_ROOT / ".env.staging.render.example")
    assert set(prod.keys()) == set(staging.keys())


@pytest.mark.contract
def test_local_template_contains_core_cross_service_keys() -> None:
    local_env = parse_env_file(REPO_ROOT / ".env.local.example")
    required_local_keys = {
        "DATABASE_URL",
        "VECINITA_MODEL_API_URL",
        "VECINITA_EMBEDDING_API_URL",
        "VECINITA_SCRAPER_API_URL",
        "VITE_GATEWAY_URL",
        "VITE_VECINITA_SCRAPER_API_URL",
        "MODAL_TOKEN_ID",
        "MODAL_TOKEN_SECRET",
        "MODAL_FUNCTION_INVOCATION",
    }
    missing = sorted(key for key in required_local_keys if key not in local_env)
    assert missing == []
