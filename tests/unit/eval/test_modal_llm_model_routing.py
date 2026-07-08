"""Eval runtime routes LLM calls via EvalConfig.model_id through vecinita-llm (ADR-037)."""

from __future__ import annotations

import json as json_lib
from typing import TYPE_CHECKING, cast

import httpx
from vecinita_eval.modal_llm import eval_runtime_for_config
from vecinita_llm_client import LlmClient
from vecinita_shared_schemas.eval_config import DEFAULT_EVAL_MODEL_ID, EvalConfig
from vecinita_shared_schemas.json_types import as_json_object

if TYPE_CHECKING:
    from _pytest.monkeypatch import MonkeyPatch


def _llm_client_factory(
    transport: httpx.MockTransport,
    *,
    model_id: str,
) -> LlmClient:
    return LlmClient(
        "http://llm.test",
        model_id=model_id,
        proxy_key="proxy-secret",
        http_client=httpx.Client(transport=transport, base_url="http://llm.test"),
    )


def test_eval_runtime_for_config_sends_model_id_to_llm(
    monkeypatch: MonkeyPatch,
) -> None:
    """Sandbox eval uses vecinita-llm URL and config.model_id on /generate."""
    captured: dict[str, object] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        payload = as_json_object(cast("object", json_lib.loads(request.content.decode())))
        captured["path"] = request.url.path
        captured["model_id"] = payload.get("model_id")
        return httpx.Response(200, json={"text": "Eval answer."})

    transport = httpx.MockTransport(handler)
    monkeypatch.setenv("VECINITA_MODAL_LLM_URL", "http://llm.test")
    monkeypatch.setattr(
        "vecinita_eval.modal_llm._eval_llm_client",
        lambda model_id: _llm_client_factory(transport, model_id=model_id),  # pyright: ignore[reportUnknownArgumentType, reportUnknownLambdaType]
    )

    config = EvalConfig(model_id="qwen3:8b", max_tokens=128, temperature=0.4)
    judge, synthesis = eval_runtime_for_config(config)
    assert judge is not None
    assert synthesis is not None
    synthesis.complete("Score this answer.")
    assert captured["path"] == "/generate"
    assert captured["model_id"] == "qwen3:8b"


def test_eval_runtime_for_config_defaults_model_id(
    monkeypatch: MonkeyPatch,
) -> None:
    """Default EvalConfig.model_id is forwarded when not overridden."""
    captured: dict[str, object] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        payload = as_json_object(cast("object", json_lib.loads(request.content.decode())))
        captured["model_id"] = payload.get("model_id")
        return httpx.Response(200, json={"text": "ok"})

    transport = httpx.MockTransport(handler)
    monkeypatch.setenv("VECINITA_MODAL_LLM_URL", "http://llm.test")
    monkeypatch.setattr(
        "vecinita_eval.modal_llm._eval_llm_client",
        lambda model_id: _llm_client_factory(transport, model_id=model_id),  # pyright: ignore[reportUnknownArgumentType, reportUnknownLambdaType]
    )

    _judge, synthesis = eval_runtime_for_config(EvalConfig())
    assert synthesis is not None
    synthesis.complete("prompt")
    assert captured["model_id"] == DEFAULT_EVAL_MODEL_ID
