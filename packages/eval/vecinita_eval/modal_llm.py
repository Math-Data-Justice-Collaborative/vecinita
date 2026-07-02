"""LlamaIndex LLM adapter for vecinita-llm HTTP client."""

from __future__ import annotations

import contextlib
from typing import TYPE_CHECKING

from llama_index.core.base.llms.types import CompletionResponse, LLMMetadata
from llama_index.core.llms.custom import CustomLLM
from pydantic import ConfigDict
from vecinita_llm_client import LlmClient, LlmClientError
from vecinita_shared_schemas.eval_config import EvalConfig

from vecinita_eval.judges import LlamaIndexJudgeClient

if TYPE_CHECKING:
    from collections.abc import Generator

    from vecinita_eval.judges import JudgeClient


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
    """Bridge vecinita-llm HTTP `/generate` to LlamaIndex evaluators and synthesis."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    client: LlmClient
    max_tokens: int = 512
    temperature: float = 0.2

    @property
    def metadata(self) -> LLMMetadata:
        """Return static metadata for LlamaIndex evaluators."""
        return LLMMetadata(
            context_window=8192,
            num_output=self.max_tokens,
            model_name="vecinita-llm",
        )

    def complete(
        self,
        prompt: str,
        formatted: bool = False,  # noqa: FBT001, FBT002
        **kwargs: object,
    ) -> CompletionResponse:
        """Complete a prompt via vecinita-llm HTTP `/generate`."""
        _ = (formatted, kwargs)
        text = self.client.generate(
            _qwen_instruct_prompt(prompt),
            max_tokens=self.max_tokens,
            temperature=self.temperature,
        )
        return CompletionResponse(text=text)

    def stream_complete(
        self,
        prompt: str,
        formatted: bool = False,  # noqa: FBT001, FBT002
        **kwargs: object,
    ) -> Generator[CompletionResponse, None, None]:
        """Stream completion tokens from vecinita-llm HTTP `/generate/stream`."""
        _ = (formatted, kwargs)
        parts: list[str] = []
        for token in self.client.generate_stream(
            _qwen_instruct_prompt(prompt),
            max_tokens=self.max_tokens,
            temperature=self.temperature,
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
        }
    )


def judge_llm_from_config(llm: ModalHttpLLM, config: EvalConfig) -> ModalHttpLLM:
    """Return an LLM copy with sandbox judge temperature."""
    return llm.model_copy(update={"temperature": config.judge_temperature})


def default_eval_runtime() -> tuple[JudgeClient | None, ModalHttpLLM | None]:
    """Create shared judge + LLM from ``VECINITA_MODAL_LLM_URL`` when configured."""
    try:
        client = LlmClient()
    except LlmClientError:
        return None, None
    warm_modal_llm(client)
    llm = ModalHttpLLM(client=client)
    return LlamaIndexJudgeClient(llm=llm), llm


def eval_runtime_for_config(
    config: EvalConfig,
) -> tuple[JudgeClient | None, ModalHttpLLM | None]:
    """Create judge + synthesis LLM with sandbox hyper-parameters applied."""
    judge, synthesis_llm = default_eval_runtime()
    if synthesis_llm is None:
        return judge, None
    configured_synthesis = synthesis_llm_from_config(synthesis_llm, config)
    if judge is None:
        return None, configured_synthesis
    judge_llm = judge_llm_from_config(synthesis_llm, config)
    return LlamaIndexJudgeClient(llm=judge_llm), configured_synthesis
