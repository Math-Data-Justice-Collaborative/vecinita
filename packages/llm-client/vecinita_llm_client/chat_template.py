"""Shared HuggingFace ``apply_chat_template`` helper (RD-167, TP-S010-24).

Used by chat-rag, tagging, and eval so prompts follow each model's chat template
instead of a hand-rolled Qwen ChatML wrap.
"""

from __future__ import annotations

from typing import Protocol


class ChatTemplateTokenizer(Protocol):
    """Minimal tokenizer surface required by :func:`apply_chat_template`."""

    def apply_chat_template(
        self,
        conversation: list[dict[str, str]],
        *,
        tokenize: bool = True,
        add_generation_prompt: bool = False,
    ) -> str | list[int]:
        """Render ``conversation`` with the model chat template."""
        ...


def apply_chat_template(
    messages: list[dict[str, str]],
    *,
    tokenizer: ChatTemplateTokenizer,
    add_generation_prompt: bool = True,
) -> str:
    """Format chat messages via the tokenizer's HuggingFace chat template.

    Args:
        messages: Ordered chat turns as ``{"role": ..., "content": ...}`` dicts.
        tokenizer: Object exposing HF ``apply_chat_template`` (real
            ``PreTrainedTokenizerBase`` or a test double).
        add_generation_prompt: When True, append the assistant generation header
            (HF default for completion prompts).

    Returns:
        Prompt string ready for ``/generate`` (``tokenize=False``).

    Raises:
        TypeError: If the tokenizer returns a non-string when ``tokenize=False``.
    """
    rendered = tokenizer.apply_chat_template(
        messages,
        tokenize=False,
        add_generation_prompt=add_generation_prompt,
    )
    if not isinstance(rendered, str):
        msg = "tokenizer.apply_chat_template must return str when tokenize=False"
        raise TypeError(msg)
    return rendered
