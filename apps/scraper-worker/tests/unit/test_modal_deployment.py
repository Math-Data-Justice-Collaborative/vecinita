"""Regression tests for Modal deployment configuration.

These tests guard against the ModuleNotFoundError that occurs when the
vecinita_scraper package is not mounted into the Modal container image.
Reproduces: ModuleNotFoundError: No module named 'vecinita_scraper' at
/root/app.py line 5 inside the deployed container.
"""

from __future__ import annotations

from pathlib import Path

import pytest

_SRC_ROOT = Path(__file__).parent.parent.parent / "src"
_WORKERS_APP = _SRC_ROOT / "vecinita_scraper" / "app.py"
_API_APP = _SRC_ROOT / "vecinita_scraper" / "api" / "app.py"

_REQUIRED_CALL = 'add_local_python_source("vecinita_scraper")'
_FROM_NAME = "Function.from_name"


@pytest.mark.unit
def test_trigger_reindex_uses_modal_function_from_name() -> None:
    """``trigger_reindex`` must resolve drain workers via ``from_name``, not in-process imports.

    Spawning handles obtained by importing sibling worker modules can be unhydrated inside
    a Modal container and fail with ``ExecutionError: ... App it is defined on is not running``.
    """
    content = _WORKERS_APP.read_text()
    assert _FROM_NAME in content
    assert "def lookup_scraper_deployed_function" in content
    assert "drain_scrape_queue" in content and "drain_store_queue" in content
    assert "lookup_scraper_deployed_function(fn_tag)" in content
    assert "def spawn_deployed_worker_map" in content
    assert "spawn_map.aio" in content


@pytest.mark.unit
def test_job_control_uses_modal_spawn_on_scraper_worker() -> None:
    """Submit path should prefer ``spawn.aio`` on ``scraper_worker`` (Modal job-queue pattern)."""
    text = (_SRC_ROOT / "vecinita_scraper" / "services" / "job_control.py").read_text()
    assert "scraper_worker" in text
    assert "spawn.aio" in text
    assert "_dispatch_scrape_job_to_modal_worker" in text


@pytest.mark.unit
def test_worker_drains_submit_batch_via_spawn_map() -> None:
    """Drains batch-submit worker jobs via shared ``spawn_map`` helper (Modal batch pattern)."""
    app_text = _WORKERS_APP.read_text()
    assert "spawn_deployed_worker_map" in app_text
    assert "spawn_map.aio" in app_text

    worker_dir = _SRC_ROOT / "vecinita_scraper" / "workers"
    for name in ("scraper.py", "processor.py", "chunker.py", "embedder.py", "finalizer.py"):
        text = (worker_dir / name).read_text()
        msg = f"{name}: expected spawn_deployed_worker_map"
        assert "spawn_deployed_worker_map" in text, msg
        assert 'await spawn_deployed_worker_map("' in text


@pytest.mark.unit
def test_workers_app_image_mounts_local_package() -> None:
    """Workers app must call add_local_python_source so the package is
    importable inside the Modal container.

    Without this, Modal copies only the entry-point script to /root/app.py
    but the vecinita_scraper package is absent from the container's Python
    path, causing ModuleNotFoundError on every worker invocation.
    """
    content = _WORKERS_APP.read_text()
    assert _REQUIRED_CALL in content, (
        f"{_WORKERS_APP.relative_to(_SRC_ROOT.parent)} must contain "
        f"'{_REQUIRED_CALL}' in the image definition so the "
        "vecinita_scraper package is available inside the Modal container."
    )
    assert "playwright install" in content and "--with-deps" in content and "chromium" in content, (
        f"{_WORKERS_APP.relative_to(_SRC_ROOT.parent)} must run "
        "`python -m playwright install --with-deps chromium` after pip_install "
        "so Crawl4AI can launch Chromium in Modal (browser bundle is not installed by pip alone)."
    )


@pytest.mark.unit
def test_api_app_image_mounts_local_package() -> None:
    """API app must call add_local_python_source so the package is
    importable inside the Modal container.

    Imports from ``vecinita_scraper.api.server`` (e.g. ``create_app``) run when
    Modal loads the script in the container, so the package must be present in
    the image.
    """
    content = _API_APP.read_text()
    assert _REQUIRED_CALL in content, (
        f"{_API_APP.relative_to(_SRC_ROOT.parent)} must contain "
        f"'{_REQUIRED_CALL}' in the image definition so the "
        "vecinita_scraper package is available inside the Modal container."
    )
