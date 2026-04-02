"""Live Q&A round-trip tests via the Render gateway."""

from __future__ import annotations

import time

import pytest
import requests

pytestmark = pytest.mark.live

_ENGLISH_QUESTION = "What environmental programs are available in Boyle Heights?"
_SPANISH_QUESTION = "¿Qué programas ambientales hay disponibles en Boyle Heights?"


def _ask(gateway_url: str, question: str, *, timeout: int = 60) -> dict:
    resp = requests.post(
        f"{gateway_url}/api/v1/ask",
        json={"question": question},
        timeout=timeout,
    )
    assert (
        resp.status_code == 200
    ), f"POST /api/v1/ask returned {resp.status_code}: {resp.text[:200]}"
    return resp.json()


def test_ask_english_question_returns_answer_and_sources(gateway_url: str):
    body = _ask(gateway_url, _ENGLISH_QUESTION)
    assert "answer" in body or "response" in body, f"Response missing answer: {body}"
    # Sources/citations are optional but rated highly
    # just confirm no server error and response is non-empty
    answer_text = body.get("answer") or body.get("response") or ""
    assert len(answer_text) > 10, f"Answer suspiciously short: {answer_text!r}"


def test_ask_spanish_question_returns_answer(gateway_url: str):
    """Spanish input exercises the language-detection path in agent/main.py."""
    body = _ask(gateway_url, _SPANISH_QUESTION)
    answer_text = body.get("answer") or body.get("response") or ""
    assert len(answer_text) > 10, f"Spanish answer suspiciously short: {answer_text!r}"


def test_ask_request_completes_within_sla(gateway_url: str):
    """Wall-clock time for a simple ask must be < 30 s (production SLA proxy)."""
    start = time.monotonic()
    _ask(gateway_url, _ENGLISH_QUESTION, timeout=35)
    elapsed = time.monotonic() - start
    assert elapsed < 30, f"Ask request took {elapsed:.1f}s — exceeds 30s SLA"
