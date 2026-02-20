"""
Embedding Service - Lightweight FastAPI service for text embeddings.

Provides HTTP endpoints for generating embeddings using sentence-transformers.
Designed to run as a separate Render free-tier service (512MB limit).
"""

import logging
import os
from typing import List
from pathlib import Path
from pydantic import BaseModel
from dotenv import load_dotenv

import numpy as np
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Vecinita Embedding Service",
    description="Lightweight embedding service using sentence-transformers",
    version="0.1.0",
)

# Load environment variables with deterministic precedence:
# backend/.env defaults, root .env overrides.
_PROJECT_ROOT = Path(__file__).resolve().parents[3]
_BACKEND_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(_BACKEND_ROOT / ".env", override=False)
load_dotenv(_PROJECT_ROOT / ".env", override=True)

# Global embedding model (lazy-loaded on first request)
_embedding_model = None
_model_name = os.getenv("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
_provider_name = os.getenv("EMBEDDING_PROVIDER", "huggingface")
_lock_selection = (os.getenv("EMBEDDING_LOCK", "false").lower() in ["1", "true", "yes"]) 
_selection_file = os.getenv("EMBEDDING_SELECTION_PATH", str(Path(__file__).parent / "selection.json"))


def _resolve_fastembed_model_name() -> str:
    """Pick a valid fastembed model name from env/config defaults."""
    explicit_fastembed = os.getenv("FASTEMBED_MODEL")
    if explicit_fastembed:
        return explicit_fastembed

    if _model_name and not _model_name.startswith("text-embedding-"):
        return _model_name

    return "BAAI/bge-small-en-v1.5"


class _FastEmbedAdapter:
    """Adapter to expose a sentence-transformers-like encode API via fastembed."""

    def __init__(self, model_name: str):
        from fastembed import TextEmbedding

        self.model_name = model_name
        self._embedder = TextEmbedding(model_name=model_name)

    def encode(self, inputs, convert_to_numpy: bool = True):
        if isinstance(inputs, str):
            texts = [inputs]
            single = True
        else:
            texts = list(inputs)
            single = False

        embeddings = list(self._embedder.embed(texts))
        if not embeddings:
            raise RuntimeError("FastEmbed returned no embeddings")

        array = np.array(embeddings)
        if single:
            return array[0]
        return array


def get_embedding_model():
    """Lazy-load embedding model on first request."""
    global _embedding_model
    if _embedding_model is None:
        logger.info(f"Loading embedding model: {_model_name}")
        if _provider_name == "fastembed":
            try:
                fallback_model = _resolve_fastembed_model_name()
                _embedding_model = _FastEmbedAdapter(fallback_model)
                logger.info("Embedding provider: fastembed")
                logger.info("✅ FastEmbed model loaded successfully: %s", fallback_model)
                return _embedding_model
            except Exception as exc:
                logger.error("❌ Failed to load fastembed model: %s", exc)
                raise RuntimeError(f"Failed to load fastembed model: {exc}")

        try:
            from sentence_transformers import SentenceTransformer

            _embedding_model = SentenceTransformer(_model_name)
            logger.info("Embedding provider: sentence-transformers")
            logger.info("✅ Embedding model loaded successfully")
        except ModuleNotFoundError as e:
            logger.warning("sentence_transformers is unavailable (%s). Falling back to FastEmbed.", e)
            try:
                fallback_model = _resolve_fastembed_model_name()
                _embedding_model = _FastEmbedAdapter(fallback_model)
                logger.info("Embedding provider: fastembed")
                logger.info("✅ FastEmbed model loaded successfully: %s", fallback_model)
            except Exception as fallback_exc:
                logger.error("❌ FastEmbed fallback failed: %s", fallback_exc)
                raise RuntimeError(
                    "Failed to load embedding model: sentence_transformers unavailable and fastembed fallback failed: "
                    f"{fallback_exc}"
                )
        except Exception as e:
            logger.error(f"❌ Failed to load embedding model: {e}")
            raise RuntimeError(f"Failed to load embedding model: {e}")
    return _embedding_model


# Request/Response Models
class EmbedRequest(BaseModel):
    """Single text embedding request."""

    text: str = Field(..., min_length=1, max_length=10000,
                      description="Text to embed")


class BatchEmbedRequest(BaseModel):
    """Batch text embedding request."""

    texts: List[str] = Field(
        ..., min_items=1, max_items=100, description="List of texts to embed"
    )


class EmbeddingResponse(BaseModel):
    """Embedding response with metadata."""

    embedding: List[float] = Field(...,
                                   description="384-dimensional embedding vector")
    dimension: int = Field(default=384, description="Embedding dimension")
    model: str = Field(default=_model_name, description="Model used")


class BatchEmbeddingResponse(BaseModel):
    """Batch embedding response."""

    embeddings: List[List[float]
                     ] = Field(..., description="List of embedding vectors")
    dimension: int = Field(default=384, description="Embedding dimension")
    count: int = Field(..., description="Number of embeddings")
    model: str = Field(default=_model_name, description="Model used")


# Health Check
@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "ok", "service": "embedding"}


class EmbeddingSelection(BaseModel):
    provider: str
    model: str
    lock: bool | None = None


