"""BUG-2026-08-05: sync ask inside async route must not block the event loop.

Repro: while POST /api/v1/ask runs a slow sync ChatRagService.ask, an asyncio
ticker on the same loop must keep advancing (proves offload via to_thread).
"""

from __future__ import annotations

import asyncio
import time
from http import HTTPStatus
from typing import Protocol

import httpx
import pytest
from httpx import ASGITransport
from vecinita_chat_rag_backend.app import create_app
from vecinita_chat_rag_backend.config import ChatRagSettings
from vecinita_shared_schemas.chat_rag import AskRequest, AskResponse

_BLOCK_S = 0.6
_TICK_S = 0.05
# If the event loop is free, we expect ~BLOCK_S/TICK_S ticks during the ask.
_MIN_TICKS_DURING_ASK = 6


class _AskService(Protocol):
    def ask(self, request: AskRequest) -> AskResponse: ...


class _SlowAskService:
    """Minimal service stub with a blocking sync ask."""

    def __init__(self, *, block_s: float) -> None:
        self._block_s = block_s

    def ask(self, request: AskRequest) -> AskResponse:
        del request
        time.sleep(self._block_s)
        return AskResponse(answer="ok", sources=[], language="en", cache_hit="none")


def _settings() -> ChatRagSettings:
    return ChatRagSettings(
        database_url="postgresql+psycopg://u:p@127.0.0.1:1/none",
        top_k=5,
        embed_url=None,
        llm_url=None,
        request_timeout_s=30.0,
        internal_write_url=None,
        internal_api_key=None,
        stats_enabled=False,
    )


@pytest.mark.asyncio
async def test_bug_2026_08_05_ask_does_not_block_event_loop() -> None:
    """Async ticker must advance while a slow sync ask runs (no event-loop stall)."""
    service: _AskService = _SlowAskService(block_s=_BLOCK_S)
    app = create_app(settings=_settings(), chat_service=service)  # type: ignore[arg-type]
    transport = ASGITransport(app=app)
    ticks = 0

    async def _ticker() -> None:
        nonlocal ticks
        while True:
            await asyncio.sleep(_TICK_S)
            ticks += 1

    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        ticker_task = asyncio.create_task(_ticker())
        try:
            ticks_before = ticks
            ask_resp = await client.post(
                "/api/v1/ask",
                json={"question": "hello", "language": "en"},
            )
            ticks_during = ticks - ticks_before
        finally:
            _ = ticker_task.cancel()
            with pytest.raises(asyncio.CancelledError):
                await ticker_task

    assert ask_resp.status_code == HTTPStatus.OK
    assert ask_resp.json()["answer"] == "ok"
    assert ticks_during >= _MIN_TICKS_DURING_ASK, (
        f"event loop stalled during ask: only {ticks_during} ticks "
        + f"(expected >= {_MIN_TICKS_DURING_ASK}); sync ask likely ran on the loop"
    )
