"""Modal app: vecinita-embedding — 384-d embeddings (ADR-048 / F70).

Deploy: modal deploy infra/modal/embedding_app.py
Stage weights: modal run infra/modal/embedding_app.py::stage_embedding_weights

Runtime: ``VECINITA_EMBED_RUNTIME`` = fastembed | sentence_transformers | onnx
Model: ``VECINITA_EMBEDDING_MODEL_ID`` (default multilingual-e5-small)
"""

from __future__ import annotations

import json
import logging
import os
from typing import Protocol, cast

import modal
from infra.modal.repo_paths import resolve_repo_root
from vecinita_embedding_client.modal_pins import (
    DEFAULT_EMBEDDING_MODEL_ID,
    EMBED_IMAGE_PIPS,
    EMBED_MEMORY_MIB,
    EMBED_SERVICE_TIMEOUT_S,
    EMBED_STAGE_TIMEOUT_S,
)
from vecinita_embedding_client.prefixes import resolve_embed_runtime

APP_NAME = "vecinita-embedding"
VOLUME_NAME = "embedding-models"
_LOG = logging.getLogger(__name__)


_REPO_ROOT = resolve_repo_root()
_PKG_ROOT = "/opt/vecinita"
_PYTHONPATH = ":".join(
    [
        f"{_PKG_ROOT}/packages/embedding-client",
        f"{_PKG_ROOT}/packages/shared-schemas",
    ],
)

app = modal.App(APP_NAME)
model_volume = modal.Volume.from_name(VOLUME_NAME, create_if_missing=True)
# Pin + runtime (S027-D55): VECINITA_EMBED_RUNTIME / VECINITA_EMBEDDING_MODEL_ID
_EMBED_SECRETS = [modal.Secret.from_name("vecinita-embedding")]

image = (
    modal.Image.debian_slim(python_version="3.11")
    .pip_install(
        *EMBED_IMAGE_PIPS,
        "httpx>=0.27,<1",
    )
    .env({"PYTHONPATH": _PYTHONPATH})
    .add_local_dir(
        _REPO_ROOT / "packages" / "embedding-client",
        remote_path=f"{_PKG_ROOT}/packages/embedding-client",
    )
    .add_local_dir(
        _REPO_ROOT / "packages" / "shared-schemas",
        remote_path=f"{_PKG_ROOT}/packages/shared-schemas",
    )
)

# Capture FastEmbed + ST in the CPU memory snapshot (S001 Tier-1). CPU only — no GPU.
with image.imports():
    from fastembed import TextEmbedding
    from sentence_transformers import SentenceTransformer


def _model_id() -> str:
    raw = os.environ.get("VECINITA_EMBEDDING_MODEL_ID", "").strip()
    return raw or DEFAULT_EMBEDDING_MODEL_ID


class _EmbedBackend(Protocol):
    def embed(self, texts: list[str]) -> list[list[float]]:
        """Return one 384-d vector per input text."""
        ...


class _FastEmbedBackend:
    def __init__(self, model_id: str, cache_dir: str) -> None:
        self._model = TextEmbedding(model_name=model_id, cache_dir=cache_dir)

    def embed(self, texts: list[str]) -> list[list[float]]:
        return [vector.tolist() for vector in self._model.embed(texts)]


class _SentenceTransformersBackend:
    def __init__(self, model_id: str, cache_dir: str) -> None:
        self._model = SentenceTransformer(model_id, cache_folder=cache_dir)

    def embed(self, texts: list[str]) -> list[list[float]]:
        raw = self._model.encode(
            texts,
            normalize_embeddings=True,
            convert_to_numpy=True,
        )
        return cast("list[list[float]]", raw.tolist())


class _OnnxSentenceTransformersBackend:
    """ONNX path via sentence-transformers ONNX backend when runtime=onnx."""

    def __init__(self, model_id: str, cache_dir: str) -> None:
        self._model = SentenceTransformer(
            model_id,
            cache_folder=cache_dir,
            backend="onnx",
        )

    def embed(self, texts: list[str]) -> list[list[float]]:
        raw = self._model.encode(
            texts,
            normalize_embeddings=True,
            convert_to_numpy=True,
        )
        return cast("list[list[float]]", raw.tolist())


