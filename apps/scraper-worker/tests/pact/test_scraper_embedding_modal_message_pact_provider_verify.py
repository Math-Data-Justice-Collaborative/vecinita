"""Provider verification: replay scraper ↔ Modal embedding sync message pact."""

from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

pytest.importorskip("pact")
from pact import Verifier
from pact.types import Message
from scraper_modal_embedding_payloads import SCRAPER_EMBEDDING_MODAL_RESPONSES


def _scraper_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _pact_file() -> Path:
    return _scraper_root() / "pacts" / "vecinita-scraper-vecinita-embedding-modal.json"


@pytest.mark.integration
@pytest.mark.pact_provider
def test_verify_scraper_embedding_modal_message_pact() -> None:
    if not os.environ.get("PACT_VERIFY_SCRAPER_EMBEDDING_MODAL_MESSAGE", "").strip():
        pytest.skip(
            "Set PACT_VERIFY_SCRAPER_EMBEDDING_MODAL_MESSAGE=1 to run scraper↔embedding Modal "
            "message pact provider verification"
        )

    pact_path = _pact_file()
    if not pact_path.is_file():
        pytest.skip(
            f"Missing pact file {pact_path} — run: "
            "cd modal-apps/scraper && PYTHONPATH=src pytest tests/pact/"
            "test_scraper_embedding_modal_message_pact.py -q"
        )

    def _producer(*, name: str, metadata: dict[str, object] | None = None) -> Message:
        if name not in SCRAPER_EMBEDDING_MODAL_RESPONSES:
            msg = f"unknown message {name!r}"
            raise KeyError(msg)
        payload = SCRAPER_EMBEDDING_MODAL_RESPONSES[name]
        return Message(
            contents=json.dumps(payload).encode("utf-8"),
            metadata=None,
            content_type="application/json",
        )

    Verifier("vecinita-embedding-modal").message_handler(_producer).add_source(str(pact_path)).verify()
