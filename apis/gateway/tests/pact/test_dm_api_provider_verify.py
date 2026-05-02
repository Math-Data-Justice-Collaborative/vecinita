"""Provider verification: replay ``dm-frontend`` pacts against a live DM API (FR-008).

Generate pacts first::

    cd apps/data-management-frontend && npm run test:pact

Run when the scraper API is reachable::

    export PACT_PROVIDER_DM_API_URL=http://127.0.0.1:8005
    pytest backend/tests/pact/test_dm_api_provider_verify.py -q
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
    return (
        _repo_root()
        / "apps"
        / "data-management-frontend"
        / "pacts"
        / "dm-frontend-vecinita-data-management-api.json"
    )


@pytest.mark.integration
@pytest.mark.pact_provider
def test_verify_dm_frontend_pact_against_dm_api() -> None:
    base = os.environ.get("PACT_PROVIDER_DM_API_URL", "").strip().rstrip("/")
    if not base:
        pytest.skip("Set PACT_PROVIDER_DM_API_URL to run DM API Pact provider verification")

    pact_path = _pact_file()
    if not pact_path.is_file():
        pytest.skip(
            f"Missing pact file {pact_path} — run: cd apps/data-management-frontend && npm run test:pact"
        )

    verifier = (
        Verifier("vecinita-data-management-api")
        .add_transport("http", url=base)
        .add_source(str(pact_path))
    )
    verifier.verify()
