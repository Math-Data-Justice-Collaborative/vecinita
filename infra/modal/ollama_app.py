"""Modal app: vecinita-ollama — Ollama model list + pull on vecinita-models volume (ADR-035).

Deploy: modal deploy infra/modal/ollama_app.py
Stage default model: modal run infra/modal/ollama_app.py::stage_default_model

Requires Modal secret `vecinita-ollama` with:
VECINITA_MODAL_PROXY_KEY — must match DO internal-write-api proxy key.
See infra/modal/.env.example and docs/staging-secrets-matrix.md.
"""

from __future__ import annotations

import json
import logging
import os
import subprocess
import uuid
from http import HTTPStatus
from pathlib import Path
from typing import Final

import modal

logger = logging.getLogger("vecinita.ollama")

APP_NAME = "vecinita-ollama"
VOLUME_NAME = "vecinita-models"
DEFAULT_MODEL_ID: Final[str] = "qwen2.5:1.5b-instruct"
_PROXY_HEADER: Final[str] = "X-Vecinita-Proxy-Key"
_PROXY_ENV: Final[str] = "VECINITA_MODAL_PROXY_KEY"
_MANIFEST_PATH = Path("/models/manifest.json")
_OLLAMA_BIN: Final[str] = "/usr/local/bin/ollama"

app = modal.App(APP_NAME)
model_volume = modal.Volume.from_name(VOLUME_NAME, create_if_missing=True)
pull_jobs = modal.Dict.from_name("vecinita-ollama-pull-jobs", create_if_missing=True)

image = (
    modal.Image.debian_slim(python_version="3.11")
    .apt_install("curl", "ca-certificates")
    .run_commands("curl -fsSL https://ollama.com/install.sh | sh")
    .pip_install("pydantic>=2.7,<3", "starlette>=0.37,<1")
    .env({"OLLAMA_MODELS": "/models"})
)


def _read_manifest() -> dict[str, object]:
    if not _MANIFEST_PATH.exists():
        return {"models": [{"model_id": DEFAULT_MODEL_ID, "available": True}]}
    with _MANIFEST_PATH.open(encoding="utf-8") as handle:
        payload = json.load(handle)
    if isinstance(payload, dict):
        return payload
    return {"models": [{"model_id": DEFAULT_MODEL_ID, "available": True}]}


def _write_manifest(models: list[dict[str, object]]) -> None:
    _MANIFEST_PATH.parent.mkdir(parents=True, exist_ok=True)
    with _MANIFEST_PATH.open("w", encoding="utf-8") as handle:
        json.dump({"models": models}, handle)
    model_volume.commit()


def _list_models_payload() -> dict[str, object]:
    manifest = _read_manifest()
    models_raw = manifest.get("models")
    if not isinstance(models_raw, list):
        models_raw = []
    items: list[dict[str, object]] = []
    for entry in models_raw:
        if not isinstance(entry, dict):
            continue
        model_id = entry.get("model_id")
        if not isinstance(model_id, str):
            continue
        available = bool(entry.get("available", True))
        items.append({"model_id": model_id, "available": available})
    if not items:
        items = [{"model_id": DEFAULT_MODEL_ID, "available": True}]
    return {"items": items}


def _run_ollama_pull(model_id: str) -> None:
    subprocess.run(  # noqa: S603
        [_OLLAMA_BIN, "pull", model_id],
        check=True,
        env=os.environ.copy(),
    )


@app.function(
    image=image,
    volumes={"/models": model_volume},
    timeout=3600,
)
def stage_default_model() -> str:
    """One-shot: pull the default playground model into vecinita-models."""
    _run_ollama_pull(DEFAULT_MODEL_ID)
    _write_manifest([{"model_id": DEFAULT_MODEL_ID, "available": True}])
    return f"staged {DEFAULT_MODEL_ID}"


@app.function(
    image=image,
    volumes={"/models": model_volume},
    timeout=3600,
)
def pull_model_job(job_id: str, model_id: str) -> str:
    """Background pull for a missing Ollama tag (RD-141)."""
    pull_jobs[job_id] = {"model_id": model_id, "status": "pulling"}
    try:
        _run_ollama_pull(model_id)
    except subprocess.CalledProcessError as exc:
        pull_jobs[job_id] = {"model_id": model_id, "status": "failed", "error": str(exc)}
        raise
    else:
        manifest = _read_manifest()
        models_raw = manifest.get("models")
        models: list[dict[str, object]] = (
            [entry for entry in models_raw if isinstance(entry, dict)]
            if isinstance(models_raw, list)
            else []
        )
        updated = False
        for entry in models:
            if entry.get("model_id") == model_id:
                entry["available"] = True
                updated = True
        if not updated:
            models.append({"model_id": model_id, "available": True})
        _write_manifest(models)
        pull_jobs[job_id] = {"model_id": model_id, "status": "available"}
        return model_id


@app.function(image=image, volumes={"/models": model_volume}, timeout=120)
@modal.asgi_app()
def ollama_api():
    from pydantic import BaseModel, ConfigDict, Field, ValidationError
    from starlette.applications import Starlette
    from starlette.requests import Request
    from starlette.responses import JSONResponse
    from starlette.routing import Route

    class PullRequest(BaseModel):
        model_config = ConfigDict(extra="forbid")
        model_id: str = Field(min_length=1, max_length=128)

    def _authorized(request: Request) -> bool:
        expected = os.environ.get(_PROXY_ENV)
        if not expected:
            return False
        return request.headers.get(_PROXY_HEADER) == expected

    async def health(_: Request) -> JSONResponse:
        return JSONResponse({"status": "ok"})

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
        job_id = str(uuid.uuid4())
        pull_model_job.spawn(job_id, payload.model_id)
        manifest = _read_manifest()
        models_raw = manifest.get("models")
        models: list[dict[str, object]] = (
            [entry for entry in models_raw if isinstance(entry, dict)]
            if isinstance(models_raw, list)
            else []
        )
        if not any(entry.get("model_id") == payload.model_id for entry in models):
            models.append({"model_id": payload.model_id, "available": False})
            _write_manifest(models)
        return JSONResponse(
            {
                "job_id": job_id,
                "model_id": payload.model_id,
                "status": "pulling",
            },
            status_code=HTTPStatus.ACCEPTED,
        )

    return Starlette(
        routes=[
            Route("/health", health, methods=["GET"]),
            Route("/models/ollama", list_models, methods=["GET"]),
            Route("/models/ollama/pull", pull_model, methods=["POST"]),
        ]
    )
