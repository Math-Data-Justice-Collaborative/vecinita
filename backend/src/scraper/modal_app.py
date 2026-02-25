"""Modal deployment entrypoint for weekly scraper reindex jobs."""

from pathlib import Path
import os

import modal

ROOT_DIR = Path(__file__).resolve().parents[3]
BACKEND_DIR = Path(__file__).resolve().parents[2]
SRC_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT_DIR / "data"

APP_NAME = os.getenv("MODAL_SCRAPER_APP_NAME", "vecinita-scraper")
SECRET_NAME = os.getenv("MODAL_SECRET_NAME", "vecinita-secrets")
REINDEX_CRON_SCHEDULE = os.getenv("REINDEX_CRON_SCHEDULE", "0 2 * * 0")

app = modal.App(APP_NAME)

image = (
    modal.Image.debian_slim()
    .pip_install_from_requirements(str(BACKEND_DIR / "requirements.txt"))
    .env({"PYTHONPATH": "/app", "TF_ENABLE_ONEDNN_OPTS": "0"})
)

_COMMON_FUNCTION_KWARGS = {
    "image": image,
    "secrets": [modal.Secret.from_name(SECRET_NAME)],
    "cpu": 2.0,
    "memory": 4096,
    "timeout": 3 * 60 * 60,
}


def _run_scraper_pipeline(clean: bool, stream: bool, verbose: bool) -> dict:
    import subprocess
    import sys
    import time

    cmd = [sys.executable, "-m", "src.scraper.cli", "--no-confirm"]
    if clean:
        cmd.append("--clean")
    if stream:
        cmd.append("--stream")
    if verbose:
        cmd.append("--verbose")

    started = time.time()
    result = subprocess.run(
        cmd,
        cwd="/app",
        capture_output=True,
        text=True,
        check=False,
    )
    duration_seconds = round(time.time() - started, 2)

    stdout_tail = "\n".join((result.stdout or "").splitlines()[-40:])
    stderr_tail = "\n".join((result.stderr or "").splitlines()[-40:])

    return {
        "status": "completed" if result.returncode == 0 else "failed",
        "return_code": result.returncode,
        "duration_seconds": duration_seconds,
        "command": cmd,
        "stdout_tail": stdout_tail,
        "stderr_tail": stderr_tail,
    }


@app.function(**_COMMON_FUNCTION_KWARGS)
def run_reindex(clean: bool = False, stream: bool = True, verbose: bool = False) -> dict:
    return _run_scraper_pipeline(clean=clean, stream=stream, verbose=verbose)


@app.function(
    schedule=modal.Cron(REINDEX_CRON_SCHEDULE),
    **_COMMON_FUNCTION_KWARGS,
)
def weekly_reindex() -> dict:
    clean = os.getenv("SCRAPER_REINDEX_CLEAN", "false").lower() in {"1", "true", "yes"}
    verbose = os.getenv("SCRAPER_REINDEX_VERBOSE", "false").lower() in {"1", "true", "yes"}
    return _run_scraper_pipeline(clean=clean, stream=True, verbose=verbose)


@app.function(**_COMMON_FUNCTION_KWARGS)
@modal.asgi_app()
def web_app():
    from fastapi import FastAPI, Header, HTTPException

    api = FastAPI(title="Vecinita Scraper Reindex Service", version="0.1.0")

    @api.get("/health")
    async def health():
        return {"status": "ok", "service": "scraper-reindex", "schedule": REINDEX_CRON_SCHEDULE}

    @api.post("/reindex")
    async def trigger_reindex(
        clean: bool = False,
        stream: bool = True,
        verbose: bool = False,
        x_reindex_token: str | None = Header(default=None),
    ):
        required_token = os.getenv("REINDEX_TRIGGER_TOKEN")
        if required_token and x_reindex_token != required_token:
            raise HTTPException(status_code=401, detail="Invalid reindex token")

        call = run_reindex.spawn(clean=clean, stream=stream, verbose=verbose)
        return {"status": "queued", "call_id": call.object_id}

    return api
