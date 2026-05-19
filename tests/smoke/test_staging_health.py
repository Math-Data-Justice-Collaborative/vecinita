"""T14.3: H1-H3 staging smoke when VECINITA_STAGING_* URLs are set (live tier T3)."""

from __future__ import annotations

import os

import httpx
import pytest

pytestmark = pytest.mark.e2e


def _staging_chat_url() -> str | None:
    return os.environ.get("VECINITA_STAGING_CHAT_URL")


@pytest.fixture
def staging_chat_url() -> str:
    url = _staging_chat_url()
    if not url:
        pytest.skip("Set VECINITA_STAGING_CHAT_URL to run live staging smoke")
    return url.rstrip("/")


def test_h1_chat_health(staging_chat_url: str) -> None:
    response = httpx.get(f"{staging_chat_url}/health", timeout=30.0)
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"


def test_h3_sample_ask(staging_chat_url: str) -> None:
    response = httpx.post(
        f"{staging_chat_url}/api/v1/ask",
        json={"question": "What are the food pantry hours?"},
        timeout=60.0,
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload.get("answer")
    assert payload.get("language") in ("en", "es")


def test_h1_write_api_health() -> None:
    write_url = os.environ.get("VECINITA_STAGING_WRITE_URL")
    if not write_url:
        pytest.skip("VECINITA_STAGING_WRITE_URL not set")
    response = httpx.get(f"{write_url.rstrip('/')}/health", timeout=30.0)
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
