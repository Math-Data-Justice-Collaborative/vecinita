"""Compatibility entrypoint.

Allows legacy startup commands that reference `src.embedding.main:app`
to continue working after the embedding service module was moved to
`src.embedding_service.main`.
"""

from src.embedding_service.main import app

__all__ = ["app"]
