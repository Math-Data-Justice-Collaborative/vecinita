"""Thin CPU ASGI route builder for prod ``vecinita-llm`` (EV-317 / #317).

Keeps Starlette/auth/Pydantic route wiring free of vLLM / ``LlmServiceCore`` imports
so the ASGI entry surface stays CPU-probe friendly. GPU work stays on ``LlmService``
methods (``.spawn`` / ``.remote``).

[Spec: docs/adr/ADR-022-gpu-memory-snapshot-cold-start.md §Amendment EV-317]
"""

from __future__ import annotations

import json
import logging
import os
import uuid
from collections.abc import Callable, Iterator
from dataclasses import dataclass
from http import HTTPStatus
from typing import Protocol

from pydantic import BaseModel, ConfigDict, Field, ValidationError
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import JSONResponse, StreamingResponse
from starlette.routing import Route

logger = logging.getLogger("vecinita.llm")

_PROXY_HEADER = "X-Vecinita-Proxy-Key"
_PROXY_ENV = "VECINITA_MODAL_PROXY_KEY"
_DEFAULT_MODEL_ID = "qwen2.5:1.5b-instruct"


class PullRequest(BaseModel):
    """POST /models/ollama/pull body."""

    model_config = ConfigDict(extra="forbid")
    model_id: str = Field(min_length=1, max_length=128)


class WarmRequest(BaseModel):
    """POST /warm body."""

    model_config = ConfigDict(extra="forbid")
    model_id: str | None = None


class GenerateRequest(BaseModel):
    """POST /generate and /generate/stream body."""

    model_config = ConfigDict(extra="forbid")
    prompt: str = Field(min_length=1)
    max_tokens: int = Field(default=512, ge=1, le=2048)
    temperature: float = Field(default=0.2, ge=0.0, le=2.0)
    model_id: str | None = Field(default=None, max_length=128)


class _CompleteAio(Protocol):
    async def aio(
        self,
        prompt: str,
        *,
        max_tokens: int = 512,
        temperature: float = 0.2,
        model_id: str | None = None,
    ) -> str: ...


class _RemoteComplete(Protocol):
    @property
    def remote(self) -> _CompleteAio: ...


class _WarmMethod(Protocol):
    def spawn(self, model_id: str | None = None) -> object: ...


class _StreamMethod(Protocol):
    def remote_gen(
        self,
        prompt: str,
        *,
        max_tokens: int = 512,
        temperature: float = 0.2,
        model_id: str | None = None,
    ) -> Iterator[str]: ...


class LlmAsgiService(Protocol):
    """Duck-typed Modal ``LlmService`` surface used by ASGI routes."""

    @property
    def warm_model(self) -> _WarmMethod: ...

    @property
    def complete(self) -> _RemoteComplete: ...

    @property
    def stream_tokens(self) -> _StreamMethod: ...


@dataclass(frozen=True, slots=True)
class AsgiRouteDeps:
    """CPU-side helpers injected from ``llm_app`` (keeps this module GPU-free)."""

    health_payload: Callable[[], dict[str, str | None]]
    list_models_payload: Callable[[], dict[str, object]]
    resolve_hf_repo: Callable[[str], object]
    register_pending_model: Callable[[str], None]
    spawn_pull_job: Callable[[str, str], None]
    default_model_id: str = _DEFAULT_MODEL_ID


def _authorized(request: Request) -> bool:
    expected = os.environ.get(_PROXY_ENV)
    if not expected:
        return False
    return request.headers.get(_PROXY_HEADER) == expected


def build_prod_asgi_app(service: LlmAsgiService, deps: AsgiRouteDeps) -> Starlette:
    """Build the prod Starlette app (CPU ingress only — no GPU imports)."""

    async def health(_: Request) -> JSONResponse:
        return JSONResponse(deps.health_payload())

    async def warm(request: Request) -> JSONResponse:
        """Fire-and-forget GPU warm (EV-318 / #318) — mirror embedding ``.spawn()``."""
        if not _authorized(request):
            return JSONResponse({"detail": "Unauthorized"}, status_code=HTTPStatus.UNAUTHORIZED)
        raw = await request.body()
        try:
            payload = WarmRequest.model_validate(json.loads(raw)) if raw else WarmRequest()
        except (json.JSONDecodeError, ValidationError) as exc:
            return JSONResponse({"detail": str(exc)}, status_code=HTTPStatus.UNPROCESSABLE_ENTITY)
        model_id = payload.model_id or deps.default_model_id
        logger.info(
            "prewarm_spawned cold_kind=warm event=prewarm_to_ready model_id=%s",
            model_id,
        )
        _ = service.warm_model.spawn(payload.model_id)
        return JSONResponse({"status": "warming", "model_id": model_id})

    async def list_models(request: Request) -> JSONResponse:
        if not _authorized(request):
            return JSONResponse({"detail": "Unauthorized"}, status_code=HTTPStatus.UNAUTHORIZED)
        return JSONResponse(deps.list_models_payload())

    async def pull_model(request: Request) -> JSONResponse:
        if not _authorized(request):
            return JSONResponse({"detail": "Unauthorized"}, status_code=HTTPStatus.UNAUTHORIZED)
        try:
            payload = PullRequest.model_validate(json.loads(await request.body()))
        except (json.JSONDecodeError, ValidationError) as exc:
            return JSONResponse({"detail": str(exc)}, status_code=HTTPStatus.UNPROCESSABLE_ENTITY)
        try:
            _ = deps.resolve_hf_repo(payload.model_id)
        except ValueError as exc:
            return JSONResponse({"detail": str(exc)}, status_code=HTTPStatus.BAD_REQUEST)
        job_id = str(uuid.uuid4())
        deps.spawn_pull_job(job_id, payload.model_id)
        deps.register_pending_model(payload.model_id)
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
            text = await service.complete.remote.aio(
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

        def event_stream() -> Iterator[str]:
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
