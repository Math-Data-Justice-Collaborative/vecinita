"""HTTP client for Modal vLLM and vecinita-ollama (ADR-009, ADR-035)."""

from vecinita_llm_client.client import LlmClient, LlmClientError

__version__ = "0.1.0"

__all__ = ["LlmClient", "LlmClientError"]
