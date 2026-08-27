"""TC-145 / RD-167 / TP-S010-24: shared HF apply_chat_template helper (Slice C).

Unit fixtures cover Qwen ChatML and a non-Qwen (Llama-3) template so prompts never
fall back to a hand-rolled ``<|im_start|>`` wrap for other families.
"""

from __future__ import annotations

import importlib
from typing import TYPE_CHECKING, Final, Protocol, cast

import pytest

if TYPE_CHECKING:
    from collections.abc import Callable
    from types import ModuleType

_SYSTEM: Final[str] = "You are a helpful assistant."
_USER: Final[str] = "What are the food pantry hours?"
_MESSAGES: Final[list[dict[str, str]]] = [
    {"role": "system", "content": _SYSTEM},
    {"role": "user", "content": _USER},
]


class _ChatTemplateTokenizer(Protocol):
    """Minimal HF tokenizer surface used by the shared helper."""

    def apply_chat_template(
        self,
        conversation: list[dict[str, str]],
        *,
        tokenize: bool = True,
        add_generation_prompt: bool = False,
    ) -> str: ...


class _ApplyChatTemplateFn(Protocol):
    """Shared helper signature locked by TC-145 / T79.1."""

    def __call__(
        self,
        messages: list[dict[str, str]],
        *,
        tokenizer: _ChatTemplateTokenizer,
        add_generation_prompt: bool = True,
    ) -> str: ...


def _import_chat_template_mod() -> ModuleType:
    """Load chat_template module (keeps ModuleNotFoundError as clear T79 failure)."""
    try:
        return importlib.import_module("vecinita_llm_client.chat_template")
    except ModuleNotFoundError as exc:
        pytest.fail(
            "vecinita_llm_client.chat_template missing " +
            f"(T79.3 / RD-167 / TP-S010-24 / TC-145): {exc}"
        )


def _import_apply_chat_template() -> _ApplyChatTemplateFn:
    """Load the shared helper (T79.3). ModuleNotFoundError is the T79.1 red phase."""
    mod = _import_chat_template_mod()
    raw = getattr(mod, "apply_chat_template", None)
    if not callable(raw):
        pytest.fail(
            "apply_chat_template not exported from vecinita_llm_client.chat_template " +
            "(T79.3 / TC-145)"
        )
    return cast("_ApplyChatTemplateFn", raw)


class _FixtureTokenizer:
    """Stand-in tokenizer with an explicit chat template string (no HF download)."""

    def __init__(self, chat_template: str) -> None:
        self.chat_template = chat_template

    def apply_chat_template(
        self,
        conversation: list[dict[str, str]],
        *,
        tokenize: bool = True,
        add_generation_prompt: bool = False,
    ) -> str:
        if tokenize:
            msg = "fixture tokenizer only supports tokenize=False"
            raise AssertionError(msg)
        # Minimal ChatML / Llama rendering via the stored template markers.
        # Real implementation must call this method (HF contract), not hand-roll Qwen.
        parts: list[str] = []
        if "im_start" in self.chat_template:
            for message in conversation:
                role = message["role"]
                content = message["content"]
                parts.append(f"<|im_start|>{role}\n{content}<|im_end|>\n")
            if add_generation_prompt:
                parts.append("<|im_start|>assistant\n")
            return "".join(parts)
        # Llama-3 style (non-Qwen)
        parts.append("<|begin_of_text|>")
        for message in conversation:
            role = message["role"]
            content = message["content"]
            parts.append(f"<|start_header_id|>{role}<|end_header_id|>\n\n{content}<|eot_id|>")
        if add_generation_prompt:
            parts.append("<|start_header_id|>assistant<|end_header_id|>\n\n")
        return "".join(parts)


_QWEN_CHAT_TEMPLATE: Final[str] = (
    "{% for message in messages %}" +
    "{{'<|im_start|>' + message['role'] + '\\n' + message['content'] + '<|im_end|>' + '\\n'}}" +
    "{% endfor %}" +
    "{% if add_generation_prompt %}{{'<|im_start|>assistant\\n'}}{% endif %}"
)

_LLAMA_CHAT_TEMPLATE: Final[str] = (
    "{{ bos_token }}" +
    "{% for message in messages %}" +
    "{{ '<|start_header_id|>' + message['role'] + '<|end_header_id|>\\n\\n'" +
    "+ message['content'] + '<|eot_id|>' }}" +
    "{% endfor %}" +
    "{% if add_generation_prompt %}" +
    "{{ '<|start_header_id|>assistant<|end_header_id|>\\n\\n' }}" +
    "{% endif %}"
)


@pytest.fixture
def qwen_tokenizer() -> _ChatTemplateTokenizer:
    """Qwen2.5-Instruct ChatML-style template fixture."""
    return cast("_ChatTemplateTokenizer", _FixtureTokenizer(_QWEN_CHAT_TEMPLATE))


@pytest.fixture
def llama_tokenizer() -> _ChatTemplateTokenizer:
    """Non-Qwen (Llama-3) chat template fixture."""
    return cast("_ChatTemplateTokenizer", _FixtureTokenizer(_LLAMA_CHAT_TEMPLATE))


