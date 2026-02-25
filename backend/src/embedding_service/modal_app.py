"""Modal deployment entrypoint for the embedding service."""

from pathlib import Path
import os

import modal

APP_NAME = os.getenv("MODAL_EMBEDDING_APP_NAME", "vecinita-embedding")
SECRET_NAME = os.getenv("MODAL_SECRET_NAME", "vecinita-secrets")
SRC_DIR = Path(__file__).resolve().parents[1]

app = modal.App(APP_NAME)

image = modal.Image.debian_slim().pip_install(
	"fastapi>=0.104.0",
	"uvicorn>=0.24.0",
	"python-dotenv>=1.0.0",
	"numpy>=1.24.0",
	"pydantic>=2.0.0",
	"fastembed>=0.6.0",
)


@app.function(
	image=image,
	secrets=[modal.Secret.from_name(SECRET_NAME)],
	cpu=1.0,
	memory=2048,
	timeout=3600,
)
@modal.asgi_app()
def web_app():
	from src.embedding_service.main import app as fastapi_app

	return fastapi_app


@app.function(image=image)
def health() -> dict:
	return {"status": "ok", "service": "embedding"}
