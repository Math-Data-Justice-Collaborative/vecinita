"""Embedding and model paths using ``EmbeddingClient`` / ``ModelClient`` (Modal vs HTTP per settings)."""

from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException

from service_clients.embedding_client import EmbeddingClient, EmbeddingUpstreamError
from service_clients.model_client import ModelClient, ModelUpstreamError
from shared_config import get_settings
from shared_schemas.embedding import EmbedRequest, EmbedResponse
from shared_schemas.model import PredictRequest, PredictResponse
from vecinita_dm_api.corpus_conflict import resolve_corpus_write_conflict

router = APIRouter(tags=["ingest"])


@router.post("/embed", response_model=EmbedResponse)
async def embed(body: EmbedRequest) -> EmbedResponse:
    try:
        response = await EmbeddingClient(get_settings().embedding_service_url).embed(
            body.text,
            body.model_version,
        )
        # Preserve canonical visibility metadata for downstream callers that persist results.
        if hasattr(response, "metadata") and isinstance(response.metadata, dict):  # type: ignore[attr-defined]
            response.metadata.setdefault("source_of_truth", "postgres")  # type: ignore[attr-defined]
            response.metadata.setdefault(
                "canonical_visibility_updated_at",
                datetime.now(timezone.utc).isoformat(),
            )  # type: ignore[attr-defined]
        return response
    except EmbeddingUpstreamError as exc:
        raise HTTPException(
            status_code=exc.mapped_http_status or 502,
            detail=str(exc),
        ) from exc


@router.post("/predict", response_model=PredictResponse)
async def predict(body: PredictRequest) -> PredictResponse:
    try:
        return await ModelClient(get_settings().model_service_url).predict(
            body.text,
            body.model_version,
        )
    except ModelUpstreamError as exc:
        raise HTTPException(
            status_code=exc.mapped_http_status or 502,
            detail=str(exc),
        ) from exc
