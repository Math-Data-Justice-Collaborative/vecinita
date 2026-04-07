"""
Modal deployment wrapper for Vecinita Embedding Service
Wraps the embedding service for Modal serverless deployment
"""

from pathlib import Path

import modal

# Create Modal app
app = modal.App("vecinita-embedding")

# Define image with dependencies
image = modal.Image.debian_slim().pip_install(
    "fastapi>=0.104.0",
    "uvicorn>=0.24.0",
    "sentence-transformers>=5.1.2",
    "numpy>=1.24.0",
    "pydantic>=2.0.0",
)


@app.function(
    image=image,
    secrets=[modal.Secret.from_name("vecinita-secrets")],
    cpu=1.0,
    memory=512,
    timeout=3600,
)
async def embedding_service():
    """Run embedding service on Modal"""
    import subprocess
    import sys

    # Run FastAPI with uvicorn
    subprocess.run(
        [
            sys.executable,
            "-m",
            "uvicorn",
            "src.services.embedding.server:app",
            "--host",
            "0.0.0.0",
            "--port",
            "8001",
        ],
        cwd="/app",
    )


# Mount source code
app_path = Path(__file__).parent.parent
app.function(image=image)(  # type: ignore[call-overload]
    embedding_service,
).__wrapped__.mounts = [
    modal.Mount.from_local_dir(
        app_path / "src" / "embedding_service",
        remote_path="/app/src/embedding_service",
    ),
    modal.Mount.from_local_dir(
        app_path / "src" / "agent",
        remote_path="/app/src/agent",
    ),
]


# Health check
@app.function(image=image)
def health():
    """Health check for monitoring"""
    return {"status": "healthy", "service": "embedding"}


# Web endpoint
@app.function(image=image)
@modal.asgi_app(requires_service_auth=False)
def web():
    """Web endpoint for modal.web"""
    from fastapi import FastAPI

    _app = FastAPI()

    @_app.get("/health")
    async def health_check():
        return {"status": "healthy"}

    return _app
