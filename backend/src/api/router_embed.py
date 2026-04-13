"""
Unified API Gateway - Embedding Router

Endpoints for text embedding generation and similarity computation.
Forwards requests to the dedicated embedding microservice.
"""

import os
from typing import Any, cast

import httpx
import numpy as np
from fastapi import APIRouter, HTTPException, Query

from src.config import (
    _normalize_internal_service_url,
    _running_on_render,
    rewrite_deprecated_modal_embedding_host,
)
from src.service_endpoints import EMBEDDING_ENDPOINT

from .models import (
    EmbedBatchRequest,
    EmbedBatchResponse,
    EmbeddingConfigResponse,
    EmbedRequest,
    EmbedResponse,
    ErrorResponse,
    SimilarityRequest,
    SimilarityResponse,
    ValidationErrorResponse,
)

_EMBED_OPENAPI_RESPONSES: dict[int | str, dict[str, Any]] = {
    422: {
        "model": ValidationErrorResponse,
        "description": "Request body or query validation failed.",
    },
    500: {
        "model": ErrorResponse,
        "description": "Unexpected error while handling the embedding request.",
    },
    503: {
        "model": ErrorResponse,
        "description": (
            "Embedding upstream unreachable, connection error, or non-success HTTP response."
        ),
    },
}

router = APIRouter(prefix="/embed", tags=["Embeddings"])

# Configuration - embedding service URL resolved via centralized service_endpoints module.
EMBEDDING_SERVICE_URL = EMBEDDING_ENDPOINT
EMBEDDING_SERVICE_AUTH_TOKEN = (
    os.getenv("EMBEDDING_SERVICE_AUTH_TOKEN")
    or os.getenv("MODAL_TOKEN_SECRET")
    or os.getenv("MODAL_API_TOKEN_SECRET")
)

# Configuration - will be fetched from embedding service
EMBEDDING_CONFIG: dict[str, Any] = {
    "model": "sentence-transformers/all-MiniLM-L6-v2",
    "provider": "huggingface",
    "dimension": 384,
    "description": "Fast, lightweight embeddings via sentence-transformers",
}


def _normalize_embedding_service_url(url: str | None) -> str:
    """Normalize embedding URL with local override for non-Render test/dev flows."""
    local_override = os.getenv("LOCAL_EMBEDDING_SERVICE_URL", "").strip()
    if local_override and not _running_on_render():
        return local_override.rstrip("/")

    return _normalize_internal_service_url(
        url,
        fallback_url="http://localhost:8001",
    ).rstrip("/")


def _embedding_service_url() -> str:
    configured = (
        os.getenv("VECINITA_EMBEDDING_API_URL")
        or os.getenv("MODAL_EMBEDDING_ENDPOINT")
        or os.getenv("EMBEDDING_SERVICE_URL")
        or EMBEDDING_SERVICE_URL
    )
    base = _normalize_embedding_service_url(configured)
    rewritten = rewrite_deprecated_modal_embedding_host(base)
    return (rewritten or base).rstrip("/")


def _embedding_service_headers() -> dict[str, str]:
    headers = {}
    if EMBEDDING_SERVICE_AUTH_TOKEN:
        headers["x-embedding-service-token"] = EMBEDDING_SERVICE_AUTH_TOKEN
        headers["authorization"] = f"Bearer {EMBEDDING_SERVICE_AUTH_TOKEN}"
    return headers


async def get_embedding_client() -> httpx.AsyncClient:
    """Dependency to get httpx AsyncClient for embedding service."""
    return httpx.AsyncClient(timeout=30.0)


def _upstream_unprocessable_detail(response: httpx.Response) -> Any:
    """Safe JSON or text from embedding service 422 responses."""
    try:
        return response.json()
    except Exception:
        return response.text or "Unprocessable entity"


async def _post_single_embedding(client: httpx.AsyncClient, text: str) -> httpx.Response:
    """Call single embedding endpoint with compatibility fallback payloads."""
    base_url = _embedding_service_url()
    response = await client.post(
        f"{base_url}/embed",
        json={"query": text},
        headers=_embedding_service_headers(),
    )
    if response.status_code == 422:
        response = await client.post(
            f"{base_url}/embed",
            json={"text": text},
            headers=_embedding_service_headers(),
        )
    return response


