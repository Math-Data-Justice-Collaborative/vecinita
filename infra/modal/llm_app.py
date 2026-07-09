"""Modal app: vecinita-llm — unified vLLM inference + HF model staging (ADR-009, ADR-037).

Deploy: modal deploy infra/modal/llm_app.py
Stage default weights: modal run infra/modal/llm_app.py::stage_llm_weights
Stage playground default tag: modal run infra/modal/llm_app.py::stage_default_model

Requires Modal secret ``vecinita-llm`` with ``VECINITA_MODAL_PROXY_KEY`` — must match DO
internal-write-api proxy key (``scripts/deploy/sync_llm_secret.sh``).

``vecinita-ollama`` is deprecated (ADR-037); all routes live on this app.
"""

from __future__ import annotations

import json
import logging
import os
import uuid
from http import HTTPStatus
from pathlib import Path
from typing import TYPE_CHECKING, Final

import modal
from infra.modal.llm_model_registry import (
    normalize_ollama_tag,
    repo_dir_name,
    resolve_hf_repo,
)
from pydantic import BaseModel, ConfigDict, Field, ValidationError

if TYPE_CHECKING:
    from starlette.requests import Request

logger = logging.getLogger("vecinita.llm")


def _resolve_repo_root() -> Path:
    """Repo root when building from infra/modal; /root when Modal mounts llm_app.py."""
    here = Path(__file__).resolve()
    if here.parent.name == "modal" and here.parent.parent.name == "infra":
        return here.parents[2]
    return Path("/root")


_REPO_ROOT = _resolve_repo_root()


APP_NAME = "vecinita-llm"
VOLUME_NAME = "llm-models"
MODEL_ID = "Qwen/Qwen2.5-1.5B-Instruct"
DEFAULT_PLAYGROUND_MODEL_ID: Final[str] = "qwen2.5:1.5b-instruct"
ENFORCE_EAGER_ENV = "VECINITA_LLM_ENFORCE_EAGER"
_PROXY_HEADER: Final[str] = "X-Vecinita-Proxy-Key"
_PROXY_ENV: Final[str] = "VECINITA_MODAL_PROXY_KEY"
_MANIFEST_PATH = Path("/models/manifest.json")
_REPOS_ROOT = Path("/models/repos")


class PullRequest(BaseModel):
    """POST /models/ollama/pull body (API compat — HF download, not ollama pull)."""

    model_config = ConfigDict(extra="forbid")
    model_id: str = Field(min_length=1, max_length=128)


class WarmRequest(BaseModel):
    """POST /warm body — optional model tag to preload."""

    model_config = ConfigDict(extra="forbid")
    model_id: str | None = None


class GenerateRequest(BaseModel):
    """POST /generate and /generate/stream body."""

    model_config = ConfigDict(extra="forbid")
    prompt: str = Field(min_length=1)
    max_tokens: int = Field(default=512, ge=1, le=2048)
    temperature: float = Field(default=0.2, ge=0.0, le=2.0)
    model_id: str | None = Field(default=None, max_length=128)


def _authorized(request: Request) -> bool:
    """Return True when the request carries the shared proxy key header."""
    expected = os.environ.get(_PROXY_ENV)
    if not expected:
        return False
    return request.headers.get(_PROXY_HEADER) == expected


def _enforce_eager_from_env() -> bool:
    """S001 T7 A/B: toggle CUDA graph capture for snapshot cold-start experiments."""
    raw = os.environ.get(ENFORCE_EAGER_ENV, "true").strip().lower()
    return raw not in ("0", "false", "no", "off")


LLM_MAX_MODEL_LEN: Final[int] = 2048


def max_model_len_for(model: str) -> int:
    """Context window sized for T4 VRAM; golden-eval RAG prompts can exceed 1.5k tokens."""
    _ = model  # reserved for per-model tuning (AWQ vs fp16)
    return LLM_MAX_MODEL_LEN


def _llm_engine_kwargs(*, max_model_len: int, model: str) -> dict[str, object]:
    """VLLM init for Tesla T4 (cc 7.5): fp16 or AWQ on T4."""
    kwargs: dict[str, object] = {
        "model": model,
        "trust_remote_code": True,
        "max_model_len": max_model_len,
        "dtype": "half",
        "hf_overrides": {"torch_dtype": "float16"},
        "gpu_memory_utilization": 0.9,
        "enforce_eager": _enforce_eager_from_env(),
        "enable_sleep_mode": True,
    }
    if "AWQ" in model.upper() or model.endswith("-awq"):
        kwargs["quantization"] = "awq"
        kwargs.pop("dtype", None)
        kwargs.pop("hf_overrides", None)
    if not model.startswith("/"):
        kwargs["download_dir"] = "/models"
    return kwargs


