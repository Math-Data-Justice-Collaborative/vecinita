"""Modal app: vecinita-llm — vLLM Qwen2.5-1.5B-Instruct on T4 (ADR-009).

Deploy: modal deploy infra/modal/llm_app.py
"""

from __future__ import annotations

import json

import modal

APP_NAME = "vecinita-llm"
VOLUME_NAME = "llm-models"
MODEL_ID = "Qwen/Qwen2.5-1.5B-Instruct"

app = modal.App(APP_NAME)
model_volume = modal.Volume.from_name(VOLUME_NAME, create_if_missing=True)

image = (
    modal.Image.debian_slim(python_version="3.11")
    .pip_install(
        "fastapi>=0.115,<1",
        "pydantic>=2.7,<3",
        "vllm>=0.6.3,<0.7",
    )
)


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

        self._llm = LLM(
            model=MODEL_ID,
            download_dir="/models",
            trust_remote_code=True,
            max_model_len=4096,
        )

    @modal.method()
    def complete(self, prompt: str, *, max_tokens: int = 512, temperature: float = 0.2) -> str:
        from vllm import SamplingParams

        params = SamplingParams(max_tokens=max_tokens, temperature=temperature)
        outputs = self._llm.generate([prompt], params)
        return outputs[0].outputs[0].text

    @modal.method()
    def stream_tokens(
        self, prompt: str, *, max_tokens: int = 512, temperature: float = 0.2
    ):
        text = self.complete(prompt, max_tokens=max_tokens, temperature=temperature)
        for piece in text.split():
            yield piece + " "


@app.function(image=image)
@modal.asgi_app()
def fastapi_app():
    from fastapi import FastAPI
    from fastapi.responses import StreamingResponse
    from pydantic import BaseModel, ConfigDict, Field

    class GenerateRequest(BaseModel):
        model_config = ConfigDict(extra="forbid")
        prompt: str = Field(..., min_length=1)
        max_tokens: int = Field(default=512, ge=1, le=2048)
        temperature: float = Field(default=0.2, ge=0.0, le=2.0)

    class GenerateResponse(BaseModel):
        text: str

    web = FastAPI(title="vecinita-llm", version="0.1.0")
    service = LlmService()

    @web.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @web.post("/generate", response_model=GenerateResponse)
    def generate(body: GenerateRequest) -> GenerateResponse:
        text = service.complete.remote(
            body.prompt,
            max_tokens=body.max_tokens,
            temperature=body.temperature,
        )
        return GenerateResponse(text=text)

    @web.post("/generate/stream")
    def generate_stream(body: GenerateRequest) -> StreamingResponse:
        def event_stream():
            for token in service.stream_tokens.remote_gen(
                body.prompt,
                max_tokens=body.max_tokens,
                temperature=body.temperature,
            ):
                yield f"data: {json.dumps({'token': token})}\n\n"
            yield f"data: {json.dumps({'done': True})}\n\n"

        return StreamingResponse(event_stream(), media_type="text/event-stream")

    return web
