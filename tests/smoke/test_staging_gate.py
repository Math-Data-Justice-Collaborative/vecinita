"""Phase 4 staging gate criteria (QA-006).

Maps to ``docs/sessions/S000-internal-docs-archive/execution-plan.md`` Phase 4 Gate Check and ``docs/staging-runbook.md``.
Live H1-H3 tiers skip when ``VECINITA_STAGING_*`` / ``DATABASE_URL`` are unset.
"""

from __future__ import annotations

import os
from http import HTTPStatus
from pathlib import Path

import httpx
import pytest

from tests.helpers.json_response import json_str, response_json_object
from tests.smoke.staging_h2 import assert_h2_database_ready, staging_database_url

pytestmark = [pytest.mark.e2e, pytest.mark.live]

_REPO_ROOT = Path(__file__).resolve().parents[2]


def test_gate_runbook_exists() -> None:
    """Operators use docs/staging-runbook.md for deploy + smoke procedure."""
    assert (_REPO_ROOT / "docs" / "staging-runbook.md").is_file()


def test_gate_cost_monitoring_documented() -> None:
    """Gate: cost estimate documented (execution-plan Phase 4)."""
    archive = _REPO_ROOT / "docs" / "sessions" / "S000-internal-docs-archive"
    assert (archive / "reference.md").is_file()


def test_gate_data_staging_state_tracked() -> None:
    """Gate: data assets tracked in docs/sessions/S000-internal-docs-archive/data-staging-state.md."""
    archive = _REPO_ROOT / "docs" / "sessions" / "S000-internal-docs-archive"
    assert (archive / "data-staging-state.md").is_file()


def test_gate_staging_h1_chat_liveness() -> None:
    """Gate item: staging GET /health → 200 (deferred without VECINITA_STAGING_CHAT_URL)."""
    chat_url = os.environ.get("VECINITA_STAGING_CHAT_URL")
    if not chat_url:
        pytest.skip("Set VECINITA_STAGING_CHAT_URL to verify live H1")
    response = httpx.get(f"{chat_url.rstrip('/')}/health", timeout=30.0)
    assert response.status_code == HTTPStatus.OK
    assert json_str(response_json_object(response), "status") == "ok"


def test_gate_staging_h2_database_ready() -> None:
    """Gate item: migrations at head; pool connects (H2)."""
    url = staging_database_url()
    if not url:
        pytest.skip("Set VECINITA_STAGING_DATABASE_URL or DATABASE_URL for live H2")
    assert_h2_database_ready(url)


def test_gate_staging_h3_sample_ask() -> None:
    """Gate item: sample ask returns answer in en/es (deferred without chat URL)."""
    chat_url = os.environ.get("VECINITA_STAGING_CHAT_URL")
    if not chat_url:
        pytest.skip("Set VECINITA_STAGING_CHAT_URL to verify live H3")
    response = httpx.post(
        f"{chat_url.rstrip('/')}/api/v1/ask",
        json={"question": "What are the food pantry hours?"},
        timeout=60.0,
    )
    assert response.status_code == HTTPStatus.OK
    payload = response_json_object(response)
    assert payload.get("answer")
    assert payload.get("language") in ("en", "es")