def _dist_is_initialized() -> bool:
    import torch.distributed as dist

    return dist.is_initialized()


def _dist_destroy_process_group() -> None:
    import torch.distributed as dist

    dist.destroy_process_group()


def _shutdown_vllm_engine(llm: object | None) -> None:
    """Tear down vLLM and NCCL before Modal container exit (BUG-2026-05-20)."""
    if llm is not None:
        try:
            engine = getattr(llm, "llm_engine", None)
            if engine is not None:
                shutdown = getattr(engine, "shutdown", None)
                if callable(shutdown):
                    shutdown()
        except Exception:
            pass
        del llm
    try:
        if _dist_is_initialized():
            _dist_destroy_process_group()
    except Exception:
        pass


def _read_manifest() -> dict[str, object]:
    if not _MANIFEST_PATH.exists():
        return {"models": [{"model_id": DEFAULT_PLAYGROUND_MODEL_ID, "available": False}]}
    with _MANIFEST_PATH.open(encoding="utf-8") as handle:
        payload = json.load(handle)
    if isinstance(payload, dict):
        return payload
    return {"models": [{"model_id": DEFAULT_PLAYGROUND_MODEL_ID, "available": False}]}


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
        available = bool(entry.get("available", False))
        items.append({"model_id": model_id, "available": available})
    if not items:
        items = [{"model_id": DEFAULT_PLAYGROUND_MODEL_ID, "available": False}]
    return {"items": items}


def _register_pending_model(model_id: str) -> None:
    manifest = _read_manifest()
    models_raw = manifest.get("models")
    models: list[dict[str, object]] = (
        [entry for entry in models_raw if isinstance(entry, dict)]
        if isinstance(models_raw, list)
        else []
    )
    if not any(entry.get("model_id") == model_id for entry in models):
        models.append({"model_id": model_id, "available": False})
        _write_manifest(models)


def _mark_model_available(model_id: str) -> None:
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


def _local_repo_path(model_id: str) -> Path:
    return _REPOS_ROOT / repo_dir_name(model_id)


def _resolve_vllm_model_arg(model_id: str | None) -> str:
    """Resolve playground tag or None to a vLLM ``model`` argument."""
    if model_id is None or normalize_ollama_tag(model_id) == normalize_ollama_tag(
        DEFAULT_PLAYGROUND_MODEL_ID
    ):
        return MODEL_ID
    local = _local_repo_path(model_id)
    if local.is_dir() and any(local.iterdir()):
        return str(local)
    return resolve_hf_repo(model_id)


def _download_hf_model(model_id: str) -> Path:
    """Download a HuggingFace repo for ``model_id`` into the volume."""
    from huggingface_hub import snapshot_download

    hf_repo = resolve_hf_repo(model_id)
    dest = _local_repo_path(model_id)
    dest.mkdir(parents=True, exist_ok=True)
    snapshot_download(repo_id=hf_repo, local_dir=str(dest))
    return dest


app = modal.App(APP_NAME)
model_volume = modal.Volume.from_name(VOLUME_NAME, create_if_missing=True)
pull_jobs = modal.Dict.from_name("vecinita-llm-pull-jobs", create_if_missing=True)

_LLM_ASGI_SECRETS = [modal.Secret.from_name("vecinita-llm")]

image = (
    modal.Image.debian_slim(python_version="3.11")
    .pip_install(
        "pydantic>=2.7,<3",
        "starlette>=0.37,<1",
        "transformers==4.51.3",
        "huggingface-hub>=0.23,<1",
        "vllm>=0.8.5,<0.9",
    )
    .env(
        {
            "TORCHINDUCTOR_COMPILE_THREADS": "1",
            "XFORMERS_ENABLE_TRITON": "1",
            "PYTHONPATH": "/root",
        }
    )
    .add_local_dir(_REPO_ROOT / "infra", remote_path="/root/infra")
)


with image.imports():
    from vllm import LLM, SamplingParams


