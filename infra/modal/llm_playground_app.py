"""Modal app: vecinita-llm-playground — vLLM + HF list/pull with model_id reload (ADR-037).

Deploy: modal deploy infra/modal/llm_playground_app.py

Shares volume ``llm-models`` with prod ``vecinita-llm`` (TP-S010-25 / TP-S010-28).
Sandbox eval and DM list/pull may switch ``model_id`` (~60-120s reload) without
stomping the pinned prod app.

F77: may load a pre-promote LoRA candidate via ``VECINITA_PLAYGROUND_FINETUNE_ADAPTER_ID``
from volume ``llm-finetune-adapters`` (ADR-053) — never auto-loads prod promote pin.

Requires Modal secret ``vecinita-llm`` with ``VECINITA_MODAL_PROXY_KEY`` (same as prod).
"""

from __future__ import annotations

import json
import logging
import uuid
from http import HTTPStatus
from typing import TYPE_CHECKING, ClassVar, Final

import modal
from infra.modal.llm_app import (
    ADAPTERS_VOLUME_NAME,
    DEFAULT_PLAYGROUND_MODEL_ID,
    MODEL_ID,
    GenerateRequest,
    PullRequest,
    ServeRole,
    WarmRequest,
    _authorized,  # pyright: ignore[reportPrivateUsage]  # shared ASGI auth
    _download_hf_model,  # pyright: ignore[reportPrivateUsage]
    _list_models_payload,  # pyright: ignore[reportPrivateUsage]
    _mark_model_available,  # pyright: ignore[reportPrivateUsage]
    _register_pending_model,  # pyright: ignore[reportPrivateUsage]
    image,
)
from infra.modal.llm_model_registry import resolve_hf_repo
from infra.modal.llm_service_core import LlmServiceCore
from pydantic import ValidationError

if TYPE_CHECKING:
    from starlette.requests import Request

logger = logging.getLogger("vecinita.llm.playground")

APP_NAME: Final[str] = "vecinita-llm-playground"
VOLUME_NAME: Final[str] = "llm-models"
ALLOW_MODEL_RELOAD: Final[bool] = True

app = modal.App(APP_NAME)
model_volume = modal.Volume.from_name(VOLUME_NAME, create_if_missing=True)
adapters_volume = modal.Volume.from_name(ADAPTERS_VOLUME_NAME, create_if_missing=True)
pull_jobs = modal.Dict.from_name("vecinita-llm-playground-pull-jobs", create_if_missing=True)

_LLM_ASGI_SECRETS = [modal.Secret.from_name("vecinita-llm")]


@app.function(
    image=image,
    volumes={"/models": model_volume},
    timeout=3600,
)
def stage_default_model() -> str:
    """One-shot: stage the default playground model tag onto the shared volume."""
    _download_hf_model(DEFAULT_PLAYGROUND_MODEL_ID)
    _mark_model_available(DEFAULT_PLAYGROUND_MODEL_ID)
    return f"staged {DEFAULT_PLAYGROUND_MODEL_ID}"


@app.function(
    image=image,
    volumes={"/models": model_volume},
    timeout=3600,
)
def pull_model_job(job_id: str, model_id: str) -> str:
    """Background HF download for a playground model tag."""
    pull_jobs[job_id] = {"model_id": model_id, "status": "pulling"}
    try:
        _download_hf_model(model_id)
    except (ValueError, OSError) as exc:
        pull_jobs[job_id] = {"model_id": model_id, "status": "failed", "error": str(exc)}
        raise
    else:
        _mark_model_available(model_id)
        pull_jobs[job_id] = {"model_id": model_id, "status": "available"}
        return model_id


@app.cls(
    image=image,
    gpu="T4",
    volumes={"/models": model_volume, "/adapters": adapters_volume},
    scaledown_window=300,
    timeout=900,
    # model_id switching requires clean vLLM init — GPU snapshot breaks NCCL on reload.
    enable_memory_snapshot=False,
)
class LlmService(LlmServiceCore):
    """Playground GPU service — reloads vLLM when ``model_id`` changes (ALLOW_MODEL_RELOAD)."""

    serve_role: ClassVar[ServeRole] = "playground"
    allow_model_reload: ClassVar[bool] = ALLOW_MODEL_RELOAD

    @modal.enter()
    def load_model(self) -> None:
        super().load_model()

    @modal.exit()
    def unload_model(self) -> None:
        super().unload_model()

    @modal.method()
    def complete(
        self,
        prompt: str,
        *,
        max_tokens: int = 512,
        temperature: float = 0.2,
        model_id: str | None = None,
    ) -> str:
        return super().complete(
            prompt,
            max_tokens=max_tokens,
            temperature=temperature,
            model_id=model_id,
        )

    @modal.method()
    def stream_tokens(
        self,
        prompt: str,
        *,
        max_tokens: int = 512,
        temperature: float = 0.2,
        model_id: str | None = None,
    ):
        """Yield incremental tokens for SSE (real vLLM deltas)."""
        yield from super().stream_tokens(
            prompt,
            max_tokens=max_tokens,
            temperature=temperature,
            model_id=model_id,
        )

    @modal.method()
    def warm_model(self, model_id: str | None = None) -> str:
        """Preload a model into VRAM (fold cold-start into warm-up window)."""
        return super().warm_model(model_id)


