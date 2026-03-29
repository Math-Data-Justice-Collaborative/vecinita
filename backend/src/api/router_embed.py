"""
Unified API Gateway - Embedding Router

Endpoints for text embedding generation and similarity computation.
Proxies requests to the dedicated embedding microservice.
"""

import os
from typing import Any, cast

import httpx
import numpy as np
from fastapi import APIRouter, HTTPException, Query

from .models import (
    EmbedBatchRequest,
    EmbedBatchResponse,
    EmbeddingConfigResponse,
    EmbedRequest,
    EmbedResponse,
    SimilarityRequest,
    SimilarityResponse,
)

router = APIRouter(prefix="/embed", tags=["Embeddings"])

# Configuration - embedding service URL from environment
EMBEDDING_SERVICE_URL = (
    os.getenv("MODAL_EMBEDDING_ENDPOINT")
    or os.getenv("EMBEDDING_SERVICE_URL")
    or "http://localhost:8001"
)
EMBEDDING_SERVICE_AUTH_TOKEN = (
    os.getenv("EMBEDDING_SERVICE_AUTH_TOKEN")
    or os.getenv("MODAL_API_PROXY_SECRET")
    or os.getenv("MODAL_API_KEY")
    or os.getenv("MODAL_TOKEN_SECRET")
    or os.getenv("MODAL_API_TOKEN_SECRET")
)
MODAL_PROXY_KEY = (
    os.getenv("MODAL_API_KEY") or os.getenv("MODAL_API_TOKEN_ID") or os.getenv("MODAL_TOKEN_ID")
)
MODAL_PROXY_SECRET = os.getenv("MODAL_API_PROXY_SECRET") or os.getenv("MODAL_TOKEN_SECRET")

# Configuration - will be fetched from embedding service
EMBEDDING_CONFIG: dict[str, Any] = {
    "model": "sentence-transformers/all-MiniLM-L6-v2",
    "provider": "huggingface",
    "dimension": 384,
    "description": "Fast, lightweight embeddings via sentence-transformers",
}


def _embedding_service_headers() -> dict[str, str]:
    headers = {}
    if EMBEDDING_SERVICE_AUTH_TOKEN:
        headers["x-embedding-service-token"] = EMBEDDING_SERVICE_AUTH_TOKEN
        headers["authorization"] = f"Bearer {EMBEDDING_SERVICE_AUTH_TOKEN}"
    if MODAL_PROXY_KEY and MODAL_PROXY_SECRET:
        headers["Modal-Key"] = MODAL_PROXY_KEY
        headers["Modal-Secret"] = MODAL_PROXY_SECRET
    return headers


async def get_embedding_client() -> httpx.AsyncClient:
    """Dependency to get httpx AsyncClient for embedding service."""
    return httpx.AsyncClient(timeout=30.0)


@router.post("")
async def embed_text(request: EmbedRequest) -> EmbedResponse:
    """
    Generate embedding for a single text.

    Proxies request to the embedding microservice.

    Args:
        request: EmbedRequest with text and optional model override

    Returns:
        EmbedResponse with 384-dimensional embedding vector
    """
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            # Call embedding service
            response = await client.post(
                f"{EMBEDDING_SERVICE_URL}/embed",
                json={"text": request.text},
                headers=_embedding_service_headers(),
            )
            response.raise_for_status()

            # Parse response
            data = response.json()

            return EmbedResponse(
                text=request.text,
                embedding=data["embedding"],
                model=data.get("model", EMBEDDING_CONFIG["model"]),
                dimension=data.get("dimension", EMBEDDING_CONFIG["dimension"]),
            )

    except httpx.HTTPError as e:
        raise HTTPException(status_code=503, detail=f"Embedding service error: {str(e)}") from e
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to generate embedding: {str(e)}"
        ) from e


@router.post("/batch")
async def embed_batch(request: EmbedBatchRequest) -> EmbedBatchResponse:
    """
    Generate embeddings for multiple texts in batch.

    More efficient than calling embed endpoint multiple times.
    Proxies request to the embedding microservice batch endpoint.

    Args:
        request: EmbedBatchRequest with list of texts

    Returns:
        EmbedBatchResponse with embeddings for each text
    """
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:  # Longer timeout for batches
            # Call embedding service batch endpoint
            response = await client.post(
                f"{EMBEDDING_SERVICE_URL}/embed-batch",
                json={"texts": request.texts},
                headers=_embedding_service_headers(),
            )
            response.raise_for_status()

            # Parse response
            data = response.json()
            embeddings_list = data["embeddings"]
            model = data.get("model", request.model or EMBEDDING_CONFIG["model"])
            dimension = data.get("dimension", EMBEDDING_CONFIG["dimension"])

            # Build EmbedResponse objects for each text
            embed_responses = []
            for text, embedding in zip(request.texts, embeddings_list, strict=False):
                embed_responses.append(
                    EmbedResponse(text=text, embedding=embedding, model=model, dimension=dimension)
                )

            return EmbedBatchResponse(embeddings=embed_responses, model=model, dimension=dimension)

    except httpx.HTTPError as e:
        raise HTTPException(status_code=503, detail=f"Embedding service error: {str(e)}") from e
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to generate batch embeddings: {str(e)}"
        ) from e


