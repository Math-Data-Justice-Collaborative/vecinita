"""Live Q&A round-trip tests via the Render gateway."""

from __future__ import annotations

import time

import pytest
import requests

from .response_validators import validate_ask_payload

pytestmark = pytest.mark.live

_ENGLISH_QUESTION = "What environmental programs are available in Boyle Heights?"
_SPANISH_QUESTION = "¿Qué programas ambientales hay disponibles en Boyle Heights?"


def _ask(gateway_url: str, question: str, *, timeout: int = 60) -> dict:
    # Gateway exposes GET /api/v1/ask with question as a query param (see router_ask.py).
    resp = requests.get(
        f"{gateway_url}/api/v1/ask",
        params={"question": question},
        timeout=timeout,
    )
    assert (
        resp.status_code == 200
    ), f"GET /api/v1/ask returned {resp.status_code}: {resp.text[:200]}"
    return resp.json()


def test_ask_english_question_returns_answer_and_sources(gateway_url: str):
    body = _ask(gateway_url, _ENGLISH_QUESTION)
    validate_ask_payload(body)


def test_ask_spanish_question_returns_answer(gateway_url: str):
    """Spanish input exercises the language-detection path in agent/main.py."""
    body = _ask(gateway_url, _SPANISH_QUESTION)
    validate_ask_payload(body)


def test_ask_request_completes_within_sla(gateway_url: str):
    """Wall-clock time for a simple ask must be < 30 s (production SLA routing)."""
    start = time.monotonic()
    _ask(gateway_url, _ENGLISH_QUESTION, timeout=35)
    elapsed = time.monotonic() - start
    assert elapsed < 30, f"Ask request took {elapsed:.1f}s — exceeds 30s SLA"