def _load_backend(cache_dir: str) -> _EmbedBackend:
    """Load the configured embed backend; FastEmbed → ST on unsupported pins (S027-D12)."""
    runtime = resolve_embed_runtime()
    model_id = _model_id()
    if runtime == "fastembed":
        try:
            return _FastEmbedBackend(model_id, cache_dir)
        except ValueError as exc:
            # S019 spike + BUG-2026-08-05: FastEmbed lacks multilingual-e5-small.
            _LOG.warning(
                "FastEmbed cannot load %s (%s); falling back to sentence_transformers",
                model_id,
                exc,
            )
            return _SentenceTransformersBackend(model_id, cache_dir)
    if runtime == "onnx":
        return _OnnxSentenceTransformersBackend(model_id, cache_dir)
    return _SentenceTransformersBackend(model_id, cache_dir)


@app.function(
    image=image,
    volumes={"/models": model_volume},
    timeout=EMBED_STAGE_TIMEOUT_S,
    memory=EMBED_MEMORY_MIB,
    secrets=_EMBED_SECRETS,
)
def stage_embedding_weights() -> str:
    """One-shot: download embed model weights into the embedding-models volume."""
    backend = _load_backend("/models")
    vectors = backend.embed(["vecinita staging warmup"])
    dim = len(vectors[0])
    model_volume.commit()
    runtime = resolve_embed_runtime()
    return f"staged {_model_id()} runtime={runtime} dim={dim}"


@app.cls(
    image=image,
    volumes={"/models": model_volume},
    timeout=EMBED_SERVICE_TIMEOUT_S,
    memory=EMBED_MEMORY_MIB,
    scaledown_window=600,
    enable_memory_snapshot=True,
    secrets=_EMBED_SECRETS,
)
class EmbeddingService:
    @modal.enter(snap=True)
    def load_model(self) -> None:
        self._backend = _load_backend("/models")
        _ = self._backend.embed(["warmup"])

    @modal.method()
    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        return self._backend.embed(texts)


@app.function(image=image, memory=EMBED_MEMORY_MIB, secrets=_EMBED_SECRETS)
@modal.asgi_app()
def embedding_api():
    from pydantic import BaseModel, ConfigDict, Field, ValidationError
    from starlette.applications import Starlette
    from starlette.requests import Request
    from starlette.responses import JSONResponse
    from starlette.routing import Route

    class EmbedRequest(BaseModel):
        model_config = ConfigDict(extra="forbid")
        text: str = Field(..., min_length=1)

    class EmbedBatchRequest(BaseModel):
        model_config = ConfigDict(extra="forbid")
        texts: list[str] = Field(..., min_length=1)

    service = EmbeddingService()

    async def health(_: Request) -> JSONResponse:
        return JSONResponse(
            {
                "status": "ok",
                "model_id": _model_id(),
                "runtime": resolve_embed_runtime(),
            },
        )

    async def warm(_request: Request) -> JSONResponse:
        """Boot EmbeddingService during user think-time (S001 T11).

        Fire-and-forget via ``.spawn()`` so the ASGI worker is not held while
        the class container cold-starts (BUG-2026-08-27 queue saturation).
        """
        _ = service.embed_texts.spawn(["warmup"])
        return JSONResponse({"status": "ok"})

    async def embed(request: Request) -> JSONResponse:
        try:
            payload = json.loads(await request.body())
            item = EmbedRequest.model_validate(payload)
        except (json.JSONDecodeError, ValidationError) as exc:
            return JSONResponse({"detail": str(exc)}, status_code=422)
        # ``.aio`` keeps the ASGI event loop free (BUG-2026-08-27 / #275).
        vectors = await service.embed_texts.remote.aio([item.text])
        return JSONResponse({"embedding": vectors[0]})

    async def embed_batch(request: Request) -> JSONResponse:
        try:
            payload = json.loads(await request.body())
            item = EmbedBatchRequest.model_validate(payload)
        except (json.JSONDecodeError, ValidationError) as exc:
            return JSONResponse({"detail": str(exc)}, status_code=422)
        vectors = await service.embed_texts.remote.aio(item.texts)
        return JSONResponse({"embeddings": vectors})

    return Starlette(
        routes=[
            Route("/health", health, methods=["GET"]),
            Route("/warm", warm, methods=["POST"]),
            Route("/embed", embed, methods=["POST"]),
            Route("/embed/batch", embed_batch, methods=["POST"]),
        ]
    )
