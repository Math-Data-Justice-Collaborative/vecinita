"""Pact (sync message): scraper ``EmbeddingClient`` ↔ Modal embedding app (RPC envelope).

Writes ``modal-apps/scraper/pacts/vecinita-scraper-vecinita-embedding-modal.json`` (gitignored).
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from pact import Pact
from scraper_modal_embedding_payloads import (
    SCRAPER_EMBEDDING_MODAL_REQUESTS,
    SCRAPER_EMBEDDING_MODAL_RESPONSES,
)

pytestmark = [pytest.mark.unit, pytest.mark.contract]

_ORDER = ("scraper_modal_embed_config_probe", "scraper_modal_embed_batch")


def _scraper_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _pact_output_dir() -> Path:
    return _scraper_root() / "pacts"


def test_scraper_embedding_modal_sync_message_pact() -> None:
    pact = Pact("vecinita-scraper", "vecinita-embedding-modal").with_specification("V4")

    for name in _ORDER:
        req = SCRAPER_EMBEDDING_MODAL_REQUESTS[name]
        resp = SCRAPER_EMBEDDING_MODAL_RESPONSES[name]
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
        assert json.loads(raw) == SCRAPER_EMBEDDING_MODAL_REQUESTS[name]

    pact.verify(_consumer_handler, kind="Sync")
    pact.write_file(_pact_output_dir(), overwrite=True)
