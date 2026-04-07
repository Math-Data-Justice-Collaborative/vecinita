"""Compatibility uploader module for the active scraper CLI.

This path is used by `src.scraper.scraper` (and therefore by
`backend/scripts/run_scraper.sh`). We re-export the Postgres-backed
implementation from `src.services.scraper.uploader` so both
CLI and API ingestion write to the same vector database.
"""

from src.services.scraper.uploader import (  # noqa: F401
    EMBEDDING_SERVICE_AVAILABLE,
    FALLBACK_EMBEDDINGS_AVAILABLE,
    DatabaseUploader,
    DocumentChunk,
)

__all__ = [
    "DatabaseUploader",
    "DocumentChunk",
    "EMBEDDING_SERVICE_AVAILABLE",
    "FALLBACK_EMBEDDINGS_AVAILABLE",
]