def test_apply_chat_template_qwen_uses_im_start_markers(
    qwen_tokenizer: _ChatTemplateTokenizer,
) -> None:
    """Qwen fixture must produce ChatML markers via the tokenizer template (TC-145)."""
    apply_chat_template = _import_apply_chat_template()
    prompt = apply_chat_template(
        _MESSAGES,
        tokenizer=qwen_tokenizer,
        add_generation_prompt=True,
    )
    assert "<|im_start|>system" in prompt
    assert _SYSTEM in prompt
    assert "<|im_start|>user" in prompt
    assert _USER in prompt
    assert prompt.rstrip().endswith("<|im_start|>assistant") or prompt.endswith(
        "<|im_start|>assistant\n"
    )


def test_apply_chat_template_non_qwen_uses_model_template_not_qwen_wrap(
    llama_tokenizer: _ChatTemplateTokenizer,
) -> None:
    """Non-Qwen prompts must use the model template, not hand-rolled Qwen wrap (TC-145)."""
    apply_chat_template = _import_apply_chat_template()
    prompt = apply_chat_template(
        _MESSAGES,
        tokenizer=llama_tokenizer,
        add_generation_prompt=True,
    )
    assert "<|im_start|>" not in prompt, (
        "non-Qwen apply_chat_template must not emit Qwen ChatML <|im_start|> markers"
    )
    assert "<|begin_of_text|>" in prompt or "<|start_header_id|>" in prompt
    assert "<|start_header_id|>system" in prompt
    assert "<|start_header_id|>user" in prompt
    assert _SYSTEM in prompt
    assert _USER in prompt
    assert "<|start_header_id|>assistant" in prompt


def test_apply_chat_template_calls_tokenizer_with_tokenize_false(
    qwen_tokenizer: _ChatTemplateTokenizer,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Helper must delegate to tokenizer.apply_chat_template(..., tokenize=False)."""
    apply_chat_template = _import_apply_chat_template()
    calls: list[dict[str, object]] = []

    def _spy(
        conversation: list[dict[str, str]],
        *,
        tokenize: bool = True,
        add_generation_prompt: bool = False,
    ) -> str:
        calls.append(
            {
                "conversation": conversation,
                "tokenize": tokenize,
                "add_generation_prompt": add_generation_prompt,
            }
        )
        return "SPY_PROMPT"

    monkeypatch.setattr(qwen_tokenizer, "apply_chat_template", _spy)
    result = apply_chat_template(
        _MESSAGES,
        tokenizer=qwen_tokenizer,
        add_generation_prompt=True,
    )
    assert result == "SPY_PROMPT"
    assert len(calls) == 1
    assert calls[0]["tokenize"] is False
    assert calls[0]["add_generation_prompt"] is True
    assert calls[0]["conversation"] == _MESSAGES


def test_default_qwen_tokenizer_rejects_tokenize_true() -> None:
    """Embedded Qwen tokenizer only supports ``tokenize=False``."""
    mod = _import_chat_template_mod()
    default_chat_tokenizer = cast(
        "Callable[[], _ChatTemplateTokenizer]",
        mod.default_chat_tokenizer,
    )
    tok = default_chat_tokenizer()
    with pytest.raises(ValueError, match="tokenize=False"):
        _ = tok.apply_chat_template(_MESSAGES, tokenize=True, add_generation_prompt=False)


def test_default_qwen_tokenizer_omits_generation_prompt_when_false() -> None:
    """``add_generation_prompt=False`` must not append the assistant header."""
    mod = _import_chat_template_mod()
    default_chat_tokenizer = cast(
        "Callable[[], _ChatTemplateTokenizer]",
        mod.default_chat_tokenizer,
    )
    tok = default_chat_tokenizer()
    rendered: str = tok.apply_chat_template(
        _MESSAGES,
        tokenize=False,
        add_generation_prompt=False,
    )
    assert rendered.endswith("<|im_end|>\n")
    assert not rendered.endswith("<|im_start|>assistant\n")


def test_apply_chat_template_rejects_non_string_render() -> None:
    """Helper must TypeError when tokenizer returns a non-str at tokenize=False."""
    apply_chat_template = _import_apply_chat_template()

    class _BadTok:
        def apply_chat_template(
            self,
            conversation: list[dict[str, str]],
            *,
            tokenize: bool = True,
            add_generation_prompt: bool = False,
        ) -> list[int]:
            _ = conversation, tokenize, add_generation_prompt
            return [1, 2, 3]

    with pytest.raises(TypeError, match="must return str"):
        _ = apply_chat_template(
            _MESSAGES,
            tokenizer=cast("_ChatTemplateTokenizer", _BadTok()),
            add_generation_prompt=True,
        )


def test_format_instruct_prompt_uses_default_tokenizer() -> None:
    """``format_instruct_prompt`` builds ChatML via the default Qwen tokenizer."""
    mod = _import_chat_template_mod()
    format_instruct_prompt = cast("Callable[..., str]", mod.format_instruct_prompt)
    prompt = format_instruct_prompt(system="sys", user="hi")
    assert "<|im_start|>system" in prompt
    assert "<|im_start|>user" in prompt
    assert prompt.endswith("<|im_start|>assistant\n")
