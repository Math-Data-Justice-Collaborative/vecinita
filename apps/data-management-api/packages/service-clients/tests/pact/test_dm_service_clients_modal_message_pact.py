"""Pact (sync message): DM ``service_clients`` ↔ Modal SDK RPC (``modal_invoker``).

Writes ``apis/data-management-api/pacts/vecinita-dm-service-clients-vecinita-modal-sdk.json``.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from pact import Pact

from dm_modal_rpc_payloads import DM_MODAL_RPC_REQUESTS, DM_MODAL_RPC_RESPONSES

pytestmark = [pytest.mark.unit, pytest.mark.contract]

_ORDER = (
    "dm_modal_embedding_single",
    "dm_modal_model_predict",
    "dm_modal_scraper_health",
)


def _dm_api_root() -> Path:
    # .../packages/service-clients/tests/pact/this_file.py → data-management-api/
    return Path(__file__).resolve().parents[4]


def _pact_output_dir() -> Path:
    return _dm_api_root() / "pacts"


def test_dm_service_clients_modal_sync_message_pact() -> None:
    pact = Pact("vecinita-dm-service-clients", "vecinita-modal-sdk").with_specification("V4")

    for name in _ORDER:
        req = DM_MODAL_RPC_REQUESTS[name]
        resp = DM_MODAL_RPC_RESPONSES[name]
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
        assert json.loads(raw) == DM_MODAL_RPC_REQUESTS[name]

    pact.verify(_consumer_handler, kind="Sync")
    pact.write_file(_pact_output_dir(), overwrite=True)
