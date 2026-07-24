"""HTTP client for Modal ``vecinita-llm`` / ``vecinita-llm-playground`` (ADR-037).

Uses ``vecinita_shared_schemas.llm_http.resolve_llm_http_config`` for URL/proxy/timeout
(TP-S010-20). Legacy Ollama env fallbacks are removed (RD-170).
"""

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
