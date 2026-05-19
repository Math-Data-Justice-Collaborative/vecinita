"""Ingest domain types (no FastAPI/Modal imports)."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ScrapedDocument:
    url: str
    title: str | None
    text: str
