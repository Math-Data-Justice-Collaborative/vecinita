"""Shared HuggingFace ``apply_chat_template`` helper (RD-167, TP-S010-24).

Used by chat-rag, tagging, and eval so prompts follow each model's chat template
instead of a hand-rolled Qwen ChatML wrap.
"""

from __future__ import annotations

from typing import Final, Protocol

# Qwen2.5-Instruct ChatML jinja (matches HF ``tokenizer.chat_template``).
# Embedded so ChatRAG/tagging/eval work without a Hub download in CI (prod pin).
QWEN_CHATML_TEMPLATE: Final[str] = (
    "{% for message in messages %}"
    "{{'<|im_start|>' + message['role'] + '\\n' + message['content']"
    " + '<|im_end|>' + '\\n'}}"
    "{% endfor %}"
    "{% if add_generation_prompt %}{{'<|im_start|>assistant\\n'}}{% endif %}"
)


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


class _QwenChatMlTokenizer:
    """Qwen2.5-Instruct ChatML tokenizer stand-in (HF ``apply_chat_template`` contract)."""

    chat_template: str = QWEN_CHATML_TEMPLATE

    def apply_chat_template(
        self,
        conversation: list[dict[str, str]],
        *,
        tokenize: bool = True,
        add_generation_prompt: bool = False,
    ) -> str:
        """Render ChatML turns; only ``tokenize=False`` is supported."""
        if tokenize:
            msg = "default Qwen chat tokenizer only supports tokenize=False"
            raise ValueError(msg)
        parts: list[str] = []
        for message in conversation:
            role = message["role"]
            content = message["content"]
            parts.append(f"<|im_start|>{role}\n{content}<|im_end|>\n")
        if add_generation_prompt:
            parts.append("<|im_start|>assistant\n")
        return "".join(parts)


_DEFAULT_QWEN_TOKENIZER: Final[_QwenChatMlTokenizer] = _QwenChatMlTokenizer()


def default_chat_tokenizer() -> ChatTemplateTokenizer:
    """Return the prod-default Qwen2.5-Instruct ChatML tokenizer (no Hub download)."""
    return _DEFAULT_QWEN_TOKENIZER


def apply_chat_template(
    messages: list[dict[str, str]],
    *,
    tokenizer: ChatTemplateTokenizer | None = None,
    add_generation_prompt: bool = True,
) -> str:
    """Format chat messages via the tokenizer's HuggingFace chat template.

    Args:
        messages: Ordered chat turns as ``{"role": ..., "content": ...}`` dicts.
        tokenizer: Object exposing HF ``apply_chat_template`` (real
            ``PreTrainedTokenizerBase`` or a test double). Defaults to the
            embedded Qwen2.5-Instruct ChatML tokenizer (prod pin).
        add_generation_prompt: When True, append the assistant generation header
            (HF default for completion prompts).

    Returns:
        Prompt string ready for ``/generate`` (``tokenize=False``).

    Raises:
        TypeError: If the tokenizer returns a non-string when ``tokenize=False``.
    """
    resolved = tokenizer if tokenizer is not None else default_chat_tokenizer()
    rendered = resolved.apply_chat_template(
        messages,
        tokenize=False,
        add_generation_prompt=add_generation_prompt,
    )
    if not isinstance(rendered, str):
        msg = "tokenizer.apply_chat_template must return str when tokenize=False"
        raise TypeError(msg)
    return rendered


def format_instruct_prompt(
    *,
    system: str,
    user: str,
    tokenizer: ChatTemplateTokenizer | None = None,
) -> str:
    """Build a system+user completion prompt via :func:`apply_chat_template`.

    Args:
        system: System instruction text.
        user: User message text.
        tokenizer: Optional tokenizer; defaults to Qwen ChatML.

    Returns:
        Instruct prompt ending with the assistant generation header.
    """
    return apply_chat_template(
        [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        tokenizer=tokenizer,
        add_generation_prompt=True,
    )
