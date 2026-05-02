"""Provider verification: replay ``vecinita-gateway`` pact against a live agent.

Generate pact first::

    pytest backend/tests/pact/test_gateway_agent_consumer_pact.py -q

Run verification when an agent is reachable::

    export PACT_PROVIDER_AGENT_URL=http://127.0.0.1:8000
    pytest backend/tests/pact/test_agent_provider_verify.py -q
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest

pytest.importorskip("pact")
from pact import Verifier


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def _pact_file() -> Path:
    return _repo_root() / "backend" / "pacts" / "vecinita-gateway-vecinita-agent.json"


@pytest.mark.integration
@pytest.mark.pact_provider
def test_verify_gateway_pact_against_agent() -> None:
    base = os.environ.get("PACT_PROVIDER_AGENT_URL", "").strip().rstrip("/")
    if not base:
        pytest.skip("Set PACT_PROVIDER_AGENT_URL to run agent Pact provider verification")

    pact_path = _pact_file()
    if not pact_path.is_file():
        pytest.skip(
            f"Missing pact file {pact_path} — run: "
            "pytest backend/tests/pact/test_gateway_agent_consumer_pact.py -q"
        )

    verifier = Verifier("vecinita-agent").add_transport("http", url=base).add_source(str(pact_path))
    verifier.verify()
