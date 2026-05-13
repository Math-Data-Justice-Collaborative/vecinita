"""ASGI entry-point for local runtime (Docker or direct uvicorn)."""

from .api.routes import create_app

app = create_app()