async def _post_batch_embedding(client: httpx.AsyncClient, texts: list[str]) -> httpx.Response:
    """Call batch embedding endpoint with compatibility fallback paths/payloads."""
    base_url = _embedding_service_url()
    response = await client.post(
        f"{base_url}/embed/batch",
        json={"queries": texts},
        headers=_embedding_service_headers(),
    )
    if response.status_code in {404, 405, 422}:
        response = await client.post(
            f"{base_url}/embed-batch",
            json={"texts": texts},
            headers=_embedding_service_headers(),
        )
    return response


@router.post("", responses=_EMBED_OPENAPI_RESPONSES)
async def embed_text(request: EmbedRequest) -> EmbedResponse:
    """
    Generate embedding for a single text.

    Forwards request to the embedding microservice.

    Args:
        request: EmbedRequest with text and optional model override

    Returns:
        EmbedResponse with 384-dimensional embedding vector
    """
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await _post_single_embedding(client, request.text)
            response.raise_for_status()

            # Parse response
            data = response.json()

            return EmbedResponse(
                text=request.text,
                embedding=data["embedding"],
                model=data.get("model", EMBEDDING_CONFIG["model"]),
                dimension=data.get(
                    "dimension", data.get("dimensions", EMBEDDING_CONFIG["dimension"])
                ),
            )

    except httpx.HTTPStatusError as e:
        if e.response is not None and e.response.status_code == 422:
            raise HTTPException(
                status_code=422,
                detail=_upstream_unprocessable_detail(e.response),
            ) from e
        raise HTTPException(status_code=503, detail=f"Embedding service error: {str(e)}") from e
    except httpx.HTTPError as e:
        raise HTTPException(status_code=503, detail=f"Embedding service error: {str(e)}") from e
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to generate embedding: {str(e)}"
        ) from e


@router.post("/batch", responses=_EMBED_OPENAPI_RESPONSES)
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
            response = await _post_batch_embedding(client, request.texts)
            response.raise_for_status()

            # Parse response
            data = response.json()
            embeddings_list = data["embeddings"]
            model = data.get("model", request.model or EMBEDDING_CONFIG["model"])
            dimension = data.get("dimension", data.get("dimensions", EMBEDDING_CONFIG["dimension"]))

            # Build EmbedResponse objects for each text
            embed_responses = []
            for text, embedding in zip(request.texts, embeddings_list, strict=False):
                embed_responses.append(
                    EmbedResponse(text=text, embedding=embedding, model=model, dimension=dimension)
                )

            return EmbedBatchResponse(embeddings=embed_responses, model=model, dimension=dimension)

    except httpx.HTTPStatusError as e:
        if e.response is not None and e.response.status_code == 422:
            raise HTTPException(
                status_code=422,
                detail=_upstream_unprocessable_detail(e.response),
            ) from e
        raise HTTPException(status_code=503, detail=f"Embedding service error: {str(e)}") from e
    except httpx.HTTPError as e:
        raise HTTPException(status_code=503, detail=f"Embedding service error: {str(e)}") from e
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to generate batch embeddings: {str(e)}"
        ) from e


@router.post("/similarity", responses=_EMBED_OPENAPI_RESPONSES)
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
            response = await _post_batch_embedding(client, [request.text1, request.text2])
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

    except httpx.HTTPStatusError as e:
        if e.response is not None and e.response.status_code == 422:
            raise HTTPException(
                status_code=422,
                detail=_upstream_unprocessable_detail(e.response),
            ) from e
        raise HTTPException(status_code=503, detail=f"Embedding service error: {str(e)}") from e
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
            if response.status_code in {404, 405}:
                # External embedding service does not expose /config; keep gateway-level config only.
                EMBEDDING_CONFIG["model"] = model
                EMBEDDING_CONFIG["provider"] = provider
                return EmbeddingConfigResponse(
                    model=model,
                    provider=provider,
                    dimension=cast(int, EMBEDDING_CONFIG["dimension"]),
                    description=f"Embedding model: {model}",
                )

            response.raise_for_status()

            # Fetch updated config
            config_response = await client.get(
                f"{EMBEDDING_SERVICE_URL}/config",
                headers=_embedding_service_headers(),
            )
            if config_response.status_code in {404, 405}:
                EMBEDDING_CONFIG["model"] = model
                EMBEDDING_CONFIG["provider"] = provider
                return EmbeddingConfigResponse(
                    model=model,
                    provider=provider,
                    dimension=cast(int, EMBEDDING_CONFIG["dimension"]),
                    description=f"Embedding model: {model}",
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
                dimension=cast(int, EMBEDDING_CONFIG["dimension"]),
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
