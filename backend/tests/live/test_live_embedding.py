"""Live embedding direct-endpoint smoke test."""

from __future__ import annotations

import pytest
import requests

pytestmark = pytest.mark.live


def test_agent_config_references_direct_embedding_endpoint(agent_url: str):
    """Agent config should reference direct embedding endpoints instead of proxy paths."""
    resp = requests.get(f"{agent_url}/api/v1/ask/config", timeout=30)
    assert resp.status_code == 200
    body = resp.json()
    # Direct modal.run endpoints are expected after proxy decommission.
    config_str = str(body)
    assert (
        "modal.run" in config_str.lower() and "vecinita-modal-proxy" not in config_str.lower()
    ), "Agent config still points at modal-proxy or does not expose direct Modal endpoint"
