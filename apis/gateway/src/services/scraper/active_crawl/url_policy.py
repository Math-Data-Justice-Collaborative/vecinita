"""Canonical URLs, naive registrable-domain scope, allowlist."""

from __future__ import annotations

import logging
from pathlib import Path
from urllib.parse import urljoin, urlparse, urlunparse

log = logging.getLogger("vecinita_pipeline.active_crawl.url_policy")


def normalize_canonical_url(url: str) -> str | None:
    """Return scheme+host+path(+query) lowercase host, strip fragment."""
    parsed = urlparse(url.strip())
    if parsed.scheme.lower() not in {"http", "https"}:
        return None
    host = (parsed.hostname or "").lower()
    if not host:
        return None
    netloc = host if parsed.port in (None, 80, 443) else f"{host}:{parsed.port}"
    path = parsed.path or ""
    if path != "/" and path.endswith("/"):
        path = path.rstrip("/")
    return urlunparse(
        (
            parsed.scheme.lower(),
            netloc,
            path,
            parsed.params,
            parsed.query,
            "",
        )
    )


def registrable_domain(host: str) -> str:
    """Naive eTLD+1: last two labels (see research.md §2b caveats)."""
    host = host.lower().removeprefix("www.")
    parts = [p for p in host.split(".") if p]
    if len(parts) >= 2:
        return ".".join(parts[-2:])
    return host


def hostname_of(url: str) -> str:
    return (urlparse(url).hostname or "").lower()


def load_allowlist(path: Path | None) -> frozenset[str]:
    if path is None or not path.is_file():
        return frozenset()
    domains: set[str] = set()
    for line in path.read_text(encoding="utf-8").splitlines():
        s = line.strip()
        if not s or s.startswith("#"):
            continue
        s = s.lower().removeprefix("www.")
        if "://" in s:
            nu = normalize_canonical_url(s)
            if nu:
                s = registrable_domain(hostname_of(nu))
        else:
            s = registrable_domain(s)
        domains.add(s)
    log.info("Loaded %s allowlist entries from %s", len(domains), path)
    return frozenset(domains)


def is_in_scope(
    target_url: str,
    seed_root: str,
    allowlist: frozenset[str],
) -> tuple[bool, str | None]:
    """Same registrable domain as seed_root, or allowlisted registrable domain."""
    canon = normalize_canonical_url(target_url)
    if not canon:
        return False, "invalid_url"
    host = hostname_of(canon)
    if not host:
        return False, "no_host"
    tdom = registrable_domain(host)
    sdom = registrable_domain(seed_root.lower().removeprefix("www.").split("/")[0])
    if tdom == sdom:
        return True, None
    if tdom in allowlist or host in allowlist:
        return True, None
    return False, "off_domain"


def absolutize(base_url: str, href: str) -> str | None:
    joined = urljoin(base_url, href)
    return normalize_canonical_url(joined)
