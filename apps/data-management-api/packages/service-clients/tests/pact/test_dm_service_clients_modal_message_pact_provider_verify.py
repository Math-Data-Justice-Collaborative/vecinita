"""Provider verification: replay DM service-clients ↔ Modal sync message pact."""

from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

pytest.importorskip("pact")
from pact import Verifier
from pact.types import Message

from dm_modal_rpc_payloads import DM_MODAL_RPC_RESPONSES


def _dm_api_root() -> Path:
    return Path(__file__).resolve().parents[4]


def _pact_file() -> Path:
    return _dm_api_root() / "pacts" / "vecinita-dm-service-clients-vecinita-modal-sdk.json"


@pytest.mark.integration
@pytest.mark.pact_provider
def test_verify_dm_modal_sdk_message_pact() -> None:
    if not os.environ.get("PACT_VERIFY_DM_MODAL_SDK_MESSAGE", "").strip():
        pytest.skip(
            "Set PACT_VERIFY_DM_MODAL_SDK_MESSAGE=1 to run DM service-clients Modal message "
            "pact provider verification"
        )

    pact_path = _pact_file()
    if not pact_path.is_file():
        pytest.skip(
            f"Missing pact file {pact_path} — run: "
            "pytest apis/data-management-api/packages/service-clients/tests/pact/"
            "test_dm_service_clients_modal_message_pact.py -q"
        )

    def _producer(*, name: str, metadata: dict[str, object] | None = None) -> Message:
        if name not in DM_MODAL_RPC_RESPONSES:
            msg = f"unknown message {name!r}"
            raise KeyError(msg)
        payload = DM_MODAL_RPC_RESPONSES[name]
        return Message(
            contents=json.dumps(payload).encode("utf-8"),
            metadata=None,
            content_type="application/json",
        )

    Verifier("vecinita-modal-sdk").message_handler(_producer).add_source(str(pact_path)).verify()
