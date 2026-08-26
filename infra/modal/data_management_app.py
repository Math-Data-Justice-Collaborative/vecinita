"""Modal app: vecinita-data-management — ASGI /jobs + ingest worker.

Deploy from repo root:
  modal deploy infra/modal/data_management_app.py

Requires Modal secret `vecinita-data-management` with:
VECINITA_MODAL_EMBED_URL, VECINITA_INTERNAL_WRITE_URL, VECINITA_INTERNAL_API_KEY,
VECINITA_MODAL_PROXY_KEY, VECINITA_CORS_ORIGINS (admin frontend origin),
VECINITA_MODAL_LLM_URL (required for retag and LLM tagging at ingest),
SUPABASE_URL, VECINITA_AUTH_REQUIRED (EV-005 F34 admin JWT on /jobs*),
SUPABASE_SECRET_KEY (EV-006 F35 — Admin API for /admin/users*; ADR-030 / TP-S005-01).
See infra/modal/.env.example and docs/staging-secrets-matrix.md.
"""

from __future__ import annotations

import logging
import os
from typing import TYPE_CHECKING, cast

import modal
from infra.modal.repo_paths import resolve_repo_root

if TYPE_CHECKING:
    from collections.abc import MutableMapping

    from vecinita_data_management_backend.store import JobPayload

logger = logging.getLogger(__name__)

APP_NAME = "vecinita-data-management"


_REPO_ROOT = resolve_repo_root()

app = modal.App(APP_NAME)

_PKG_ROOT = "/opt/vecinita"
_PYTHONPATH = ":".join(
    [
        f"{_PKG_ROOT}/packages/ingest",
        f"{_PKG_ROOT}/packages/embedding-client",
        f"{_PKG_ROOT}/packages/llm-client",
        f"{_PKG_ROOT}/packages/tagging",
        f"{_PKG_ROOT}/packages/shared-schemas",
        f"{_PKG_ROOT}/apps/data-management-backend",
    ]
)

image = (
    modal.Image.debian_slim(python_version="3.11")
    .pip_install(
        "fastapi>=0.115,<1",
        "httpx>=0.27,<1",
        "huggingface-hub>=0.30,<1",
        "langdetect>=1.0.9",
        "pydantic>=2.7,<3",
        "PyJWT>=2.10,<3",
        "cryptography>=42,<45",
        "tokenizers>=0.21,<1",
        "trafilatura>=1.12,<3",
        "pypdf>=6.13.3",
        "playwright>=1.40,<2",
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
        _REPO_ROOT / "packages" / "llm-client",
        remote_path=f"{_PKG_ROOT}/packages/llm-client",
    )
    .add_local_dir(
        _REPO_ROOT / "packages" / "tagging",
        remote_path=f"{_PKG_ROOT}/packages/tagging",
    )
    .add_local_dir(
        _REPO_ROOT / "data" / "fixtures" / "tags",
        remote_path=f"{_PKG_ROOT}/data/fixtures/tags",
    )
    .add_local_dir(
        _REPO_ROOT / "apps" / "data-management-backend",
        remote_path=f"{_PKG_ROOT}/apps/data-management-backend",
    )
)


def _run_scheduled_catchup_tick() -> str:
    """F75 daily catch-up branch (job/CRUD enqueue residual; cron records tick)."""
    from vecinita_data_management_backend.schedule_catchup import (
        record_scheduled_catchup_tick,
    )
    from vecinita_data_management_backend.write_client import (
        InternalWriteClient,
        InternalWriteClientError,
    )

    try:
        write = InternalWriteClient()
    except InternalWriteClientError:
        logger.warning("catch-up tick: write client unavailable", exc_info=True)
        return "automation_catchup_tick"
    return record_scheduled_catchup_tick(write)


