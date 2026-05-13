from __future__ import annotations

import os
from pathlib import Path

import httpx
import pytest


def _read_env_value(key: str) -> str | None:
    """Read a config value from environment, then fallback to local .env file."""

    value = os.getenv(key)
    if value:
        return value

    env_path = Path(__file__).resolve().parents[1] / ".env"
    if not env_path.exists():
        return None

    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        if k.strip() == key:
            return v.strip().strip('"').strip("'")

    return None


def _live_api_url() -> str | None:
    return _read_env_value("LIVE_API_URL")


def _proxy_auth_headers() -> dict[str, str]:
    token_id = _read_env_value("MODAL_TOKEN_ID") or _read_env_value("MODAL_AUTH_KEY")
    token_secret = _read_env_value("MODAL_TOKEN_SECRET") or _read_env_value(
        "MODAL_AUTH_SECRET"
    )

    if not token_id or not token_secret:
        return {}

    # Modal auth proxy accepts these headers for authenticated requests.
    return {
        "Modal-Key": token_id,
        "Modal-Secret": token_secret,
    }


@pytest.mark.live
def test_live_health_endpoint() -> None:
    base_url = _live_api_url()
    if not base_url:
        pytest.skip("LIVE_API_URL is not configured in environment or .env")

    response = httpx.get(
        f"{base_url.rstrip('/')}/health",
        headers=_proxy_auth_headers(),
        timeout=20.0,
    )

    assert response.status_code == 200, response.text
    assert response.json() == {"status": "ok"}


@pytest.mark.live
def test_live_embed_single_query() -> None:
    base_url = _live_api_url()
    if not base_url:
        pytest.skip("LIVE_API_URL is not configured in environment or .env")

    response = httpx.post(
        f"{base_url.rstrip('/')}/embed",
        headers=_proxy_auth_headers(),
        json={"query": "Hello from live test"},
        timeout=30.0,
    )

    assert response.status_code == 200, response.text
    payload = response.json()

    assert isinstance(payload["embedding"], list)
    assert len(payload["embedding"]) > 0
    assert payload["dimensions"] == len(payload["embedding"])
    assert isinstance(payload["model"], str)


@pytest.mark.live
def test_live_embed_batch_query() -> None:
    base_url = _live_api_url()
    if not base_url:
        pytest.skip("LIVE_API_URL is not configured in environment or .env")

    response = httpx.post(
        f"{base_url.rstrip('/')}/embed/batch",
        headers=_proxy_auth_headers(),
        json={"queries": ["alpha", "beta"]},
        timeout=30.0,
    )

    assert response.status_code == 200, response.text
    payload = response.json()

    assert isinstance(payload["embeddings"], list)
    assert len(payload["embeddings"]) == 2
    assert all(isinstance(vector, list) for vector in payload["embeddings"])
    assert all(len(vector) == payload["dimensions"] for vector in payload["embeddings"])
    assert isinstance(payload["model"], str)
