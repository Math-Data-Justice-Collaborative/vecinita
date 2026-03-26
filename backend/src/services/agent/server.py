"""Compatibility shim for legacy imports.

Canonical runtime module is `src.agent.main`.
This module re-exports canonical symbols so legacy paths continue to work
while the codebase is migrated to the flatter structure.
"""

from src.agent import main as _canonical
from src.agent.main import *  # noqa: F401,F403

# Legacy tests and patch points still reference ChatGroq on this module.
if not hasattr(_canonical, "ChatGroq") and hasattr(_canonical, "ChatOllama"):
    ChatGroq = _canonical.ChatOllama


def _export_private_symbol(name: str) -> None:
    if hasattr(_canonical, name):
        globals()[name] = getattr(_canonical, name)


for _private_name in (
    "_get_llm_with_tools",
    "_get_llm_without_tools",
    "_get_chatollama_class",
    "_get_chatopenai_class",
    "_sanitize_messages",
):
    _export_private_symbol(_private_name)

__all__ = [name for name in dir(_canonical) if not name.startswith("__")]
