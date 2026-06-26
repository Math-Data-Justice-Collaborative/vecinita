"""Modal app: vecinita-llm — vLLM Qwen2.5-1.5B-Instruct on T4 (ADR-009).

Deploy: modal deploy infra/modal/llm_app.py
Stage weights: modal run infra/modal/llm_app.py::stage_llm_weights
"""

from __future__ import annotations

import json
import logging
import time

import modal

logger = logging.getLogger("vecinita.llm")

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
        # Skip CUDA graph capture at startup — removes seconds of cold-start init
        # for a small model on T4 (S001 Tier-0, ADR-022 budget-safe combo).
        "enforce_eager": True,
        # Required for sleep(level=1) / wake_up() snapshot prep (S001 T5, vLLM 0.7+).
        "enable_sleep_mode": True,
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
        "vllm>=0.7,<0.8",
    )
    .env(
        {
            # vLLM + GPU snapshot mitigations (S001 T4, ADR-022).
            "TORCHINDUCTOR_COMPILE_THREADS": "1",
            "XFORMERS_ENABLE_TRITON": "1",
        }
    )
)

# Import vLLM in global image scope so library init lands in the GPU memory
# snapshot instead of every cold boot (S001 T4; split enter in T5).
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
    enable_memory_snapshot=True,
    experimental_options={"enable_gpu_snapshot": True},
)
class LlmService:
    @modal.enter(snap=True)
    def load_model(self) -> None:
        # S001 P1 cold-start instrumentation: vLLM import is in image.imports()
        # (T4) so import_s is ~0 on restore; construct_s still captures engine
        # init + weight load. For the weight-load split, read vLLM's
        # "Loading weights took ..." line in the same container log.
        t_enter = time.perf_counter()
        import_s = 0.0

        t1 = time.perf_counter()
        self._llm = LLM(**_llm_engine_kwargs(max_model_len=1024))
        construct_s = time.perf_counter() - t1

        # Warm-up forward pass: fold first-token init into startup and give a
        # measurable t4 (Modal docs recommend warming up before serving).
        t2 = time.perf_counter()
        self._llm.generate(["warmup"], SamplingParams(max_tokens=1))
        warmup_s = time.perf_counter() - t2

        # Discard KV cache before GPU snapshot (Modal vLLM pattern, S001 T5).
        self._llm.sleep(level=1)

        logger.warning(
            "cold_start_breakdown import_s=%.2f construct_s=%.2f warmup_s=%.2f "
            "total_enter_s=%.2f (construct_s includes vLLM engine init + weight load; "
            "see vLLM 'Loading weights took' log for the split)",
            import_s,
            construct_s,
            warmup_s,
            time.perf_counter() - t_enter,
        )

    @modal.enter(snap=False)
    def restore_model(self) -> None:
        """Recreate KV cache after snapshot restore (S001 T5)."""
        self._llm.wake_up()

    @modal.exit()
    def unload_model(self) -> None:
        _shutdown_vllm_engine(getattr(self, "_llm", None))
        self._llm = None

    def _generate_text(
        self, prompt: str, *, max_tokens: int = 512, temperature: float = 0.2
    ) -> str:
        """Shared vLLM generate path — do not call self.complete() from other methods."""
        params = SamplingParams(
            max_tokens=max_tokens,
            temperature=temperature,
            repetition_penalty=1.15,
        )
        outputs = self._llm.generate([prompt], params)
        return outputs[0].outputs[0].text

    @modal.method()
    def complete(self, prompt: str, *, max_tokens: int = 512, temperature: float = 0.2) -> str:
        return self._generate_text(prompt, max_tokens=max_tokens, temperature=temperature)

    @modal.method()
    def stream_tokens(self, prompt: str, *, max_tokens: int = 512, temperature: float = 0.2):
        text = self._generate_text(prompt, max_tokens=max_tokens, temperature=temperature)
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

    async def warm(_: Request) -> JSONResponse:
        """Boot LlmService (T4 GPU) during user think-time (S001 T11).

        `/health` only warms this ASGI web fn; pre-warm must invoke the GPU class.
        """
        service.complete.remote("warmup", max_tokens=1)
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
            Route("/warm", warm, methods=["POST"]),
            Route("/generate", generate, methods=["POST"]),
            Route("/generate/stream", generate_stream, methods=["POST"]),
        ]
    )
