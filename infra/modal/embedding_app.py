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

image = (
    modal.Image.debian_slim(python_version="3.11")
    .pip_install("fastembed>=0.4,<0.5", "pydantic>=2.7,<3", "starlette>=0.38,<1")
)


@app.function(
    image=image,
    volumes={"/models": model_volume},
    timeout=600,
)
def stage_embedding_weights() -> str:
    """One-shot: download FastEmbed model into the embedding-models volume."""
    from fastembed import TextEmbedding

    model = TextEmbedding(model_name=MODEL_NAME, cache_dir="/models")
    vectors = list(model.embed(["vecinita staging warmup"]))
    dim = len(vectors[0])
    model_volume.commit()
    return f"staged {MODEL_NAME} dim={dim}"


@app.cls(
    image=image,
    volumes={"/models": model_volume},
    timeout=120,
)
class EmbeddingService:
    @modal.enter()
    def load_model(self) -> None:
        from fastembed import TextEmbedding

        self._model = TextEmbedding(model_name=MODEL_NAME, cache_dir="/models")

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
            Route("/embed", embed, methods=["POST"]),
            Route("/embed/batch", embed_batch, methods=["POST"]),
        ]
    )
