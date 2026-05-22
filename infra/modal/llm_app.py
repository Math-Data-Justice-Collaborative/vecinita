"""Modal app: vecinita-llm — vLLM Qwen2.5-1.5B-Instruct on T4 (ADR-009).

Deploy: modal deploy infra/modal/llm_app.py
Stage weights: modal run infra/modal/llm_app.py::stage_llm_weights
"""

from __future__ import annotations

import json

import modal

APP_NAME = "vecinita-llm"
VOLUME_NAME = "llm-models"
MODEL_ID = "Qwen/Qwen2.5-1.5B-Instruct"


def _llm_engine_kwargs(*, max_model_len: int) -> dict[str, object]:
    """vLLM init for Tesla T4 (cc 7.5): fp16 only; avoid bf16 cast warning where possible."""
    return {
        "model": MODEL_ID,
        "download_dir": "/models",
        "trust_remote_code": True,
        "max_model_len": max_model_len,
        "dtype": "half",
        "hf_overrides": {"torch_dtype": "float16"},
        "gpu_memory_utilization": 0.9,
    }


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


app = modal.App(APP_NAME)
model_volume = modal.Volume.from_name(VOLUME_NAME, create_if_missing=True)

image = (
    modal.Image.debian_slim(python_version="3.11")
    .pip_install(
        "pydantic>=2.7,<3",
        "starlette>=0.37,<1",
        "transformers>=4.44,<4.47",
        "vllm>=0.6.3,<0.7",
    )
)


@app.function(
    image=image,
    gpu="T4",
    volumes={"/models": model_volume},
    timeout=3600,
)
def stage_llm_weights() -> str:
    """One-shot: download Qwen weights into the llm-models volume (loads vLLM once)."""
    from vllm import LLM, SamplingParams

    llm: LLM | None = None
    try:
        llm = LLM(**_llm_engine_kwargs(max_model_len=512))
        params = SamplingParams(max_tokens=1)
        llm.generate(["warmup"], params)
        model_volume.commit()
        return f"staged {MODEL_ID}"
    finally:
        _shutdown_vllm_engine(llm)


@app.cls(
    image=image,
    gpu="T4",
    volumes={"/models": model_volume},
    scaledown_window=300,
    timeout=600,
)
class LlmService:
    @modal.enter()
    def load_model(self) -> None:
        from vllm import LLM

        self._llm = LLM(**_llm_engine_kwargs(max_model_len=1024))

    @modal.exit()
    def unload_model(self) -> None:
        _shutdown_vllm_engine(getattr(self, "_llm", None))
        self._llm = None

    def _generate_text(
        self, prompt: str, *, max_tokens: int = 512, temperature: float = 0.2
    ) -> str:
        """Shared vLLM generate path — do not call self.complete() from other methods."""
        from vllm import SamplingParams

        params = SamplingParams(
            max_tokens=max_tokens,
            temperature=temperature,
            repetition_penalty=1.15,
        )
        outputs = self._llm.generate([prompt], params)
        return outputs[0].outputs[0].text

    @modal.method()
    def complete(self, prompt: str, *, max_tokens: int = 512, temperature: float = 0.2) -> str:
        return self._generate_text(
            prompt, max_tokens=max_tokens, temperature=temperature
        )

    @modal.method()
    def stream_tokens(
        self, prompt: str, *, max_tokens: int = 512, temperature: float = 0.2
    ):
        text = self._generate_text(
            prompt, max_tokens=max_tokens, temperature=temperature
        )
        for piece in text.split():
            yield piece + " "


@app.function(image=image, timeout=1200)
@modal.asgi_app()
def fastapi_app():
    """Starlette ASGI (not FastAPI routes) — Modal expects JSON bodies via request.body()."""
    from pydantic import BaseModel, ConfigDict, Field, ValidationError
    from starlette.applications import Starlette
    from starlette.requests import Request
    from starlette.responses import JSONResponse, StreamingResponse
    from starlette.routing import Route

    class GenerateRequest(BaseModel):
        model_config = ConfigDict(extra="forbid")
        prompt: str = Field(..., min_length=1)
        max_tokens: int = Field(default=512, ge=1, le=2048)
        temperature: float = Field(default=0.2, ge=0.0, le=2.0)

    service = LlmService()

    async def health(_: Request) -> JSONResponse:
        return JSONResponse({"status": "ok"})

    async def generate(request: Request) -> JSONResponse:
        try:
            payload = GenerateRequest.model_validate(json.loads(await request.body()))
        except (json.JSONDecodeError, ValidationError) as exc:
            return JSONResponse({"detail": str(exc)}, status_code=422)
        text = service.complete.remote(
            payload.prompt,
            max_tokens=payload.max_tokens,
            temperature=payload.temperature,
        )
        return JSONResponse({"text": text})

    async def generate_stream(request: Request) -> StreamingResponse:
        try:
            payload = GenerateRequest.model_validate(json.loads(await request.body()))
        except (json.JSONDecodeError, ValidationError) as exc:
            return JSONResponse({"detail": str(exc)}, status_code=422)

        def event_stream():
            for token in service.stream_tokens.remote_gen(
                payload.prompt,
                max_tokens=payload.max_tokens,
                temperature=payload.temperature,
            ):
                yield f"data: {json.dumps({'token': token})}\n\n"
            yield f"data: {json.dumps({'done': True})}\n\n"

        return StreamingResponse(event_stream(), media_type="text/event-stream")

    return Starlette(
        routes=[
            Route("/health", health, methods=["GET"]),
            Route("/generate", generate, methods=["POST"]),
            Route("/generate/stream", generate_stream, methods=["POST"]),
        ]
    )
