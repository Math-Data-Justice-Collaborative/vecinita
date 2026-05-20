"""Ingest domain types (no FastAPI/Modal imports)."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ScrapedDocument:
    """Normalized page content extracted from a fetched URL."""

    url: str
    title: str | None
    text: str
