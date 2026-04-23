"""Active crawl orchestration: BFS + SmartLoader + persistence."""

from __future__ import annotations

import hashlib
import logging
import tempfile
import time
from io import BytesIO
from pathlib import Path
from uuid import UUID

from src.services.scraper.active_crawl.config import ActiveCrawlConfig, retrieval_mode_for
from src.services.scraper.active_crawl.discovery import (
    extract_same_site_links,
    fetch_html_for_discovery,
)
from src.services.scraper.active_crawl.escalation import should_force_playwright
from src.services.scraper.active_crawl.frontier import CrawlFrontier, QueuedURL
from src.services.scraper.active_crawl.persistence import CrawlRepository, FetchAttemptRow
from src.services.scraper.active_crawl.robots import robots_cache_from_env
from src.services.scraper.active_crawl.url_policy import (
    hostname_of,
    load_allowlist,
    normalize_canonical_url,
    registrable_domain,
)
from src.services.scraper.config import ScraperConfig
from src.services.scraper.loaders import SmartLoader
from src.services.scraper.utils import normalize_scrape_url

log = logging.getLogger("vecinita_pipeline.active_crawl.runner")


def _loader_to_retrieval_path(loader_type: str) -> str:
    lt = (loader_type or "").lower()
    if "playwright" in lt:
        return "playwright"
    if "recursive" in lt:
        return "recursive_loader"
    if "skip" in lt:
        return "skipped"
    return "static"


def _docs_text(docs: list) -> str:
    parts: list[str] = []
    for d in docs:
        pc = getattr(d, "page_content", None) or ""
        if pc:
            parts.append(pc)
    return "\n\n".join(parts).strip()


def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _read_seed_urls(cfg: ActiveCrawlConfig) -> list[str]:
    if not cfg.seeds_file.is_file():
        raise FileNotFoundError(f"Seed file not found: {cfg.seeds_file}")
    urls: list[str] = []
    for line in cfg.seeds_file.read_text(encoding="utf-8").splitlines():
        n = normalize_scrape_url(line)
        if n:
            urls.append(n)
    if not urls:
        raise ValueError(f"No valid URLs in {cfg.seeds_file}")
    return urls


def run_once_seeds(cfg: ActiveCrawlConfig, *, bfs: bool = True) -> UUID:
    """MVP: seeds only. When bfs=False, only seeds are fetched (legacy name)."""
    return run_active_crawl(cfg, bfs=bfs)


