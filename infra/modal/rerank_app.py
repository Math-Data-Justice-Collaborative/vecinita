"""Modal app: vecinita-rerank — cross-encoder rerank (F45 / EV-029).

Deploy: modal deploy infra/modal/rerank_app.py
Model: BAAI/bge-reranker-v2-m3 on T4 (RD-213)
"""

from __future__ import annotations

import json
import os

import modal
from infra.modal.repo_paths import resolve_repo_root

APP_NAME = "vecinita-rerank"
VOLUME_NAME = "rerank-models"
CE_MODEL = "BAAI/bge-reranker-v2-m3"

_RERANK_SECRETS = [modal.Secret.from_name("vecinita-rerank")]


_REPO_ROOT = resolve_repo_root()

app = modal.App(APP_NAME)
model_volume = modal.Volume.from_name(VOLUME_NAME, create_if_missing=True)

image = modal.Image.debian_slim(python_version="3.11").pip_install(
    "sentence-transformers>=3.0,<4",
    "torch>=2.2,<3",
    "transformers>=4.40,<5",
    "httpx>=0.27,<1",
    "starlette>=0.37,<1",
)


@app.cls(
    image=image,
    gpu="T4",
    volumes={"/models": model_volume},
    timeout=900,
    scaledown_window=120,
    secrets=_RERANK_SECRETS,
)
class RerankService:
    """Cross-encoder scorer for production ChatRAG rerank (F45)."""

    @modal.enter()
    def load(self) -> None:
        from sentence_transformers import CrossEncoder

        os.environ.setdefault("HF_HOME", "/models/hf")
        os.environ.setdefault("TRANSFORMERS_CACHE", "/models/hf")
        model_id = os.environ.get("VECINITA_RAG_RERANK_CE_MODEL", CE_MODEL)
        self._model = CrossEncoder(model_id, device="cuda")
        _ = self._model.predict([["warmup query", "warmup passage"]])
        model_volume.commit()

    @modal.method()
    def score_pairs(self, query: str, passages: list[str]) -> list[float]:
        if not passages:
            return []
        pairs = [[query, p] for p in passages]
        scores = self._model.predict(pairs)
        return [float(s) for s in scores]


@app.function(image=image, secrets=_RERANK_SECRETS)
@modal.asgi_app()
def rerank_api():
    from starlette.applications import Starlette
    from starlette.requests import Request
    from starlette.responses import JSONResponse
    from starlette.routing import Route

    service = RerankService()

    async def health(_: Request) -> JSONResponse:
        return JSONResponse({"status": "ok", "model_id": CE_MODEL})

    async def score(request: Request) -> JSONResponse:
        try:
            payload = json.loads(await request.body())
        except json.JSONDecodeError as exc:
            return JSONResponse({"detail": str(exc)}, status_code=422)
        if not isinstance(payload, dict):
            return JSONResponse({"detail": "body must be object"}, status_code=422)
        query = payload.get("query")
        passages_obj = payload.get("passages")
        if not isinstance(query, str) or not query.strip():
            return JSONResponse({"detail": "query required"}, status_code=422)
        if not isinstance(passages_obj, list):
            return JSONResponse({"detail": "passages must be list"}, status_code=422)
        passages = [str(p) for p in passages_obj]
        scores = service.score_pairs.remote(query, passages)
        return JSONResponse({"scores": scores})

    return Starlette(
        routes=[
            Route("/health", health, methods=["GET"]),
            Route("/score", score, methods=["POST"]),
        ],
    )