def _load_selection_file():
    try:
        p = Path(_selection_file)
        if p.exists():
            data = p.read_text()
            js = __import__("json").loads(data)
            global _provider_name, _model_name, _lock_selection, _embedding_model
            _provider_name = js.get("provider", _provider_name)
            _model_name = js.get("model", _model_name)
            _lock_selection = bool(js.get("lock", _lock_selection))
            _embedding_model = None  # force reload with new model
            logger.info(f"Embedding selection loaded: provider={_provider_name}, model={_model_name}, lock={_lock_selection}")
    except Exception as e:
        logger.warning(f"Failed to load embedding selection file: {e}")


def _save_selection_file(provider: str, model: str, lock: bool | None):
    try:
        payload = {"provider": provider, "model": model, "lock": _lock_selection if lock is None else bool(lock)}
        Path(_selection_file).parent.mkdir(parents=True, exist_ok=True)
        Path(_selection_file).write_text(__import__("json").dumps(payload, indent=2))
        _load_selection_file()
    except Exception as e:
        logger.error(f"Failed to save embedding selection file: {e}")


# Single Embedding
@app.post("/embed", response_model=EmbeddingResponse)
async def embed(request: EmbedRequest):
    """
    Generate embedding for a single text.

    Args:
        request: EmbedRequest with text to embed

    Returns:
        EmbeddingResponse with embedding vector and metadata
    """
    try:
        model = get_embedding_model()
        embedding = model.encode(request.text, convert_to_numpy=True)
        return EmbeddingResponse(
            embedding=embedding.tolist(),
            dimension=len(embedding),
            model=_model_name,
        )
    except Exception as e:
        logger.error(f"Error generating embedding: {e}")
        raise HTTPException(
            status_code=500, detail=f"Embedding error: {str(e)}")


# Batch Embeddings
@app.post("/embed-batch", response_model=BatchEmbeddingResponse)
async def embed_batch(request: BatchEmbedRequest):
    """
    Generate embeddings for multiple texts (batch).

    Args:
        request: BatchEmbedRequest with list of texts to embed

    Returns:
        BatchEmbeddingResponse with list of embedding vectors
    """
    try:
        model = get_embedding_model()
        embeddings = model.encode(request.texts, convert_to_numpy=True)
        return BatchEmbeddingResponse(
            embeddings=[emb.tolist() for emb in embeddings],
            dimension=embeddings.shape[1],
            count=len(embeddings),
            model=_model_name,
        )
    except Exception as e:
        logger.error(f"Error generating batch embeddings: {e}")
        raise HTTPException(
            status_code=500, detail=f"Batch embedding error: {str(e)}")


# Similarity Search (optional utility)
@app.post("/similarity")
async def similarity(query_request: EmbedRequest, texts_request: BatchEmbedRequest):
    """
    Find most similar texts to a query.

    Args:
        query_request: Query text to find matches for
        texts_request: List of candidate texts

    Returns:
        List of (text, similarity_score) tuples sorted by similarity
    """
    try:
        from sklearn.metrics.pairwise import cosine_similarity

        model = get_embedding_model()

        # Encode query and texts
        query_embedding = model.encode(query_request.text)
        text_embeddings = model.encode(texts_request.texts)

        # Compute similarity
        similarities = cosine_similarity([query_embedding], text_embeddings)[0]

        # Return sorted results
        results = [
            {"text": text, "similarity": float(sim)}
            for text, sim in zip(texts_request.texts, similarities)
        ]
        results.sort(key=lambda x: x["similarity"], reverse=True)

        return {"query": query_request.text, "results": results}
    except Exception as e:
        logger.error(f"Error computing similarity: {e}")
        raise HTTPException(
            status_code=500, detail=f"Similarity error: {str(e)}")


# Root endpoint
@app.get("/")
async def root():
    """Root endpoint with service info."""
    return {
        "name": "Vecinita Embedding Service",
        "version": "0.1.0",
        "model": _model_name,
        "endpoints": {
            "health": "GET /health",
            "embed_single": "POST /embed",
            "embed_batch": "POST /embed-batch",
            "similarity": "POST /similarity",
        },
        "provider": _provider_name,
        "locked": _lock_selection,
    }


@app.get("/config")
async def get_config():
    return {
        "current": {"provider": _provider_name, "model": _model_name, "locked": _lock_selection},
        "available": {
            "providers": [
                {"key": "huggingface", "label": "HuggingFace (local)"},
                {"key": "fastembed", "label": "FastEmbed (fallback)"},
            ],
            "models": {
                "huggingface": [
                    "sentence-transformers/all-MiniLM-L6-v2",
                    "BAAI/bge-small-en-v1.5",
                    "sentence-transformers/all-mpnet-base-v2",
                ],
                "fastembed": [
                    "BAAI/bge-small-en-v1.5",
                    "sentence-transformers/all-MiniLM-L6-v2",
                ],
            },
        },
    }


@app.post("/config")
async def set_config(sel: EmbeddingSelection):
    if _lock_selection:
        raise HTTPException(status_code=403, detail="Embedding selection is locked")
    if sel.provider not in {"huggingface", "fastembed"}:
        raise HTTPException(status_code=400, detail="Only 'huggingface' and 'fastembed' providers are supported")

    selected_model = sel.model
    if sel.provider == "fastembed" and not selected_model:
        selected_model = os.getenv("FASTEMBED_MODEL", "BAAI/bge-small-en-v1.5")

    _save_selection_file(sel.provider, selected_model, sel.lock)
    return {"status": "ok", "current": {"provider": _provider_name, "model": _model_name, "locked": _lock_selection}}


if __name__ == "__main__":
    import uvicorn

    port = int(os.environ.get("PORT", 8001))
    uvicorn.run(app, host="0.0.0.0", port=port)
