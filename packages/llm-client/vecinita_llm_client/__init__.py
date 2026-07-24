"""HTTP client for Modal vLLM and shared chat-template helper (ADR-009, ADR-037)."""

from vecinita_llm_client.chat_template import (
    ChatTemplateTokenizer,
    apply_chat_template,
    default_chat_tokenizer,
    format_instruct_prompt,
)
from vecinita_llm_client.client import LlmClient, LlmClientError

__version__ = "0.1.0"

__all__ = [
    "ChatTemplateTokenizer",
    "LlmClient",
    "LlmClientError",
    "apply_chat_template",
    "default_chat_tokenizer",
    "format_instruct_prompt",
]
