"""Modal deployment entrypoint for the embedding service."""

import os
import sys
from pathlib import Path

import modal

APP_NAME = os.getenv("MODAL_EMBEDDING_APP_NAME", "vecinita-embedding")
SECRET_NAME = os.getenv("MODAL_SECRET_NAME", "vecinita-secrets")
SRC_DIR = Path(__file__).resolve().parents[1]

app = modal.App(APP_NAME)

image = (
    modal.Image.debian_slim()
    .pip_install(
        "fastapi>=0.104.0",
        "uvicorn>=0.24.0",
        "python-dotenv>=1.0.0",
        "numpy>=1.24.0",
        "pydantic>=2.0.0",
        "fastembed>=0.6.0",
    )
    .env({"PYTHONPATH": "/root", "EMBEDDING_DISABLE_APP_AUTH": "true"})
    .add_local_dir(str(SRC_DIR), remote_path="/root/src")
)


@app.function(
    image=image,
    secrets=[modal.Secret.from_name(SECRET_NAME)],
    cpu=1.0,
    memory=2048,
    timeout=3600,
)
@modal.asgi_app(requires_proxy_auth=False)
def web_app():
    if "/root" not in sys.path:
        sys.path.insert(0, "/root")

    from src.embedding_service.main import app as fastapi_app

    return fastapi_app


@app.function(image=image)
def health() -> dict:
    return {"status": "ok", "service": "embedding"}
