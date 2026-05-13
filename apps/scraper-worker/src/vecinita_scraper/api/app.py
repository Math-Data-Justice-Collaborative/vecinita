"""Modal app for serving the FastAPI REST API."""

from __future__ import annotations

from vecinita_scraper.api.server import create_app
from vecinita_scraper.core.logger import get_logger

logger = get_logger(__name__)

try:
    import modal
except ImportError as exc:  # pragma: no cover
    raise ImportError(
        "modal is required to serve the API. Install with: pip install modal"
    ) from exc

# Create Modal app for the API
app = modal.App(name="vecinita-scraper-api")
APP_SECRETS = [modal.Secret.from_name("vecinita-scraper-env")]

image = (
    modal.Image.debian_slim()
    .pip_install(
        "fastapi>=0.100",
        "uvicorn>=0.23.0",
        "httpx>=0.25.0",
        "psycopg2-binary>=2.9.9",
        "pydantic>=2.0",
        "python-dotenv>=1.0",
        "structlog>=23.0",
    )
    .add_local_python_source("vecinita_scraper")
)


# Serve the FastAPI app via Modal ASGI endpoint
@app.function(image=image, secrets=APP_SECRETS)
@modal.asgi_app()
def fastapi() -> object:
    """ASGI entrypoint for Modal to serve the FastAPI scraper API."""
    return create_app()


if __name__ == "__main__":
    # Local entrypoint for testing
    logger.info("Starting FastAPI app on Modal")
