"""Fetch ollama.com public library metadata for super-admin catalog browsing."""

from __future__ import annotations

import re
import time
from typing import Final, Protocol

import httpx

_PLAYGROUND_LIBRARY_BASE: Final[str] = "https://ollama.com"
_LIBRARY_HREF_RE: Final[re.Pattern[str]] = re.compile(r'href="/library/([^"/]+)"')
_SLUG_RE: Final[re.Pattern[str]] = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9._-]*$")
_CACHE_TTL_SECONDS: Final[float] = 3600.0

_families_cache: tuple[float, list[str]] | None = None
_tags_cache: dict[str, tuple[float, list[str]]] = {}


class PlaygroundLibraryClientError(RuntimeError):
    """Raised when playground library metadata cannot be fetched or parsed."""


class PlaygroundLibraryClientProtocol(Protocol):
    """Read ollama.com library metadata (mockable in tests)."""

    def list_families(self) -> list[str]: ...  # noqa: D102

    def list_tags(self, slug: str) -> list[str]: ...  # noqa: D102

    def close(self) -> None: ...  # noqa: D102


def _validate_slug(slug: str) -> str:
    cleaned = slug.strip()
    if not cleaned or not _SLUG_RE.fullmatch(cleaned):
        msg = f"Invalid model slug: {slug!r}"
        raise PlaygroundLibraryClientError(msg)
    return cleaned


def parse_library_slugs(html: str) -> list[str]:
    """Extract sorted unique model family slugs from the library index HTML."""
    return sorted(set(_LIBRARY_HREF_RE.findall(html)))


def parse_model_tags(slug: str, html: str) -> list[str]:
    """Extract sorted unique full model_id tags from a model family tags page."""
    validated = _validate_slug(slug)
    tag_re = re.compile(rf"{re.escape(validated)}:[a-zA-Z0-9][a-zA-Z0-9._-]+")
    return sorted(set(tag_re.findall(html)))


class PlaygroundLibraryClient:
    """Read-only client for ollama.com/library pages (no official registry API)."""

    def __init__(
        self,
        *,
        http_client: httpx.Client | None = None,
        timeout: float = 30.0,
    ) -> None:
        """Optionally inject an HTTP client (for tests) and request timeout."""
        self._owns = http_client is None
        self._client = http_client or httpx.Client(
            base_url=_PLAYGROUND_LIBRARY_BASE,
            timeout=timeout,
            follow_redirects=True,
        )

    def close(self) -> None:
        """Close the owned HTTP client when this wrapper created it."""
        if self._owns:
            self._client.close()

    def list_families(self) -> list[str]:
        """Return all model family slugs published on ollama.com/library."""
        global _families_cache  # noqa: PLW0603
        now = time.monotonic()
        if _families_cache is not None:
            cached_at, cached = _families_cache
            if now - cached_at < _CACHE_TTL_SECONDS:
                return list(cached)

        response = self._client.get("/library")
        if response.status_code >= httpx.codes.BAD_REQUEST:
            msg = f"playground library index failed: {response.status_code}"
            raise PlaygroundLibraryClientError(msg)
        families = parse_library_slugs(response.text)
        _families_cache = (now, families)
        return list(families)

    def list_tags(self, slug: str) -> list[str]:
        """Return all published tags for one model family slug."""
        validated = _validate_slug(slug)
        now = time.monotonic()
        cached_entry = _tags_cache.get(validated)
        if cached_entry is not None:
            cached_at, cached = cached_entry
            if now - cached_at < _CACHE_TTL_SECONDS:
                return list(cached)

        response = self._client.get(f"/library/{validated}/tags")
        if response.status_code >= httpx.codes.BAD_REQUEST:
            msg = f"playground tags page failed for {validated}: {response.status_code}"
            raise PlaygroundLibraryClientError(msg)
        tags = parse_model_tags(validated, response.text)
        _tags_cache[validated] = (now, tags)
        return list(tags)


def reset_playground_library_cache_for_tests() -> None:
    """Clear in-memory library caches between tests."""
    global _families_cache  # noqa: PLW0603
    _families_cache = None
    _tags_cache.clear()
