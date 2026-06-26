"""Modal app: vecinita-embedding — FastEmbed 384-dim (ADR-008).

Deploy: modal deploy infra/modal/embedding_app.py
Stage weights: modal run infra/modal/embedding_app.py::stage_embedding_weights
"""

from __future__ import annotations

import json

import modal

APP_NAME = "vecinita-embedding"
VOLUME_NAME = "embedding-models"
MODEL_NAME = "BAAI/bge-small-en-v1.5"

app = modal.App(APP_NAME)
model_volume = modal.Volume.from_name(VOLUME_NAME, create_if_missing=True)

image = modal.Image.debian_slim(python_version="3.11").pip_install(
    "fastembed>=0.4,<0.5", "pydantic>=2.7,<3", "starlette>=0.38,<1"
)

# Import the remote-only dep in global scope so it is captured in the CPU memory
# snapshot (S001 Tier-1). FastEmbed/ONNX is CPU-only, so no GPU snapshot is needed.
with image.imports():
    from fastembed import TextEmbedding


@app.function(
    image=image,
    volumes={"/models": model_volume},
    timeout=600,
)
def stage_embedding_weights() -> str:
    """One-shot: download FastEmbed model into the embedding-models volume."""
    model = TextEmbedding(model_name=MODEL_NAME, cache_dir="/models")
    vectors = list(model.embed(["vecinita staging warmup"]))
    dim = len(vectors[0])
    model_volume.commit()
    return f"staged {MODEL_NAME} dim={dim}"


@app.cls(
    image=image,
    volumes={"/models": model_volume},
    timeout=120,
    # Keep the CPU container warm longer between bursts (was unset → 60s default);
    # cheap for a CPU service and cuts repeat cold starts (S001 Tier-0).
    scaledown_window=600,
    # CPU memory snapshot: skip ONNX/library init on most boots (S001 Tier-1).
    enable_memory_snapshot=True,
)
class EmbeddingService:
    @modal.enter(snap=True)
    def load_model(self) -> None:
        self._model = TextEmbedding(model_name=MODEL_NAME, cache_dir="/models")
        # Warm-up forward pass inside snap=True so the ONNX session / first-inference
        # init is folded into the CPU memory snapshot instead of hitting the first
        # request as tail latency (Modal docs: warm up in snap=True). S001 Tier-1.
        list(self._model.embed(["warmup"]))

    @modal.method()
    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        return [vector.tolist() for vector in self._model.embed(texts)]


@app.function(image=image)
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
        return JSONResponse({"status": "ok"})

    async def warm(_: Request) -> JSONResponse:
        """Boot EmbeddingService during user think-time (S001 T11)."""
        service.embed_texts.remote(["warmup"])
        return JSONResponse({"status": "ok"})

    async def embed(request: Request) -> JSONResponse:
        try:
            payload = json.loads(await request.body())
            item = EmbedRequest.model_validate(payload)
        except (json.JSONDecodeError, ValidationError) as exc:
            return JSONResponse({"detail": str(exc)}, status_code=422)
        vectors = service.embed_texts.remote([item.text])
        return JSONResponse({"embedding": vectors[0]})

    async def embed_batch(request: Request) -> JSONResponse:
        try:
            payload = json.loads(await request.body())
            item = EmbedBatchRequest.model_validate(payload)
        except (json.JSONDecodeError, ValidationError) as exc:
            return JSONResponse({"detail": str(exc)}, status_code=422)
        vectors = service.embed_texts.remote(item.texts)
        return JSONResponse({"embeddings": vectors})

    return Starlette(
        routes=[
            Route("/health", health, methods=["GET"]),
            Route("/warm", warm, methods=["POST"]),
            Route("/embed", embed, methods=["POST"]),
            Route("/embed/batch", embed_batch, methods=["POST"]),
        ]
    )
