"""Compatibility wrapper for schema imports."""

import sys
from pathlib import Path

SRC_DIR = Path(__file__).resolve().parent / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from vecinita.schemas import (  # noqa: E402
    BatchEmbeddingResponse,
    BatchQueryRequest,
    EmbeddingResponse,
    QueryRequest,
)

__all__ = [
    "BatchEmbeddingResponse",
    "BatchQueryRequest",
    "EmbeddingResponse",
    "QueryRequest",
]
