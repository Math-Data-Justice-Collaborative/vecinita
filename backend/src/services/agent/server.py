"""Compatibility shim for legacy imports.

Canonical runtime module is `src.agent.main`.
This module re-exports canonical symbols so legacy paths continue to work
while the codebase is migrated to the flatter structure.
"""

from src.agent import main as _canonical
from src.agent.main import *  # noqa: F401,F403
from src.embedding_service import client as _embedding_client

# Compatibility patch points used by legacy unit tests.
ChatGroq = getattr(_canonical, "ChatOllama", None)
ChatOpenAI = getattr(_canonical, "ChatOllama", None)
create_client = getattr(_canonical, "create_client", None)
create_embedding_client = _embedding_client.create_embedding_client
HuggingFaceEmbeddings = getattr(_canonical, "HuggingFaceEmbeddings", None)
AGENT_THINKING_MESSAGES = getattr(_canonical, "AGENT_THINKING_MESSAGES", None)
get_agent_thinking_message = getattr(_canonical, "get_agent_thinking_message", None)
AgentState = getattr(_canonical, "AgentState", None)


def _export_private_symbol(name: str) -> None:
    if hasattr(_canonical, name):
        globals()[name] = getattr(_canonical, name)


for _private_name in (
    "_get_llm_with_tools",
    "_get_llm_without_tools",
    "_get_chatollama_class",
    "_sanitize_messages",
):
    _export_private_symbol(_private_name)

__all__ = [name for name in dir(_canonical) if not name.startswith("__")]
