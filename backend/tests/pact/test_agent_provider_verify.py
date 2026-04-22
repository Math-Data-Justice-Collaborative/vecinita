"""Reserved for standalone **agent** consumer pacts (FR-007).

Chat traffic is currently modeled against the **gateway** provider
(``chat-frontend-vecinita-gateway.json``). When a dedicated
``*-vecinita-agent.json`` consumer appears, add a matching verifier here
using ``PACT_PROVIDER_AGENT_URL`` mirroring :mod:`test_chat_gateway_provider_verify`.
"""

from __future__ import annotations

import pytest


@pytest.mark.integration
@pytest.mark.pact_provider
def test_agent_provider_verification_placeholder() -> None:
    pytest.skip("No standalone agent consumer pact yet — use gateway provider verification (T026).")
