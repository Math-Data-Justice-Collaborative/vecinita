"""Compatibility shim for legacy imports.

Canonical runtime module is `src.agent.main`.
This module re-exports canonical symbols so legacy paths continue to work
while the codebase is migrated to the flatter structure.
"""

from src.agent.main import *  # noqa: F401,F403
from src.agent import main as _canonical

# Legacy tests and patch points still reference ChatGroq on this module.
if not hasattr(_canonical, "ChatGroq") and hasattr(_canonical, "ChatOllama"):
    ChatGroq = _canonical.ChatOllama  # type: ignore[misc]

__all__ = [name for name in dir(_canonical) if not name.startswith("_")]
