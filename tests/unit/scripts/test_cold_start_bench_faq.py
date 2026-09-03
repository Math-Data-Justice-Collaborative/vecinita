"""TC-320-05 companion: cold_start_bench chat-ask stamps answer_path (F85)."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, cast

import httpx
import pytest
from scripts.ops import cold_start_bench as bench
from vecinita_shared_schemas.json_types import JsonObject, as_json_object

if TYPE_CHECKING:
    from pathlib import Path

pytestmark = pytest.mark.unit

_BAD_INPUT_EXIT = 2
_FAQ_SAMPLE_N = 2


def test_chat_ask_faq_bypass_sample_writes_answer_path_report(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """ChatRAG FAQ hit → report uses answer_path, never cold_kind (AC-320-05)."""

    def fake_post(
        url: str,
        *,
        json: dict[str, object] | None = None,
        headers: dict[str, str] | None = None,
        timeout: float | None = None,
    ) -> httpx.Response:
        _ = (url, json, headers, timeout)
        request = httpx.Request("POST", url)
        return httpx.Response(
            200,
            json={
                "answer": "Vecinita is a bilingual community Q&A assistant.",
                "language": "en",
                "sources": [],
                "cache_hit": "none",
                "answer_path": "faq_bypass",
            },
            request=request,
        )

    monkeypatch.setattr(httpx, "post", fake_post)
    out = tmp_path / "faq-bench.json"
    code = bench.main(
        [
            "--mode",
            "chat-ask",
            "--n",
            str(_FAQ_SAMPLE_N),
            "--chat-url",
            "https://chat.example/api",
            "--faq-question",
            "What is Vecinita?",
            "--output",
            str(out),
        ]
    )
    assert code == 0
    decoded = cast("object", json.loads(out.read_text(encoding="utf-8")))
    report = as_json_object(decoded)
    assert report["mode"] == "chat-ask"
    path_summary = as_json_object(report["answer_path_summary"])
    faq_summary = as_json_object(path_summary["faq_bypass"])
    assert faq_summary["n"] == _FAQ_SAMPLE_N
    assert "cold_kind" not in report
    samples_raw = report["samples"]
    assert isinstance(samples_raw, list)
    samples = cast("list[JsonObject]", samples_raw)
    for sample in samples:
        assert sample["answer_path"] == "faq_bypass"
        assert "cold_kind" not in sample
        assert "question" not in sample
        assert isinstance(sample["first_token_ms"], float)


def test_chat_ask_requires_chat_url(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Fail closed when ChatRAG URL missing for chat-ask mode."""
    monkeypatch.delenv("VECINITA_STAGING_CHAT_URL", raising=False)
    code = bench.main(
        [
            "--mode",
            "chat-ask",
            "--n",
            "1",
            "--chat-url",
            "",
            "--output",
            str(tmp_path / "out.json"),
        ]
    )
    assert code == _BAD_INPUT_EXIT
