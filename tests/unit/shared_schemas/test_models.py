"""Smoke validation for shared OpenAPI-aligned models."""

from __future__ import annotations

from uuid import uuid4

import pytest
from vecinita_shared_schemas import (
    AskRequest,
    BatchUpsertRequest,
    CreateJobRequest,
)
from vecinita_shared_schemas.chat_rag import (
    AskResponse,
    DocumentBrowseItem,
    Source,
    TagSummary,
)
from vecinita_shared_schemas.data_management import JobOptions

_EMBEDDING_DIM = 384


def test_ask_request_model() -> None:
    """Test ask request model."""
    model = AskRequest.model_validate({"question": "Hello"})
    assert model.question == "Hello"


def test_create_job_request_model() -> None:
    """Test create job request model."""
    model = CreateJobRequest.model_validate(
        {"urls": ["https://example.com/page"], "options": {"chunk_size_tokens": 256}}
    )
    assert len(model.urls) == 1


def test_batch_upsert_embedding_dimension() -> None:
    """Test batch upsert embedding dimension."""
    embedding = [0.0] * _EMBEDDING_DIM
    model = BatchUpsertRequest.model_validate(
        {
            "documents": [
                {
                    "url": "https://example.com/doc",
                    "chunks": [{"chunk_index": 0, "text": "chunk", "embedding": embedding}],
                }
            ]
        }
    )
    assert len(model.documents[0].chunks[0].embedding) == _EMBEDDING_DIM


def test_create_job_request_requires_urls_for_ingest() -> None:
    """Test create job request requires urls for ingest."""
    with pytest.raises(ValueError, match="urls required"):
        CreateJobRequest.model_validate({"urls": [], "options": {"job_type": "ingest"}})


def test_create_job_request_requires_document_id_for_retag() -> None:
    """Test create job request requires document id for retag."""
    with pytest.raises(ValueError, match="document_id required"):
        CreateJobRequest.model_validate(
            {
                "urls": [],
                "options": JobOptions(job_type="retag", document_id=None),
            }
        )


def test_chat_rag_models_validate() -> None:
    """Test chat rag models validate."""
    chunk_id = uuid4()
    document_id = uuid4()
    source = Source.model_validate(
        {
            "chunk_id": chunk_id,
            "document_id": document_id,
            "title": "Community resources",
            "url": "https://example.com/doc",
            "score": 0.9,
        }
    )
    response = AskResponse.model_validate(
        {
            "answer": "Hours are posted on Monday.",
            "language": "en",
            "sources": [source.model_dump(mode="json")],
        }
    )
    browse = DocumentBrowseItem.model_validate(
        {
            "document_id": document_id,
            "title": "Community resources",
            "url": "https://example.com/doc",
            "language": "en",
            "tags": [TagSummary(slug="housing", label="Housing").model_dump(mode="json")],
        }
    )

    assert response.sources[0].chunk_id == chunk_id
    assert browse.tags[0].slug == "housing"
