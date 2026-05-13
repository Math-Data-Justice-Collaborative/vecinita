"""Modal App initialization with queues and shared infrastructure.

Scrape jobs use Modal's primary job-queue pattern: ``modal.Function.from_name`` + ``.spawn()`` /
``.spawn.aio()`` on ``scraper_worker`` (see ``job_control._dispatch_scrape_job_to_modal_worker``),
returning a ``FunctionCall`` id for ``FunctionCall.get()`` polling via
``GET /jobs/spawns/{call_id}``.
If spawn is unavailable, work falls back to the ``scrape-jobs`` Modal ``Queue`` and
``drain_scrape_queue``.

Downstream stages still use Modal ``Queue`` plus drain functions that resolve workers with
``from_name`` and ``spawn_map.aio`` (batch background execution; results in Postgres / next queues).
See https://modal.com/docs/guide/job-queue and
https://modal.com/docs/guide/batch-processing#background-execution-with-spawn_map
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

modal: Any
try:
    import modal as _modal

    modal = _modal
except ImportError:  # pragma: no cover - used only in local test environments without Modal

    class _DummyAsyncMethod:
        async def aio(self, *args: Any, **kwargs: Any) -> Any:
            return None

    class _DummyQueue:
        def __init__(self) -> None:
            self.put = _DummyAsyncMethod()
            self.get = _DummyAsyncMethod()

        @classmethod
        def from_name(cls, name: str, create_if_missing: bool = False) -> _DummyQueue:
            return cls()

    class _DummyImage:
        @staticmethod
        def debian_slim() -> _DummyImage:
            return _DummyImage()

        def pip_install(self, *packages: str) -> _DummyImage:
            return self

        def run_commands(self, *commands: str) -> _DummyImage:
            return self

        def add_local_python_source(self, *packages: str) -> _DummyImage:
            return self

    class _DummySecret:
        @staticmethod
        def from_name(name: str) -> str:
            return name

    class _DummyFunctionWrapper:
        def __init__(self, func: Callable[..., Any]) -> None:
            self._func = func
            self.spawn = _DummyAsyncMethod()

        def __call__(self, *args: Any, **kwargs: Any) -> Any:
            return self._func(*args, **kwargs)

    class _DummyApp:
        def __init__(self, name: str) -> None:
            self.name = name
            self.image = None

        def function(self, **kwargs: Any) -> Callable[[Callable[..., Any]], _DummyFunctionWrapper]:
            def decorator(func: Callable[..., Any]) -> _DummyFunctionWrapper:
                return _DummyFunctionWrapper(func)

            return decorator

    class _DummyModalModule:
        App = _DummyApp
        Image = _DummyImage
        Queue = _DummyQueue
        Secret = _DummySecret

        @staticmethod
        def batched(**kwargs: Any) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
            def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
                return func

            return decorator

    modal = _DummyModalModule()

# Create Modal app
app = modal.App(name="vecinita-scraper")
APP_SECRETS = [modal.Secret.from_name("vecinita-scraper-env")]

# Define image with dependencies
image = (
    modal.Image.debian_slim()
    .pip_install(
        "crawl4ai>=0.4.0",
        "docling>=0.4.0",
        "langchain>=0.1.0",
        "tiktoken>=0.5.0",
        "fastapi>=0.100",
        "uvicorn>=0.23.0",
        "httpx>=0.25.0",
        "psycopg2-binary>=2.9.9",
        "pydantic>=2.0",
        "python-dotenv>=1.0",
        "structlog>=23.0",
        "aiohttp>=3.8.0",
    )
    .run_commands("python -m playwright install --with-deps chromium")
    .add_local_python_source("vecinita_scraper")
)

# Create app with custom image
app.image = image

# Initialize queues for worker communication
# These queues are the backbone of the job processing pipeline

# Queue for initial scraping job submissions
scrape_jobs_queue = modal.Queue.from_name(
    "scrape-jobs",
    create_if_missing=True,
)

# Queue for document processing tasks
process_jobs_queue = modal.Queue.from_name(
    "process-jobs",
    create_if_missing=True,
)

# Queue for chunking tasks
chunk_jobs_queue = modal.Queue.from_name(
    "chunk-jobs",
    create_if_missing=True,
)

# Queue for embedding tasks
embed_jobs_queue = modal.Queue.from_name(
    "embed-jobs",
    create_if_missing=True,
)

# Queue for storage/finalization tasks
store_jobs_queue = modal.Queue.from_name(
    "store-jobs",
    create_if_missing=True,
)


@app.function(secrets=APP_SECRETS)
def health_check() -> dict[str, str]:
    """Health check endpoint for Modal workers."""
    return {"status": "ok", "worker": "vecinita-scraper"}


@app.function(image=image, secrets=APP_SECRETS, timeout=300)
def modal_scrape_job_submit(payload: dict[str, Any]) -> dict[str, Any]:
    """Create a scraping job (Postgres + scrape-jobs queue); for Modal RPC callers."""
    from vecinita_scraper.services.job_control import modal_job_submit

    return modal_job_submit(payload, jobs_queue=scrape_jobs_queue)


@app.function(image=image, secrets=APP_SECRETS, timeout=120)
def modal_scrape_job_get(job_id: str) -> dict[str, Any]:
    """Return job status JSON envelope for Modal RPC callers."""
    from vecinita_scraper.services.job_control import modal_job_get

    return modal_job_get(job_id)


@app.function(image=image, secrets=APP_SECRETS, timeout=120)
def modal_scrape_job_list(user_id: str | None = None, limit: int = 50) -> dict[str, Any]:
    """List jobs JSON envelope for Modal RPC callers."""
    from vecinita_scraper.services.job_control import modal_job_list

    return modal_job_list(user_id, limit)


@app.function(image=image, secrets=APP_SECRETS, timeout=120)
def modal_scrape_job_cancel(job_id: str) -> dict[str, Any]:
    """Cancel job JSON envelope for Modal RPC callers."""
    from vecinita_scraper.services.job_control import modal_job_cancel

    return modal_job_cancel(job_id)


def lookup_scraper_deployed_function(fn_tag: str) -> Any:
    """Return a hydrated Modal handle for a function deployed on this app (by tag).

    Use for any ``.spawn`` / ``.spawn.aio`` / ``.spawn_map.aio`` from another Modal function
    or from a different module import path. In-process ``worker_fn.spawn`` handles can be
    unhydrated inside containers and raise
    ``ExecutionError: ... App it is defined on is not running``.

    Tags match the Python names on ``@app.function`` entrypoints (e.g. ``scraper_worker``,
    ``drain_scrape_queue``). See https://modal.com/docs/guide/job-queue
    """
    import os

    app_name = (os.getenv("MODAL_SCRAPER_APP_NAME") or app.name or "").strip()
    if not app_name:
        raise RuntimeError(
            "Set MODAL_SCRAPER_APP_NAME or ensure modal.App has a name to spawn Modal functions."
        )

    env_name = (os.getenv("MODAL_ENVIRONMENT_NAME") or os.getenv("MODAL_ENV") or "").strip() or None
    if env_name:
        return modal.Function.from_name(app_name, fn_tag, environment_name=env_name)
    return modal.Function.from_name(app_name, fn_tag)


async def spawn_deployed_worker_map(fn_tag: str, payloads: list[Any]) -> None:
    """Submit many worker jobs without waiting for results (Modal ``spawn_map`` batch pattern).

    Batches are capped (``MODAL_PIPELINE_MAX_CONCURRENT_SPAWNS``) so a large drain does not
    overload Modal with a single enormous ``spawn_map`` (**US2** burst / bounded concurrency).
    """
    if not payloads:
        return
    from vecinita_scraper.workers.pipeline_spawn import (
        chunk_payloads_for_bounded_spawn,
        max_concurrent_worker_spawns,
    )

    fn = lookup_scraper_deployed_function(fn_tag)
    cap = max_concurrent_worker_spawns()
    for batch in chunk_payloads_for_bounded_spawn(payloads, cap):
        await fn.spawn_map.aio(batch)


@app.function(image=image, secrets=APP_SECRETS, timeout=60)
def trigger_reindex(
    clean: bool = False, stream: bool = True, verbose: bool = False
) -> dict[str, Any]:
    """Kick pipeline drainers so queued work continues (Modal-native reindex trigger).

    ``clean=True`` is not implemented here (no DB wipe); use the legacy backend
    Modal cron app if a full clean reindex is required.
    """
    import os

    _ = stream
    _ = verbose

    batch_raw = os.getenv("MODAL_REINDEX_DRAIN_BATCH", "25").strip()
    try:
        batch_size = max(1, min(500, int(batch_raw)))
    except ValueError:
        batch_size = 25

    # Modal function tags match the Python names on ``@app.function`` drain entrypoints.
    spawned: list[str] = []
    for fn_tag in (
        "drain_scrape_queue",
        "drain_process_queue",
        "drain_chunk_queue",
        "drain_embed_queue",
        "drain_store_queue",
    ):
        fn = lookup_scraper_deployed_function(fn_tag)
        fn.spawn(batch_size=batch_size)
        spawned.append(fn_tag)

    return {
        "status": "accepted",
        "mode": "modal-function",
        "clean": clean,
        "clean_applied": False,
        "stream": stream,
        "verbose": verbose,
        "spawned_drains": spawned,
        "batch_size": batch_size,
        "message": "Spawned pipeline drain functions to process queued scrape/embed/store work.",
    }


# Import worker modules after the shared app and queues are defined so Modal
# registers decorated functions during deployment.
from vecinita_scraper.workers import chunker as _chunker  # noqa: E402,F401
from vecinita_scraper.workers import embedder as _embedder  # noqa: E402,F401
from vecinita_scraper.workers import finalizer as _finalizer  # noqa: E402,F401
from vecinita_scraper.workers import processor as _processor  # noqa: E402,F401
from vecinita_scraper.workers import scraper as _scraper  # noqa: E402,F401

# Note: FastAPI app is served separately via Modal's web endpoint deployment.
# See src/vecinita_scraper/api/server.py for the REST API implementation.


if __name__ == "__main__":
    # Local entrypoint for testing
    result = health_check.remote()
    print(result)
