"""BUG-2026-09-09: Modal DM must spawn process_dm_job (not ASGI BackgroundTasks).

[Spec: docs/adr/ADR-038-modal-job-lifecycle-storage-split.md]
[Spec: docs/bug-reports/BUG-2026-09-09-stuck-pending-eval-jobs.md]
"""

from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
DM_APP = REPO_ROOT / "infra" / "modal" / "data_management_app.py"


def test_data_management_app_defines_process_dm_job_spawn() -> None:
    """ADR-038 / TP-S013-02: durable dispatch via Modal .spawn + modal_call_id."""
    text = DM_APP.read_text(encoding="utf-8")
    assert "def process_dm_job(" in text
    assert "process_dm_job.spawn(" in text
    assert "job_spawner=" in text
    assert "pipeline_runner=runner" not in text
