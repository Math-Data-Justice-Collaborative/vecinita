"""Shared TypedDict shapes for pytest fixtures (strict typing)."""

from __future__ import annotations

from typing import TYPE_CHECKING, TypedDict

if TYPE_CHECKING:
    from uuid import UUID


class DocumentFixtureData(TypedDict):
    """Document id and URL produced by audit/history E2E fixtures."""

    doc_id: UUID
    url: str