def run_active_crawl(cfg: ActiveCrawlConfig, *, bfs: bool = True) -> UUID:
    repo = CrawlRepository()
    allowlist = load_allowlist(cfg.allowlist_file)
    robots = robots_cache_from_env()
    scraper_cfg = ScraperConfig()
    loader = SmartLoader(scraper_cfg)
    seeds = _read_seed_urls(cfg)

    snapshot = {
        "max_depth": cfg.max_depth,
        "max_pages_total": cfg.max_pages_total,
        "max_pages_per_host": cfg.max_pages_per_host,
        "wall_seconds": cfg.wall_seconds,
        "no_raw": cfg.no_raw,
        "seeds_file": str(cfg.seeds_file),
        "bfs": bfs,
    }
    run_id = repo.create_run(snapshot)

    frontier = CrawlFrontier(max_depth=cfg.max_depth)
    per_host: dict[str, int] = {}
    pages_budget_used = 0
    wall = time.monotonic() + cfg.wall_seconds

    for s in seeds:
        canon = normalize_canonical_url(s)
        if not canon:
            continue
        host = hostname_of(canon)
        root = registrable_domain(host)
        frontier.seed(canon, root)

    failed_log = tempfile.NamedTemporaryFile(delete=False, suffix="_active_crawl_failed.log")
    failed_log.close()
    failed_log_path = failed_log.name

    try:
        while True:
            if time.monotonic() > wall:
                log.warning("Wall clock cap reached; stopping crawl")
                break
            if pages_budget_used >= cfg.max_pages_total:
                log.info("max_pages_total reached")
                break
            item = frontier.dequeue()
            if item is None:
                break
            pages_budget_used += 1

            host = hostname_of(item.url)
            if per_host.get(host, 0) >= cfg.max_pages_per_host:
                repo.insert_fetch_attempt(
                    FetchAttemptRow(
                        crawl_run_id=run_id,
                        canonical_url=item.url,
                        requested_url=item.url,
                        final_url=None,
                        seed_root=item.seed_root,
                        depth=item.depth,
                        http_status=None,
                        outcome="skipped",
                        skip_reason="max_pages_per_host",
                        retrieval_path="static",
                        document_format=None,
                        extracted_text=None,
                        raw_artifact=None,
                        raw_omitted_reason=None,
                        content_sha256=None,
                        pdf_extraction_status=None,
                        error_detail=None,
                    )
                )
                repo.increment_counters(run_id, skipped=1)
                continue

            if not robots.can_fetch(item.url):
                repo.insert_fetch_attempt(
                    FetchAttemptRow(
                        crawl_run_id=run_id,
                        canonical_url=item.url,
                        requested_url=item.url,
                        final_url=None,
                        seed_root=item.seed_root,
                        depth=item.depth,
                        http_status=None,
                        outcome="skipped",
                        skip_reason="robots",
                        retrieval_path="static",
                        document_format=None,
                        extracted_text=None,
                        raw_artifact=None,
                        raw_omitted_reason=None,
                        content_sha256=None,
                        pdf_extraction_status=None,
                        error_detail=None,
                    )
                )
                repo.increment_counters(run_id, skipped=1)
                continue

            if item.url.lower().split("?", 1)[0].endswith(".pdf"):
                t0 = time.perf_counter()
                _handle_pdf_url(cfg, repo, run_id, item)
                dt_ms = int((time.perf_counter() - t0) * 1000)
                log.info(
                    "active_crawl_rate crawl_run_id=%s host=%s delta_ms=%s outcome=pdf",
                    run_id,
                    host,
                    dt_ms,
                )
                per_host[host] = per_host.get(host, 0) + 1
                continue

            mode = retrieval_mode_for(cfg, item.url)
            t0 = time.perf_counter()
            if mode == "always_playwright":
                docs, ltype, ok = loader.load_url(
                    item.url, failed_log=failed_log_path, force_loader="playwright"
                )
            elif mode == "static_only":
                docs, ltype, ok = loader.load_url(
                    item.url, failed_log=failed_log_path, force_loader="unstructured"
                )
            else:
                docs, ltype, ok = loader.load_url(
                    item.url, failed_log=failed_log_path, force_loader=None
                )
                if not ok:
                    docs2, ltype2, ok2 = loader.load_url(
                        item.url, failed_log=failed_log_path, force_loader="playwright"
                    )
                    if ok2:
                        docs, ltype, ok = docs2, ltype2, ok2
                text_probe = _docs_text(docs) if ok else ""
                if ok and should_force_playwright(
                    thin_body_chars=len(text_probe),
                    threshold=cfg.thin_body_threshold,
                    static_failed=False,
                ):
                    docs2, ltype2, ok2 = loader.load_url(
                        item.url, failed_log=failed_log_path, force_loader="playwright"
                    )
                    if ok2 and _docs_text(docs2):
                        docs, ltype, ok = docs2, ltype2, ok2
            text = _docs_text(docs) if ok else ""

            _persist_html_attempt(
                cfg,
                repo,
                run_id,
                item,
                ok,
                ltype,
                text,
                docs if ok else [],
            )
            per_host[host] = per_host.get(host, 0) + 1
            repo.increment_counters(run_id, fetched=1 if ok else 0, failed=0 if ok else 1)
            dt_ms = int((time.perf_counter() - t0) * 1000)
            log.info(
                "active_crawl_rate crawl_run_id=%s host=%s delta_ms=%s retrieval_mode=%s ok=%s loader=%s",
                run_id,
                host,
                dt_ms,
                mode,
                ok,
                ltype,
            )

            if ok and bfs and item.depth < cfg.max_depth:
                dr = fetch_html_for_discovery(item.url)
                if dr.html:
                    links = extract_same_site_links(
                        item.url,
                        dr.html,
                        seed_registrable=item.seed_root,
                        allowlist=allowlist,
                    )
                    for link in links:
                        frontier.enqueue(
                            QueuedURL(url=link, depth=item.depth + 1, seed_root=item.seed_root)
                        )

        repo.finish_run(run_id, "completed")
    except Exception as exc:
        log.exception("Active crawl failed: %s", exc)
        repo.finish_run(run_id, "failed", notes=str(exc)[:2000])
        raise
    finally:
        Path(failed_log_path).unlink(missing_ok=True)

    log.info("active_crawl_rate summary crawl_run_id=%s status=completed", run_id)
    return run_id


