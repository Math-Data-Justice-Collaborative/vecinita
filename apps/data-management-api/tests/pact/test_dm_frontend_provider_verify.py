"""Provider verification: replay DM frontend pact against live DM API."""

from __future__ import annotations

import os
from pathlib import Path

import pytest

pytest.importorskip("pact")
from pact import Verifier


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[4]


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
        pytest.skip("Set PACT_PROVIDER_DM_API_URL to run DM frontend provider verification")

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
