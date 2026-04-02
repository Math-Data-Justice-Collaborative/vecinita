"""Live embedding proxy path smoke test."""

from __future__ import annotations

import pytest
import requests

pytestmark = pytest.mark.live


def test_agent_config_references_embedding_proxy_path(agent_url: str):
    """Agent config must reference the embedding endpoint via the proxy, not direct Modal URL."""
    resp = requests.get(f"{agent_url}/api/v1/ask/config", timeout=30)
    assert resp.status_code == 200
    body = resp.json()
    # Check that the config doesn't expose raw Modal URLs directly
    # The modal-proxy sits in front; any direct modal.run URL in config = misconfiguration
    config_str = str(body)
    assert (
        "modal.run" not in config_str.lower() or "vecinita-modal-proxy" in config_str.lower()
    ), "Agent config exposes a direct Modal URL without proxy; embedding may bypass proxy"