def _persist_html_attempt(
    cfg: ActiveCrawlConfig,
    repo: CrawlRepository,
    run_id: UUID,
    item: QueuedURL,
    ok: bool,
    loader_type: str,
    text: str,
    docs: list,
) -> None:
    path = _loader_to_retrieval_path(loader_type)
    fmt = "html"
    sha = _sha256(text) if text else None
    raw: bytes | None = None
    raw_omit: str | None = None
    if ok and text and not cfg.no_raw:
        try:
            joined = "\n\n".join(getattr(d, "page_content", "") or "" for d in docs)
            raw = joined.encode("utf-8", errors="replace")[:4_000_000]
        except Exception:
            raw_omit = "serialization_error"
    elif cfg.no_raw:
        raw_omit = "ACTIVE_CRAWL_NO_RAW"

    outcome = "success" if ok and text else ("partial" if ok else "failed")
    err = None if ok else "loader_failed_or_empty"

    repo.insert_fetch_attempt(
        FetchAttemptRow(
            crawl_run_id=run_id,
            canonical_url=item.url,
            requested_url=item.url,
            final_url=item.url,
            seed_root=item.seed_root,
            depth=item.depth,
            http_status=200 if ok else None,
            outcome=outcome,
            skip_reason=None,
            retrieval_path=path,
            document_format=fmt,
            extracted_text=text or None,
            raw_artifact=raw,
            raw_omitted_reason=raw_omit,
            content_sha256=sha,
            pdf_extraction_status="na",
            error_detail=err,
        )
    )


def _handle_pdf_url(
    cfg: ActiveCrawlConfig,
    repo: CrawlRepository,
    run_id: UUID,
    item: QueuedURL,
) -> None:
    import httpx

    try:
        with httpx.Client(timeout=60.0, follow_redirects=True) as client:
            r = client.get(item.url, headers={"User-Agent": "VecinaActiveCrawl/0.1"})
        status = r.status_code
        if status != 200:
            repo.insert_fetch_attempt(
                FetchAttemptRow(
                    crawl_run_id=run_id,
                    canonical_url=item.url,
                    requested_url=item.url,
                    final_url=str(r.url),
                    seed_root=item.seed_root,
                    depth=item.depth,
                    http_status=status,
                    outcome="failed",
                    skip_reason=None,
                    retrieval_path="static",
                    document_format="pdf",
                    extracted_text=None,
                    raw_artifact=None,
                    raw_omitted_reason="http_error",
                    content_sha256=None,
                    pdf_extraction_status="failed",
                    error_detail=f"HTTP {status}",
                )
            )
            repo.increment_counters(run_id, failed=1)
            return
        data = r.content
        if len(data) > 20_000_000:
            repo.insert_fetch_attempt(
                FetchAttemptRow(
                    crawl_run_id=run_id,
                    canonical_url=item.url,
                    requested_url=item.url,
                    final_url=str(r.url),
                    seed_root=item.seed_root,
                    depth=item.depth,
                    http_status=status,
                    outcome="partial",
                    skip_reason=None,
                    retrieval_path="static",
                    document_format="pdf",
                    extracted_text=None,
                    raw_artifact=None if cfg.no_raw else data[:1_000_000],
                    raw_omitted_reason="too_large" if cfg.no_raw else None,
                    content_sha256=hashlib.sha256(data).hexdigest(),
                    pdf_extraction_status="skipped_size",
                    error_detail=None,
                )
            )
            repo.increment_counters(run_id, fetched=1)
            return
        text, pstatus = _extract_pdf_text(data)
        raw = None if cfg.no_raw else data
        raw_omit = "ACTIVE_CRAWL_NO_RAW" if cfg.no_raw else None
        repo.insert_fetch_attempt(
            FetchAttemptRow(
                crawl_run_id=run_id,
                canonical_url=item.url,
                requested_url=item.url,
                final_url=str(r.url),
                seed_root=item.seed_root,
                depth=item.depth,
                http_status=status,
                outcome="success" if text else "partial",
                skip_reason=None,
                retrieval_path="static",
                document_format="pdf",
                extracted_text=text or None,
                raw_artifact=raw,
                raw_omitted_reason=raw_omit,
                content_sha256=hashlib.sha256(data).hexdigest(),
                pdf_extraction_status=pstatus,
                error_detail=None if text else "empty_pdf_text",
            )
        )
        repo.increment_counters(run_id, fetched=1)
    except Exception as exc:
        repo.insert_fetch_attempt(
            FetchAttemptRow(
                crawl_run_id=run_id,
                canonical_url=item.url,
                requested_url=item.url,
                final_url=None,
                seed_root=item.seed_root,
                depth=item.depth,
                http_status=None,
                outcome="failed",
                skip_reason=None,
                retrieval_path="static",
                document_format="pdf",
                extracted_text=None,
                raw_artifact=None,
                raw_omitted_reason=None,
                content_sha256=None,
                pdf_extraction_status="failed",
                error_detail=str(exc)[:4000],
            )
        )
        repo.increment_counters(run_id, failed=1)


def _extract_pdf_text(data: bytes) -> tuple[str, str]:
    try:
        from pypdf import PdfReader

        reader = PdfReader(BytesIO(data))
        parts: list[str] = []
        for page in reader.pages:
            t = page.extract_text() or ""
            if t:
                parts.append(t)
        text = "\n\n".join(parts).strip()
        return text, "ok" if text else "failed"
    except Exception:
        return "", "failed"
