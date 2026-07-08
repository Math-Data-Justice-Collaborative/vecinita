"""Regression: eval 502 when Ollama generate 404 — model not on volume (BUG-2026-07-07)."""

from __future__ import annotations

import io
import json
from email.message import Message
from http import HTTPStatus
from typing import TYPE_CHECKING, cast
from unittest.mock import MagicMock
from urllib import error as urllib_error
from urllib import request as urllib_request

from vecinita_shared_schemas.json_types import as_json_object

if TYPE_CHECKING:
    from pathlib import Path

    from _pytest.monkeypatch import MonkeyPatch

_MODEL_ID = "qwen2.5:1.5b-instruct"
_EXPECTED_GENERATE_ATTEMPTS = 2
_OLLAMA_GENERATE_URL = "http://127.0.0.1:11434/api/generate"


def test_ollama_generate_pulls_missing_model_on_404_then_succeeds(
    monkeypatch: MonkeyPatch,
) -> None:
    """Fresh vecinita-models volume: first generate 404 must pull model and retry."""
    from infra.modal import ollama_app  # noqa: PLC0415

    attempts = 0
    pull = MagicMock()
    monkeypatch.setattr(ollama_app, "_ensure_ollama_serve", MagicMock())
    monkeypatch.setattr(ollama_app, "_run_ollama_pull", pull)
    monkeypatch.setattr(ollama_app, "model_volume", MagicMock())

    def fake_urlopen(
        req: urllib_request.Request,
        timeout: float = 600,
    ) -> io.BytesIO:
        del req, timeout
        nonlocal attempts
        attempts += 1
        if attempts == 1:
            raise urllib_error.HTTPError(
                _OLLAMA_GENERATE_URL,
                HTTPStatus.NOT_FOUND,
                "Not Found",
                hdrs=Message(),
                fp=None,
            )
        body = json.dumps({"response": "eval answer"}).encode()
        return io.BytesIO(body)

    monkeypatch.setattr(urllib_request, "urlopen", fake_urlopen)

    text = ollama_app._ollama_generate_text(  # noqa: SLF001  # pyright: ignore[reportPrivateUsage]
        _MODEL_ID,
        "hello",
        max_tokens=32,
        temperature=0.2,
    )

    pull.assert_called_once_with(_MODEL_ID)
    assert text == "eval answer"
    assert attempts == _EXPECTED_GENERATE_ATTEMPTS


def test_read_manifest_defaults_unavailable_when_missing(
    monkeypatch: MonkeyPatch,
    tmp_path: Path,
) -> None:
    """Empty volume must not claim default model is downloaded (manifest drift)."""
    from infra.modal import ollama_app  # noqa: PLC0415

    path = tmp_path / "manifest.json"
    monkeypatch.setattr(ollama_app, "_MANIFEST_PATH", path)
    monkeypatch.setattr(ollama_app, "model_volume", MagicMock())

    payload = as_json_object(cast("object", ollama_app._list_models_payload()))  # noqa: SLF001  # pyright: ignore[reportPrivateUsage]
    items_raw = payload.get("items")
    assert isinstance(items_raw, list)
    first = as_json_object(cast("object", items_raw[0]))
    assert first.get("model_id") == _MODEL_ID
    assert first.get("available") is False
