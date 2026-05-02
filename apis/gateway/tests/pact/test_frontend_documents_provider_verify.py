"""Provider verification: replay chat frontend pact against live gateway."""

from __future__ import annotations

import os
from pathlib import Path

import pytest

pytest.importorskip("pact")
from pact import Verifier


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[4]


def _pact_file() -> Path:
    return _repo_root() / "frontends" / "chat" / "pacts" / "chat-frontend-vecinita-gateway.json"


@pytest.mark.integration
@pytest.mark.pact_provider
def test_verify_frontend_documents_pact_against_gateway() -> None:
    base = os.environ.get("PACT_PROVIDER_GATEWAY_URL", "").strip().rstrip("/")
    if not base:
        pytest.skip("Set PACT_PROVIDER_GATEWAY_URL to run frontend documents provider verification")

    pact_path = _pact_file()
    if not pact_path.is_file():
        pytest.skip(f"Missing pact file {pact_path} — run: cd frontends/chat && npm run test:pact")

    verifier = (
        Verifier("vecinita-gateway").add_transport("http", url=base).add_source(str(pact_path))
    )
    verifier.verify()
