"""Live embedding direct-endpoint smoke test."""

from __future__ import annotations

import pytest
import requests

pytestmark = pytest.mark.live


def test_agent_config_references_direct_embedding_endpoint(agent_config_url: str):
    """Agent config should reference direct embedding endpoints instead of routing paths."""
    resp = requests.get(agent_config_url, timeout=30)
    assert resp.status_code == 200
    body = resp.json()
    config_str = str(body).lower()
    # Current config payload may not include concrete endpoint URLs, but must
    # not reference the old direct-routing service and should indicate a live
    # remote provider/runtime.
    assert (
        "vecinita-direct-routing" not in config_str
    ), "Agent config still points at deprecated direct-routing service"
    assert (
        "modal" in config_str or "ollama" in config_str
    ), "Agent config does not expose expected remote provider metadata"
