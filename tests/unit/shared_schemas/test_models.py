"""Smoke validation for shared OpenAPI-aligned models."""

from __future__ import annotations

from vecinita_shared_schemas import (
    AskRequest,
    BatchUpsertRequest,
    CreateJobRequest,
)


def test_ask_request_model() -> None:
    model = AskRequest.model_validate({"question": "Hello"})
    assert model.question == "Hello"


def test_create_job_request_model() -> None:
    model = CreateJobRequest.model_validate(
        {"urls": ["https://example.com/page"], "options": {"chunk_size_tokens": 256}}
    )
    assert len(model.urls) == 1


def test_batch_upsert_embedding_dimension() -> None:
    embedding = [0.0] * 384
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
    assert len(model.documents[0].chunks[0].embedding) == 384
