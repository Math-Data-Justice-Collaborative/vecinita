"""T14.3: H1-H3 staging smoke when VECINITA_STAGING_* URLs are set (live tier T3)."""

from __future__ import annotations

import os
from http import HTTPStatus

import httpx
import pytest

from tests.helpers.json_response import json_str, response_json_object
from tests.smoke.staging_h2 import assert_h2_database_ready, staging_database_url

pytestmark = [pytest.mark.e2e, pytest.mark.live]


def _staging_chat_url() -> str | None:
    return os.environ.get("VECINITA_STAGING_CHAT_URL")


@pytest.fixture
def staging_chat_url() -> str:
    """Return the staging chat URL, skipping when it is not configured."""
    url = _staging_chat_url()
    if not url:
        pytest.skip("Set VECINITA_STAGING_CHAT_URL to run live staging smoke")
    return url.rstrip("/")


def test_h1_chat_health(staging_chat_url: str) -> None:
    """H1: staging chat /health returns 200 with status ok."""
    response = httpx.get(f"{staging_chat_url}/health", timeout=30.0)
    assert response.status_code == HTTPStatus.OK
    body = response_json_object(response)
    assert body["status"] == "ok"


def test_h2_database_ready() -> None:
    """H2: staging database is reachable and migrated."""
    url = staging_database_url()
    if not url:
        pytest.skip("Set VECINITA_STAGING_DATABASE_URL or DATABASE_URL for H2")
    assert_h2_database_ready(url)


def test_h3_sample_ask(staging_chat_url: str) -> None:
    """H3: staging /api/v1/ask answers a sample question."""
    response = httpx.post(
        f"{staging_chat_url}/api/v1/ask",
        json={"question": "What are the food pantry hours?"},
        timeout=60.0,
    )
    assert response.status_code == HTTPStatus.OK
    payload = response_json_object(response)
    assert payload.get("answer")
    assert payload.get("language") in ("en", "es")


def test_h1_write_api_health() -> None:
    """H1: staging internal-write API /health returns 200 with status ok."""
    write_url = os.environ.get("VECINITA_STAGING_WRITE_URL")
    if not write_url:
        pytest.skip("VECINITA_STAGING_WRITE_URL not set")
    response = httpx.get(f"{write_url.rstrip('/')}/health", timeout=30.0)
    assert response.status_code == HTTPStatus.OK
    assert json_str(response_json_object(response), "status") == "ok"
