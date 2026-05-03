"""Modal deployment entrypoint for scheduled / invoked reindex jobs.

HTTP scraping and job APIs are deployed from ``modal-apps/scraper`` (Modal apps
``vecinita-scraper`` workers and ``vecinita-scraper-api``). This module remains
for the legacy **non-HTTP** ``run_reindex`` / ``weekly_reindex`` definitions
until that cron path is fully migrated to the scraper service repo.

See ``docs/deployment/MODAL_DEPLOYMENT.md``.
"""

import os
from pathlib import Path

import modal

BACKEND_DIR = Path(__file__).resolve().parents[3]

APP_NAME = os.getenv("MODAL_SCRAPER_APP_NAME", "vecinita-scraper")
SECRET_NAME = os.getenv("MODAL_SECRET_NAME", "vecinita-secrets")
REINDEX_CRON_SCHEDULE = os.getenv("REINDEX_CRON_SCHEDULE", "0 2 * * 0")

app = modal.App(APP_NAME)

image = (
    modal.Image.debian_slim()
    .pip_install_from_requirements(str(BACKEND_DIR / "requirements.txt"))
    .env({"PYTHONPATH": "/app", "TF_ENABLE_ONEDNN_OPTS": "0"})
)


def _run_scraper_pipeline(clean: bool, stream: bool, verbose: bool) -> dict:
    import subprocess
    import sys
    import time

    cmd = [sys.executable, "-m", "src.services.scraper.cli", "--no-confirm"]
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


@app.function(
    image=image,
    secrets=[modal.Secret.from_name(SECRET_NAME)],
    cpu=2.0,
    memory=4096,
    timeout=3 * 60 * 60,
)
def run_reindex(clean: bool = False, stream: bool = True, verbose: bool = False) -> dict:
    return _run_scraper_pipeline(clean=clean, stream=stream, verbose=verbose)


@app.function(
    image=image,
    secrets=[modal.Secret.from_name(SECRET_NAME)],
    cpu=2.0,
    memory=4096,
    timeout=3 * 60 * 60,
    schedule=modal.Cron(REINDEX_CRON_SCHEDULE),
)
def weekly_reindex() -> dict:
    clean = os.getenv("SCRAPER_REINDEX_CLEAN", "false").lower() in {"1", "true", "yes"}
    verbose = os.getenv("SCRAPER_REINDEX_VERBOSE", "false").lower() in {"1", "true", "yes"}
    return _run_scraper_pipeline(clean=clean, stream=True, verbose=verbose)
