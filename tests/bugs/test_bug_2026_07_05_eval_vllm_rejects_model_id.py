"""BUG-2026-07-05 / ADR-037: unified vecinita-llm accepts model_id on /generate.

Pre-ADR-037, fixed-model vLLM rejected extra ``model_id`` fields. The unified app
forwards playground tags so sandbox eval can select staged models.
"""

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
_SANDBOX_MODEL_ID = "qwen2.5:1.5b-instruct"


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


def test_llm_client_forwards_model_id_for_unified_vllm_generate() -> None:
    """Unified vecinita-llm /generate accepts model_id for playground tag routing."""
    captured: dict[str, object] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        payload = as_json_object(cast("object", json_lib.loads(request.content.decode())))
        captured["model_id"] = payload.get("model_id")
        return httpx.Response(200, json={"text": "ok"})

    transport = httpx.MockTransport(handler)
    client = LlmClient(
        _VLLM_BASE,
        model_id=_SANDBOX_MODEL_ID,
        http_client=httpx.Client(transport=transport, base_url=_VLLM_BASE),
    )
    assert client.generate("Score this.", model_id=_SANDBOX_MODEL_ID) == "ok"
    assert captured.get("model_id") == _SANDBOX_MODEL_ID


def test_eval_runtime_for_config_forwards_model_id_to_vecinita_llm(
    monkeypatch: MonkeyPatch,
) -> None:
    """Eval always uses vecinita-llm and forwards sandbox model_id (ADR-037)."""
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
        EvalConfig(model_id=_SANDBOX_MODEL_ID),
    )
    assert synthesis is not None
    synthesis.complete("prompt")
    assert captured["path"] == "/generate"
    assert captured.get("model_id") == _SANDBOX_MODEL_ID
