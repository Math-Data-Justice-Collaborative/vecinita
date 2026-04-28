"""Pact (sync message): gateway ↔ Modal SDK RPC envelope (invoke_modal_* boundaries).

Writes ``backend/pacts/vecinita-gateway-vecinita-modal-sdk.json`` (gitignored).
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from pact import Pact

from tests.pact.modal_sdk_pact_payloads import MODAL_RPC_REQUESTS, MODAL_RPC_RESPONSES

pytestmark = [pytest.mark.unit, pytest.mark.contract]

_ORDER = (
    "modal_rpc_embedding_single",
    "modal_rpc_embedding_batch",
    "modal_rpc_model_chat",
    "modal_rpc_scraper_submit",
    "modal_rpc_scraper_get",
    "modal_rpc_scraper_list",
    "modal_rpc_scraper_cancel",
)


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def _pact_output_dir() -> Path:
    return _repo_root() / "backend" / "pacts"


def test_gateway_modal_sdk_sync_message_pact() -> None:
    pact = Pact("vecinita-gateway", "vecinita-modal-sdk").with_specification("V4")

    for name in _ORDER:
        req = MODAL_RPC_REQUESTS[name]
        resp = MODAL_RPC_RESPONSES[name]
        (
            pact.upon_receiving(name, interaction="Sync")
            .with_body(json.dumps(req), content_type="application/json")
            .will_respond_with()
            .with_body(json.dumps(resp), content_type="application/json")
        )

    pending = list(_ORDER)

    def _consumer_handler(body: str | bytes | None, _metadata: dict[str, object]) -> None:
        assert pending, "unexpected extra message"
        name = pending.pop(0)
        raw = body if isinstance(body, str) else (body.decode("utf-8") if body else "{}")
        assert json.loads(raw) == MODAL_RPC_REQUESTS[name]

    pact.verify(_consumer_handler, kind="Sync")
    pact.write_file(_pact_output_dir(), overwrite=True)
