"""Modal app: vecinita-embedding — FastEmbed 384-dim (ADR-008).

Deploy: modal deploy infra/modal/embedding_app.py
"""

from __future__ import annotations

import modal

APP_NAME = "vecinita-embedding"
VOLUME_NAME = "embedding-models"
MODEL_NAME = "BAAI/bge-small-en-v1.5"

app = modal.App(APP_NAME)
model_volume = modal.Volume.from_name(VOLUME_NAME, create_if_missing=True)

image = (
    modal.Image.debian_slim(python_version="3.11")
    .pip_install("fastapi>=0.115,<1", "fastembed>=0.4,<0.5", "pydantic>=2.7,<3")
)


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
def fastapi_app():
    from fastapi import FastAPI
    from pydantic import BaseModel, ConfigDict, Field

    class EmbedRequest(BaseModel):
        model_config = ConfigDict(extra="forbid")
        text: str = Field(..., min_length=1)

    class EmbedBatchRequest(BaseModel):
        model_config = ConfigDict(extra="forbid")
        texts: list[str] = Field(..., min_length=1)

    class EmbedResponse(BaseModel):
        embedding: list[float]

    class EmbedBatchResponse(BaseModel):
        embeddings: list[list[float]]

    web = FastAPI(title="vecinita-embedding", version="0.1.0")
    service = EmbeddingService()

    @web.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @web.post("/embed", response_model=EmbedResponse)
    def embed(body: EmbedRequest) -> EmbedResponse:
        vectors = service.embed_texts.remote([body.text])
        return EmbedResponse(embedding=vectors[0])

    @web.post("/embed/batch", response_model=EmbedBatchResponse)
    def embed_batch(body: EmbedBatchRequest) -> EmbedBatchResponse:
        vectors = service.embed_texts.remote(body.texts)
        return EmbedBatchResponse(embeddings=vectors)

    return web
