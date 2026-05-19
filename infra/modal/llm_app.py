"""Modal app: vecinita-llm — vLLM Qwen2.5-1.5B-Instruct on T4 (ADR-009).

Deploy: modal deploy infra/modal/llm_app.py
"""

from __future__ import annotations

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


@app.function(image=image)
@modal.asgi_app()
def fastapi_app():
    from fastapi import FastAPI

    web = FastAPI(title="vecinita-llm", version="0.1.0")

    @web.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    return web
