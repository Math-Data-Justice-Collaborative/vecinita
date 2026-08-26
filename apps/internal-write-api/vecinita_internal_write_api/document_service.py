"""Document CRUD, tags, chunks, and corpus tree for internal write API."""

from __future__ import annotations

from vecinita_internal_write_api.document_crud import (
    delete_document,
    get_corpus_tree,
    get_document_content_hash,
    get_document_detail,
    get_document_history,
    list_documents,
    mark_document_checked,
    patch_document_metadata,
)
from vecinita_internal_write_api.document_tags import (
    get_document_tags,
    list_document_chunks,
    patch_chunk_tags,
    patch_document_tags,
)

__all__ = [
    "delete_document",
    "get_corpus_tree",
    "get_document_content_hash",
    "get_document_detail",
    "get_document_history",
    "get_document_tags",
    "list_document_chunks",
    "list_documents",
    "mark_document_checked",
    "patch_chunk_tags",
    "patch_document_metadata",
    "patch_document_tags",
]
