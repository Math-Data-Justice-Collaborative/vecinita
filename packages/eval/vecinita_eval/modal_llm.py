"""LlamaIndex LLM adapter for vecinita-llm HTTP client (ADR-037)."""

from __future__ import annotations

import contextlib
import os
from typing import TYPE_CHECKING, Final

from llama_index.core.base.llms.types import CompletionResponse, LLMMetadata
from llama_index.core.llms.custom import CustomLLM
from pydantic import ConfigDict
from vecinita_llm_client import LlmClient, LlmClientError
from vecinita_shared_schemas.eval_config import DEFAULT_EVAL_MODEL_ID, EvalConfig

from vecinita_eval.judges import LlamaIndexJudgeClient

if TYPE_CHECKING:
    from collections.abc import Generator

    from vecinita_eval.judges import JudgeClient

_ENV_LLM_URL: Final[str] = "VECINITA_MODAL_LLM_URL"
_ENV_PROXY_KEY: Final[str] = "VECINITA_MODAL_PROXY_KEY"

# Golden/ad-hoc eval batches drive slow first-token generation; use a read timeout well
# above the 120s LlmClient default (BUG-2026-07-08). Scoped to eval only.
_EVAL_LLM_TIMEOUT_S: Final[float] = 900.0


def _qwen_instruct_prompt(prompt: str) -> str:
    """Wrap a plain prompt in Qwen2.5-Instruct chat format."""
    return (
        "<|im_start|>system\n"
        "Follow the instructions precisely. Be concise.\n"
        "<|im_start|>user\n"
        f"{prompt}\n"
        "<|im_start|>assistant\n"
    )


def warm_modal_llm(client: LlmClient) -> None:
    """Best-effort cold-start warm for vecinita-llm before eval batches."""
    with contextlib.suppress(Exception):
        client.warm()


class ModalHttpLLM(CustomLLM):
    """Bridge Modal LLM HTTP ``/generate`` to LlamaIndex evaluators and synthesis."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    client: LlmClient
    max_tokens: int = 512
    temperature: float = 0.2
    model_id: str | None = None

    @property
    def metadata(self) -> LLMMetadata:
        """Return static metadata for LlamaIndex evaluators."""
        model_name = self.model_id or "vecinita-llm"
        return LLMMetadata(
            context_window=8192,
            num_output=self.max_tokens,
            model_name=model_name,
        )

    def complete(
        self,
        prompt: str,
        formatted: bool = False,  # noqa: FBT001, FBT002
        **kwargs: object,
    ) -> CompletionResponse:
        """Complete a prompt via Modal LLM HTTP ``/generate``."""
        _ = (formatted, kwargs)
        text = self.client.generate(
            _qwen_instruct_prompt(prompt),
            max_tokens=self.max_tokens,
            temperature=self.temperature,
            model_id=self.model_id,
        )
        return CompletionResponse(text=text)

    def stream_complete(
        self,
        prompt: str,
        formatted: bool = False,  # noqa: FBT001, FBT002
        **kwargs: object,
    ) -> Generator[CompletionResponse, None, None]:
        """Stream completion tokens from Modal LLM HTTP ``/generate/stream``."""
        _ = (formatted, kwargs)
        parts: list[str] = []
        for token in self.client.generate_stream(
            _qwen_instruct_prompt(prompt),
            max_tokens=self.max_tokens,
            temperature=self.temperature,
            model_id=self.model_id,
        ):
            parts.append(token)
            yield CompletionResponse(text=token, delta=token)
        if not parts:
            yield CompletionResponse(text="")


def synthesis_llm_from_config(llm: ModalHttpLLM, config: EvalConfig) -> ModalHttpLLM:
    """Return an LLM copy with sandbox synthesis hyper-parameters."""
    return llm.model_copy(
        update={
            "max_tokens": config.max_tokens,
            "temperature": config.temperature,
            "model_id": config.model_id,
        }
    )


def judge_llm_from_config(llm: ModalHttpLLM, config: EvalConfig) -> ModalHttpLLM:
    """Return an LLM copy with sandbox judge temperature."""
    return llm.model_copy(
        update={
            "temperature": config.judge_temperature,
            "model_id": config.model_id,
        }
    )


def _eval_llm_client(model_id: str) -> LlmClient | None:
    """Create a vecinita-llm client when Modal LLM env vars are configured."""
    if not os.environ.get(_ENV_LLM_URL):
        return None
    try:
        return LlmClient(model_id=model_id, timeout=_EVAL_LLM_TIMEOUT_S)
    except LlmClientError:
        return None


def default_eval_runtime() -> tuple[JudgeClient | None, ModalHttpLLM | None]:
    """Create shared judge + LLM from vecinita-llm when configured."""
    client = _eval_llm_client(DEFAULT_EVAL_MODEL_ID)
    if client is None:
        return None, None
    warm_modal_llm(client)
    llm = ModalHttpLLM(client=client, model_id=client.default_model_id)
    return LlamaIndexJudgeClient(llm=llm), llm


def eval_runtime_for_config(
    config: EvalConfig,
) -> tuple[JudgeClient | None, ModalHttpLLM | None]:
    """Create judge + synthesis LLM with sandbox config including model_id."""
    client = _eval_llm_client(config.model_id)
    if client is None:
        return default_eval_runtime()

    warm_modal_llm(client)
    base_llm = ModalHttpLLM(
        client=client,
        model_id=config.model_id,
        max_tokens=config.max_tokens,
        temperature=config.temperature,
    )
    judge_llm = base_llm.model_copy(update={"temperature": config.judge_temperature})
    return LlamaIndexJudgeClient(llm=judge_llm), base_llm