@router.post("/similarity")
async def compute_similarity(request: SimilarityRequest) -> SimilarityResponse:
    """
    Compute similarity score between two texts.

    Uses cosine similarity on embedding vectors.
    Generates embeddings for both texts then computes similarity.

    Args:
        request: SimilarityRequest with two texts

    Returns:
        SimilarityResponse with score between -1 and 1
    """
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            # Generate embeddings for both texts using batch endpoint
            response = await client.post(
                f"{EMBEDDING_SERVICE_URL}/embed-batch",
                json={"texts": [request.text1, request.text2]},
                headers=_embedding_service_headers(),
            )
            response.raise_for_status()

            # Parse response
            data = response.json()
            embeddings = data["embeddings"]
            model = data.get("model", request.model or EMBEDDING_CONFIG["model"])

            # Extract the two embeddings
            embed1 = np.array(embeddings[0])
            embed2 = np.array(embeddings[1])

            # Compute cosine similarity
            # cosine_similarity = (A · B) / (||A|| ||B||)
            dot_product = np.dot(embed1, embed2)
            norm1 = np.linalg.norm(embed1)
            norm2 = np.linalg.norm(embed2)

            denom = norm1 * norm2
            if denom == 0:
                similarity = 0.0
            else:
                similarity = float(dot_product / denom)
                similarity = max(-1.0, min(1.0, similarity))

            return SimilarityResponse(
                text1=request.text1, text2=request.text2, similarity=similarity, model=model
            )

    except httpx.HTTPError as e:
        raise HTTPException(status_code=503, detail=f"Embedding service error: {str(e)}") from e
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to compute similarity: {str(e)}"
        ) from e


@router.get("/config")
async def get_embedding_config() -> EmbeddingConfigResponse:
    """
    Get current embedding model configuration.

    Returns:
        Current model, provider, and dimension info
    """
    return EmbeddingConfigResponse(
        model=cast(str, EMBEDDING_CONFIG["model"]),
        provider=cast(str, EMBEDDING_CONFIG["provider"]),
        dimension=cast(int, EMBEDDING_CONFIG["dimension"]),
        description=cast(str, EMBEDDING_CONFIG["description"]),
    )


@router.post("/config")
async def update_embedding_config(
    provider: str = Query(..., description="Embedding provider (e.g., 'huggingface')"),
    model: str = Query(
        ..., description="Model identifier (e.g., 'sentence-transformers/all-MiniLM-L6-v2')"
    ),
    lock: bool | None = Query(None, description="Lock selection to prevent further changes"),
) -> EmbeddingConfigResponse:
    """
    Update the embedding model configuration.

    Admin endpoint. Changes will affect all subsequent embeddings.
    Proxies request to the embedding microservice.

    Args:
        provider: Embedding provider (only 'huggingface' supported currently)
        model: Model identifier (e.g., sentence-transformers/all-MiniLM-L6-v2)
        lock: Whether to lock the selection

    Returns:
        Updated configuration
    """
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            # Call embedding service config endpoint
            payload: dict[str, Any] = {"provider": provider, "model": model}
            if lock is not None:
                payload["lock"] = lock

            response = await client.post(
                f"{EMBEDDING_SERVICE_URL}/config",
                json=payload,
                headers=_embedding_service_headers(),
            )
            response.raise_for_status()

            # Fetch updated config
            config_response = await client.get(
                f"{EMBEDDING_SERVICE_URL}/config",
                headers=_embedding_service_headers(),
            )
            config_response.raise_for_status()
            config_data = config_response.json()

            current = config_data.get("current", {})

            # Update local cache
            EMBEDDING_CONFIG["model"] = current.get("model", model)
            EMBEDDING_CONFIG["provider"] = current.get("provider", provider)

            return EmbeddingConfigResponse(
                model=current.get("model", model),
                provider=current.get("provider", provider),
                dimension=cast(
                    int, EMBEDDING_CONFIG["dimension"]
                ),  # Still hardcoded, could fetch dynamically
                description=f"Embedding model: {current.get('model', model)}",
            )

    except httpx.HTTPStatusError as e:
        if e.response.status_code == 403:
            raise HTTPException(
                status_code=403, detail="Embedding configuration is locked. Cannot update."
            ) from e
        raise HTTPException(
            status_code=e.response.status_code, detail=f"Embedding service error: {e.response.text}"
        ) from e
    except httpx.HTTPError as e:
        raise HTTPException(status_code=503, detail=f"Embedding service error: {str(e)}") from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update config: {str(e)}") from e