def _run_scheduled_freshness_tick() -> dict[str, object]:
    """F76 freshness branch — enqueue refresh for stale refresh-enabled sources."""
    from uuid import UUID

    from vecinita_data_management_backend.freshness_refresh import run_scheduled_freshness_tick
    from vecinita_data_management_backend.modal_jobs_client import ModalJobsEnqueueClient
    from vecinita_data_management_backend.write_client import InternalWriteClient
    from vecinita_shared_schemas.internal_write import DocumentSummary

    write = InternalWriteClient()
    jobs = ModalJobsEnqueueClient()

    def list_stale() -> list[DocumentSummary]:
        items: list[DocumentSummary] = []
        page = 1
        while True:
            listing = write.list_documents(page=page, page_size=100, stale=True)
            items.extend(listing.items)
            if page * listing.page_size >= listing.total or not listing.items:
                break
            page += 1
        return items

    def enqueue(document_id: UUID, *, force: bool = False) -> UUID:
        return jobs.enqueue_freshness_refresh(
            document_id,
            force=force,
            refresh_enabled=True,
            is_stale=True,
        )

    result = run_scheduled_freshness_tick(
        list_stale_documents=list_stale,
        enqueue_freshness=enqueue,
    )
    logger.info(
        "daily schedule tick: job_type=freshness_refresh enqueued=%s skipped=%s outcome=%s",
        result.get("enqueued"),
        result.get("skipped"),
        result.get("outcome"),
    )
    return result


@app.function(
    image=image,
    secrets=[modal.Secret.from_name("vecinita-data-management")],
    schedule=modal.Period(days=1),
    timeout=600,
)
def daily_corpus_automations() -> dict[str, object]:
    """Shared F75/F76 daily schedule (ADR-052 / TP2 / TC-264 / S030-D31 M2).

    Dispatches ``automation_catchup`` then ``freshness_refresh`` as distinct job types
    from one ``schedule=modal.Period(days=1)`` entry.
    """
    from vecinita_data_management_backend.schedule_dispatch import run_daily_dispatch

    return run_daily_dispatch(
        run_catchup=_run_scheduled_catchup_tick,
        run_freshness=_run_scheduled_freshness_tick,
    )


@app.function(
    image=image,
    secrets=[modal.Secret.from_name("vecinita-data-management")],
    timeout=600,
)
# Edge proxy auth blocks browser OPTIONS preflight (CORS); Modal-Key enforced in FastAPI.
@modal.asgi_app(requires_proxy_auth=False)
def fastapi_app():
    from uuid import UUID

    from vecinita_data_management_backend.app import create_app
    from vecinita_data_management_backend.jobs import run_job
    from vecinita_data_management_backend.store import DictJobStore
    from vecinita_data_management_backend.write_client import InternalWriteClient
    from vecinita_embedding_client import EmbeddingClient
    from vecinita_llm_client import LlmClient
    from vecinita_tagging.llm_client import LlmTagClient
    from vecinita_tagging.translate_client import LlmTranslateClient

    jobs_dict = modal.Dict.from_name("vecinita-data-management-jobs", create_if_missing=True)
    # modal.Dict is a MutableMapping at runtime but is not typed as one.
    store = DictJobStore(cast("MutableMapping[str, JobPayload]", jobs_dict))
    embed = EmbeddingClient()
    write = InternalWriteClient()
    tag_client: LlmTagClient | None = None
    translate_client: LlmTranslateClient | None = None
    try:
        llm = LlmClient()
        tag_client = LlmTagClient(llm)
        translate_client = LlmTranslateClient(llm)
    except Exception:
        logger.warning(
            "LlmTagClient init failed — retag/translate jobs will fail. "
            "Ensure VECINITA_MODAL_LLM_URL is set in Modal secret '%s'.",
            APP_NAME,
            exc_info=True,
        )
        tag_client = None
        translate_client = None

    # F77: approved finetune_train jobs call vecinita-llm-finetune::train_lora (T129.5).
    os.environ.setdefault("VECINITA_FINETUNE_USE_MODAL", "1")

    def runner(job_id: UUID) -> None:
        run_job(
            job_id,
            store=store,
            embed_client=embed,
            write_client=write,
            tag_client=tag_client,
            translate_client=translate_client,
        )

    return create_app(store=store, pipeline_runner=runner)
