"""Shared Modal worker failure reporting (avoid chained ConfigError from get_db)."""

from __future__ import annotations

from vecinita_scraper.core.errors import ConfigError
from vecinita_scraper.core.logger import get_logger
from vecinita_scraper.core.models import JobStatus

logger = get_logger(__name__)


async def report_worker_job_failure(job_id: str, exc: BaseException) -> None:
    """Persist FAILED when possible; never call ``get_db()`` again for ``ConfigError``."""
    if isinstance(exc, ConfigError):
        logger.error(
            "worker_job_configuration_failure",
            job_id=job_id,
            exc_type="ConfigError",
        )
        raise exc

    from vecinita_scraper.core.db import get_db

    db = get_db()
    await db.update_job_status(job_id, JobStatus.FAILED.value, error_message=str(exc))
