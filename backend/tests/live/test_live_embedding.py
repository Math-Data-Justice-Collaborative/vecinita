"""Live embedding direct-endpoint smoke test."""

from __future__ import annotations

import pytest
import requests

pytestmark = pytest.mark.live


def test_agent_config_references_direct_embedding_endpoint(agent_url: str):
    """Agent config should reference direct embedding endpoints instead of routing paths."""
    resp = requests.get(f"{agent_url}/api/v1/ask/config", timeout=30)
    assert resp.status_code == 200
    body = resp.json()
    # Direct modal.run endpoints are expected after routing decommission.
    config_str = str(body)
    assert (
        "modal.run" in config_str.lower() and "vecinita-direct-routing" not in config_str.lower()
    ), "Agent config still points at direct-routing or does not expose direct Modal endpoint"
