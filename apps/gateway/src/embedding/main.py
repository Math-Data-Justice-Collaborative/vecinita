"""Compatibility entrypoint.

Allows legacy startup commands that reference `src.embedding.main:app`
to continue working after the embedding service module was moved to
`vecinita_common.embedding.main`.
"""

from vecinita_common.embedding.main import app

__all__ = ["app"]