@app.function(
    image=image,
    gpu="T4",
    volumes={"/models": model_volume},
    timeout=3600,
)
def stage_llm_weights() -> str:
    """One-shot: download Qwen weights into the llm-models volume (loads vLLM once)."""
    llm = LLM(**_llm_engine_kwargs(max_model_len=512, model=MODEL_ID))
    try:
        params = SamplingParams(max_tokens=1)
        llm.generate(["warmup"], params)
        _write_manifest([{"model_id": DEFAULT_PLAYGROUND_MODEL_ID, "available": True}])
        model_volume.commit()
        return f"staged {MODEL_ID}"
    finally:
        _shutdown_vllm_engine(llm)


@app.function(
    image=image,
    volumes={"/models": model_volume},
    timeout=3600,
)
def stage_default_model() -> str:
    """One-shot: stage the default playground model tag (ADR-037; replaces ollama_app)."""
    _download_hf_model(DEFAULT_PLAYGROUND_MODEL_ID)
    _mark_model_available(DEFAULT_PLAYGROUND_MODEL_ID)
    return f"staged {DEFAULT_PLAYGROUND_MODEL_ID}"


@app.function(
    image=image,
    volumes={"/models": model_volume},
    timeout=3600,
)
def pull_model_job(job_id: str, model_id: str) -> str:
    """Background HF download for a playground model tag (replaces vecinita-ollama pull)."""
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
    volumes={"/models": model_volume},
    scaledown_window=300,
    timeout=900,
    # ADR-037: model_id switching requires clean vLLM init — GPU snapshot breaks NCCL on reload.
    enable_memory_snapshot=False,
)
class LlmService:
    @modal.enter()
    def load_model(self) -> None:
        """Lazy-load vLLM on first request (supports default + playground tag switches)."""
        self._llm = None
        self._loaded_model_arg = None

    @modal.exit()
    def unload_model(self) -> None:
        _shutdown_vllm_engine(getattr(self, "_llm", None))
        self._llm = None
        self._loaded_model_arg = None

    def _ensure_model_loaded(self, model_id: str | None) -> None:
        resolved = _resolve_vllm_model_arg(model_id)
        if getattr(self, "_loaded_model_arg", None) == resolved and self._llm is not None:
            return
        _shutdown_vllm_engine(getattr(self, "_llm", None))
        self._llm = None
        self._loaded_model_arg = None
        import gc

        gc.collect()
        try:
            import torch

            if torch.cuda.is_available():
                torch.cuda.empty_cache()
                torch.cuda.synchronize()
        except Exception:
            pass
        self._llm = LLM(
            **_llm_engine_kwargs(max_model_len=max_model_len_for(resolved), model=resolved)
        )
        self._loaded_model_arg = resolved
        self._llm.generate(["warmup"], SamplingParams(max_tokens=1))

    def _generate_text(
        self,
        prompt: str,
        *,
        max_tokens: int = 512,
        temperature: float = 0.2,
        model_id: str | None = None,
    ) -> str:
        self._ensure_model_loaded(model_id)
        params = SamplingParams(
            max_tokens=max_tokens,
            temperature=temperature,
            repetition_penalty=1.15,
        )
        if self._llm is None:
            msg = "LlmService model is not loaded"
            raise RuntimeError(msg)
        outputs = self._llm.generate([prompt], params)
        return outputs[0].outputs[0].text

    @modal.method()
    def complete(
        self,
        prompt: str,
        *,
        max_tokens: int = 512,
        temperature: float = 0.2,
        model_id: str | None = None,
    ) -> str:
        return self._generate_text(
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
        text = self._generate_text(
            prompt,
            max_tokens=max_tokens,
            temperature=temperature,
            model_id=model_id,
        )
        for piece in text.split():
            yield piece + " "

    @modal.method()
    def warm_model(self, model_id: str | None = None) -> str:
        """Preload a model into VRAM (fold cold-start into warm-up window)."""
        self._ensure_model_loaded(model_id)
        return _resolve_vllm_model_arg(model_id)


@app.function(
    image=image,
    timeout=1200,
    secrets=_LLM_ASGI_SECRETS,
)
@modal.asgi_app()
def fastapi_app():
    """Starlette ASGI — health, generate, model list/pull (ADR-037 unified surface)."""
    from starlette.applications import Starlette
    from starlette.responses import JSONResponse, StreamingResponse
    from starlette.routing import Route

    service = LlmService()

    async def health(_: Request) -> JSONResponse:
        return JSONResponse({"status": "ok"})

    async def warm(request: Request) -> JSONResponse:
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