@app.function(
    image=image,
    timeout=1200,
    secrets=_LLM_ASGI_SECRETS,
    volumes={"/models": model_volume},
)
@modal.asgi_app()
def fastapi_app():
    """Starlette ASGI — health, generate, model list/pull (playground reload surface)."""
    from starlette.applications import Starlette
    from starlette.responses import JSONResponse, StreamingResponse
    from starlette.routing import Route

    service = LlmService()

    async def health(_: Request) -> JSONResponse:
        return JSONResponse({"status": "ok"})

    async def warm(request: Request) -> JSONResponse:
        if not _authorized(request):
            return JSONResponse({"detail": "Unauthorized"}, status_code=HTTPStatus.UNAUTHORIZED)
        raw = await request.body()
        try:
            payload = WarmRequest.model_validate(json.loads(raw)) if raw else WarmRequest()
        except (json.JSONDecodeError, ValidationError) as exc:
            return JSONResponse({"detail": str(exc)}, status_code=HTTPStatus.UNPROCESSABLE_ENTITY)
        try:
            loaded = service.warm_model.remote(payload.model_id)
        except RuntimeError as exc:
            return JSONResponse({"detail": str(exc)}, status_code=HTTPStatus.BAD_GATEWAY)
        return JSONResponse(
            {
                "status": "ok",
                "model_id": payload.model_id or DEFAULT_PLAYGROUND_MODEL_ID,
                "loaded": loaded,
            }
        )

    async def list_models(request: Request) -> JSONResponse:
        if not _authorized(request):
            return JSONResponse({"detail": "Unauthorized"}, status_code=HTTPStatus.UNAUTHORIZED)
        return JSONResponse(_list_models_payload())

    async def pull_model(request: Request) -> JSONResponse:
        if not _authorized(request):
            return JSONResponse({"detail": "Unauthorized"}, status_code=HTTPStatus.UNAUTHORIZED)
        try:
            payload = PullRequest.model_validate(json.loads(await request.body()))
        except (json.JSONDecodeError, ValidationError) as exc:
            return JSONResponse({"detail": str(exc)}, status_code=HTTPStatus.UNPROCESSABLE_ENTITY)
        try:
            resolve_hf_repo(payload.model_id)
        except ValueError as exc:
            return JSONResponse({"detail": str(exc)}, status_code=HTTPStatus.BAD_REQUEST)
        job_id = str(uuid.uuid4())
        pull_model_job.spawn(job_id, payload.model_id)
        _register_pending_model(payload.model_id)
        return JSONResponse(
            {
                "job_id": job_id,
                "model_id": payload.model_id,
                "status": "pulling",
            },
            status_code=HTTPStatus.ACCEPTED,
        )

    async def generate(request: Request) -> JSONResponse:
        if not _authorized(request):
            return JSONResponse({"detail": "Unauthorized"}, status_code=HTTPStatus.UNAUTHORIZED)
        try:
            payload = GenerateRequest.model_validate(json.loads(await request.body()))
        except (json.JSONDecodeError, ValidationError) as exc:
            return JSONResponse({"detail": str(exc)}, status_code=422)
        try:
            text = service.complete.remote(
                payload.prompt,
                max_tokens=payload.max_tokens,
                temperature=payload.temperature,
                model_id=payload.model_id,
            )
        except RuntimeError as exc:
            return JSONResponse({"detail": str(exc)}, status_code=HTTPStatus.BAD_GATEWAY)
        return JSONResponse({"text": text})

    async def generate_stream(request: Request) -> StreamingResponse | JSONResponse:
        if not _authorized(request):
            return JSONResponse({"detail": "Unauthorized"}, status_code=HTTPStatus.UNAUTHORIZED)
        try:
            payload = GenerateRequest.model_validate(json.loads(await request.body()))
        except (json.JSONDecodeError, ValidationError) as exc:
            return JSONResponse({"detail": str(exc)}, status_code=422)

        def event_stream():
            for token in service.stream_tokens.remote_gen(
                payload.prompt,
                max_tokens=payload.max_tokens,
                temperature=payload.temperature,
                model_id=payload.model_id,
            ):
                yield f"data: {json.dumps({'token': token})}\n\n"
            yield f"data: {json.dumps({'done': True})}\n\n"

        return StreamingResponse(event_stream(), media_type="text/event-stream")

    return Starlette(
        routes=[
            Route("/health", health, methods=["GET"]),
            Route("/warm", warm, methods=["POST"]),
            Route("/models/ollama", list_models, methods=["GET"]),
            Route("/models/ollama/pull", pull_model, methods=["POST"]),
            Route("/generate", generate, methods=["POST"]),
            Route("/generate/stream", generate_stream, methods=["POST"]),
        ]
    )


__all__ = [
    "ALLOW_MODEL_RELOAD",
    "APP_NAME",
    "DEFAULT_PLAYGROUND_MODEL_ID",
    "MODEL_ID",
    "VOLUME_NAME",
    "app",
]
