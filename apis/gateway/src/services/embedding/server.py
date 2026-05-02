"""Compatibility shim for legacy embedding service import path.

Canonical embedding app module is `src.embedding_service.main`.
"""

from src.embedding_service.main import *  # noqa: F401,F403
