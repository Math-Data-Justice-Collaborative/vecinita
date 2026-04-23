"""Submit single-URL scrape jobs to VECINITA_SCRAPER_API_URL (live Modal / DM API)."""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from typing import Any
from urllib.parse import urlparse

import httpx

log = logging.getLogger("vecinita_pipeline.active_crawl.live_scraper")


def normalize_jobs_base_url(raw: str) -> str:
    """Return origin + ``/jobs`` for POST/GET job APIs (matches .env.prod.render examples)."""
    u = (raw or "").strip().rstrip("/")
    if not u:
        raise ValueError("VECINITA_SCRAPER_API_URL is empty")
    parsed = urlparse(u)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        raise ValueError(f"VECINITA_SCRAPER_API_URL must be http(s) with host: {raw!r}")
    if u.endswith("/jobs"):
        return u
    return f"{u}/jobs"


def first_scraper_bearer_token(raw_keys: str) -> str | None:
    parts = [p.strip() for p in (raw_keys or "").split(",") if p.strip()]
    return parts[0] if parts else None


@dataclass(frozen=True)
class LiveScrapeResult:
    """Outcome after POST + poll loop."""

    completed: bool
    terminal_status: str
    error_detail: str | None
    submit_http_status: int | None
    last_poll_http_status: int | None


def submit_and_wait_for_job(
    *,
    jobs_base_url: str,
    bearer: str,
    seed_url: str,
    crawl_run_id: str,
    depth: int,
    poll_interval_s: float,
    max_wait_s: int,
    deadline_monotonic: float,
) -> LiveScrapeResult:
    """POST ``/jobs`` then poll ``GET /jobs/{{id}}`` until terminal state or timeout."""
    headers = {
        "Authorization": f"Bearer {bearer}",
        "Content-Type": "application/json",
        "User-Agent": "VecinaActiveCrawl/0.1",
    }
    payload: dict[str, Any] = {
        "url": seed_url,
        "user_id": "active-crawl-cli",
        "crawl_config": {
            # One URL per active-crawl queue item; remote pipeline handles extraction/chunking.
            "max_depth": 1,
            "timeout_seconds": min(600, max(30, int(max_wait_s))),
            "include_links": False,
            "include_images": False,
        },
        "metadata": {
            "active_crawl_run_id": crawl_run_id,
            "active_crawl_depth": depth,
        },
    }
    submit_status: int | None = None
    last_poll: int | None = None
    with httpx.Client(timeout=120.0, follow_redirects=True) as client:
        try:
            r = client.post(jobs_base_url, json=payload, headers=headers)
        except Exception as exc:
            return LiveScrapeResult(
                completed=False,
                terminal_status="failed",
                error_detail=f"submit_request_error:{exc}",
                submit_http_status=None,
                last_poll_http_status=None,
            )
        submit_status = r.status_code
        if r.status_code not in (200, 201):
            detail = _safe_detail(r)
            return LiveScrapeResult(
                completed=False,
                terminal_status="failed",
                error_detail=f"submit_http_{r.status_code}:{detail}",
                submit_http_status=submit_status,
                last_poll_http_status=None,
            )
        try:
            body = r.json()
        except Exception:
            return LiveScrapeResult(
                completed=False,
                terminal_status="failed",
                error_detail="submit_response_not_json",
                submit_http_status=submit_status,
                last_poll_http_status=None,
            )
        job_id = body.get("job_id")
        if not job_id or not isinstance(job_id, str):
            return LiveScrapeResult(
                completed=False,
                terminal_status="failed",
                error_detail="submit_response_missing_job_id",
                submit_http_status=submit_status,
                last_poll_http_status=None,
            )

        status_url = f"{jobs_base_url.rstrip('/')}/{job_id}"
        terminal = {"completed", "failed", "cancelled"}
        job_deadline = min(deadline_monotonic, time.monotonic() + max(1, int(max_wait_s)))
        while time.monotonic() < job_deadline:
            try:
                pr = client.get(status_url, headers=headers)
            except Exception as exc:
                return LiveScrapeResult(
                    completed=False,
                    terminal_status="failed",
                    error_detail=f"poll_error:{exc}",
                    submit_http_status=submit_status,
                    last_poll_http_status=last_poll,
                )
            last_poll = pr.status_code
            if pr.status_code == 404:
                return LiveScrapeResult(
                    completed=False,
                    terminal_status="failed",
                    error_detail="job_not_found_404",
                    submit_http_status=submit_status,
                    last_poll_http_status=last_poll,
                )
            if pr.status_code >= 400:
                return LiveScrapeResult(
                    completed=False,
                    terminal_status="failed",
                    error_detail=f"poll_http_{pr.status_code}:{_safe_detail(pr)}",
                    submit_http_status=submit_status,
                    last_poll_http_status=last_poll,
                )
            try:
                st = pr.json()
            except Exception:
                time.sleep(poll_interval_s)
                continue
            st_name = (st.get("status") or "").strip().lower()
            if st_name in terminal:
                err = st.get("error_message")
                err_s = str(err).strip() if err is not None else None
                ok = st_name == "completed"
                return LiveScrapeResult(
                    completed=ok,
                    terminal_status=st_name,
                    error_detail=err_s,
                    submit_http_status=submit_status,
                    last_poll_http_status=last_poll,
                )
            time.sleep(poll_interval_s)

        return LiveScrapeResult(
            completed=False,
            terminal_status="failed",
            error_detail="remote_job_poll_timeout",
            submit_http_status=submit_status,
            last_poll_http_status=last_poll,
        )


def _safe_detail(r: httpx.Response) -> str:
    try:
        j = r.json()
        d = j.get("detail") or j.get("message") or j.get("error")
        if isinstance(d, str):
            return d[:500]
    except Exception:
        pass
    return (r.text or "")[:500]
