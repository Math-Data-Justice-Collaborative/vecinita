"""Modal app: vecinita-data-management — ASGI /jobs + ingest worker.

Deploy from repo root:
  modal deploy infra/modal/data_management_app.py

Requires Modal secret `vecinita-data-management` with:
VECINITA_MODAL_EMBED_URL, VECINITA_INTERNAL_WRITE_URL, VECINITA_INTERNAL_API_KEY
"""

from __future__ import annotations

from pathlib import Path

import modal

APP_NAME = "vecinita-data-management"
_REPO_ROOT = Path(__file__).resolve().parents[2]

app = modal.App(APP_NAME)

_PKG_ROOT = "/opt/vecinita"
_PYTHONPATH = ":".join(
    [
        f"{_PKG_ROOT}/packages/ingest",
        f"{_PKG_ROOT}/packages/embedding-client",
        f"{_PKG_ROOT}/packages/shared-schemas",
        f"{_PKG_ROOT}/apps/data-management-backend",
    ]
)

image = (
    modal.Image.debian_slim(python_version="3.11")
    .pip_install(
        "fastapi>=0.115,<1",
        "httpx>=0.27,<1",
        "pydantic>=2.7,<3",
    )
    .env({"PYTHONPATH": _PYTHONPATH})
    .add_local_dir(_REPO_ROOT / "packages" / "ingest", remote_path=f"{_PKG_ROOT}/packages/ingest")
    .add_local_dir(
        _REPO_ROOT / "packages" / "embedding-client",
        remote_path=f"{_PKG_ROOT}/packages/embedding-client",
    )
    .add_local_dir(
        _REPO_ROOT / "packages" / "shared-schemas",
        remote_path=f"{_PKG_ROOT}/packages/shared-schemas",
    )
    .add_local_dir(
        _REPO_ROOT / "apps" / "data-management-backend",
        remote_path=f"{_PKG_ROOT}/apps/data-management-backend",
    )
)


@app.function(
    image=image,
    secrets=[modal.Secret.from_name("vecinita-data-management")],
    timeout=600,
)
@modal.asgi_app(requires_proxy_auth=True)
def fastapi_app():
    from uuid import UUID

    from vecinita_data_management_backend.app import create_app
    from vecinita_data_management_backend.pipeline import run_ingest_job
    from vecinita_data_management_backend.store import InMemoryJobStore
    from vecinita_data_management_backend.write_client import InternalWriteClient
    from vecinita_embedding_client import EmbeddingClient

    store = InMemoryJobStore()
    embed = EmbeddingClient()
    write = InternalWriteClient()

    def runner(job_id: UUID) -> None:
        run_ingest_job(
            job_id,
            store=store,
            embed_client=embed,
            write_client=write,
        )

    return create_app(store=store, pipeline_runner=runner)
