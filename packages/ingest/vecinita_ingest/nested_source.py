"""Derive nested source metadata from document URLs (F61 / ADR-045)."""

from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import urlparse, urlunparse

from vecinita_ingest.crawl import normalize_url

_FILE_AND_DIR_MIN_SEGMENTS = 2


@dataclass(frozen=True)
class NestedSourceFields:
    """Path/parent fields stored on documents for corpus tree nesting."""

    source_domain: str
    source_path: str
    parent_url: str | None
    canonical_url: str


def _path_segments(path: str) -> list[str]:
    return [part for part in path.split("/") if part]


def derive_nested_source(
    url: str,
    *,
    parent_url: str | None = None,
    source_domain: str | None = None,
    source_path: str | None = None,
    canonical_url: str | None = None,
) -> NestedSourceFields:
    """Compute nested source fields from a URL, honoring explicit overrides."""
    canonical = canonical_url or normalize_url(url)
    parsed = urlparse(canonical)
    domain = (source_domain or parsed.netloc or "unknown").lower()
    segments = _path_segments(parsed.path)
    if source_path is not None:
        path = (
            source_path if source_path.startswith("/") or source_path == "" else f"/{source_path}"
        )
    elif len(segments) >= _FILE_AND_DIR_MIN_SEGMENTS:
        path = "/" + "/".join(segments[:-1])
    else:
        path = "/"

    derived_parent: str | None = parent_url
    if derived_parent is None and path not in {"", "/"}:
        derived_parent = urlunparse((parsed.scheme, domain, path.rstrip("/") + "/", "", "", ""))

    return NestedSourceFields(
        source_domain=domain,
        source_path=path,
        parent_url=derived_parent,
        canonical_url=canonical,
    )
