"""BUG-2026-07-05: Eval must not send model_id to vecinita-llm /generate (422 extra_forbidden)."""

from __future__ import annotations

import json as json_lib
from typing import TYPE_CHECKING, cast

import httpx
from vecinita_eval.modal_llm import eval_runtime_for_config
from vecinita_llm_client import LlmClient
from vecinita_shared_schemas.eval_config import EvalConfig
from vecinita_shared_schemas.json_types import as_json_object

if TYPE_CHECKING:
    from _pytest.monkeypatch import MonkeyPatch

_VLLM_BASE = "https://vecinita--vecinita-llm-fastapi-app.modal.run"


def _patched_llm_client_class(
    transport: httpx.MockTransport,
) -> type[LlmClient]:
    class PatchedLlmClient(LlmClient):
        def __init__(
            self,
            base_url: str | None = None,
            *,
            model_id: str | None = None,
            proxy_key: str | None = None,
            timeout: float = 120.0,
            http_client: httpx.Client | None = None,
        ) -> None:
            super().__init__(
                base_url or "http://llm.test",
                model_id=model_id,
                proxy_key=proxy_key or "proxy-secret",
                timeout=timeout,
                http_client=http_client
                or httpx.Client(transport=transport, base_url="http://llm.test"),
            )

    return PatchedLlmClient


def test_llm_client_omits_model_id_for_vllm_generate() -> None:
    """VLLM GenerateRequest forbids model_id — LlmClient must not send it."""
    captured: dict[str, object] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        payload = as_json_object(cast("object", json_lib.loads(request.content.decode())))
        captured["keys"] = sorted(payload.keys())
        return httpx.Response(200, json={"text": "ok"})

    transport = httpx.MockTransport(handler)
    client = LlmClient(
        _VLLM_BASE,
        model_id="qwen2.5:1.5b-instruct",
        http_client=httpx.Client(transport=transport, base_url=_VLLM_BASE),
    )
    assert client.generate("Score this.", model_id="qwen2.5:1.5b-instruct") == "ok"
    keys = captured.get("keys")
    assert isinstance(keys, list)
    assert "model_id" not in keys


def test_eval_runtime_for_config_omits_model_id_when_only_vllm_configured(
    monkeypatch: MonkeyPatch,
) -> None:
    """Production fallback (LLM URL only) must not forward Ollama model_id."""
    captured: dict[str, object] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        payload = as_json_object(cast("object", json_lib.loads(request.content.decode())))
        captured["model_id"] = payload.get("model_id")
        captured["path"] = request.url.path
        return httpx.Response(200, json={"text": "Eval answer."})

    transport = httpx.MockTransport(handler)
    monkeypatch.delenv("VECINITA_MODAL_OLLAMA_URL", raising=False)
    monkeypatch.setenv("VECINITA_MODAL_LLM_URL", "http://llm.test")
    monkeypatch.setenv("VECINITA_MODAL_PROXY_KEY", "proxy-secret")
    monkeypatch.setattr(
        "vecinita_eval.modal_llm.LlmClient",
        _patched_llm_client_class(transport),
    )

    _judge, synthesis = eval_runtime_for_config(
        EvalConfig(model_id="qwen2.5:1.5b-instruct"),
    )
    assert synthesis is not None
    synthesis.complete("prompt")
    assert captured["path"] == "/generate"
    assert captured.get("model_id") is None
