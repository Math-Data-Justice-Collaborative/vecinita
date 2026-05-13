"""Unit tests for Docling processor."""

from __future__ import annotations

import json
from types import SimpleNamespace

import pytest

from vecinita_scraper.processors.docling_processor import DoclingProcessor


@pytest.mark.unit
def test_process_plain_markdown_returns_normalized_document() -> None:
    """Markdown content should pass through without requiring Docling."""
    processor = DoclingProcessor()

    processed = processor.process_content("# Title\n\nBody", "markdown")

    assert processed.markdown_content == "# Title\n\nBody"
    assert processed.tables_json is None
    metadata = json.loads(processed.metadata_json or "{}")
    assert metadata["content_type"] == "markdown"
    assert metadata["normalized"] is True


@pytest.mark.unit
def test_process_html_uses_docling(monkeypatch) -> None:
    """HTML content should route through the Docling processor path."""
    processor = DoclingProcessor()

    class FakeDocument:
        tables = []

        def export_to_markdown(self) -> str:
            return "# Converted"

    class FakeConverter:
        def convert(self, source: str) -> SimpleNamespace:
            assert source.startswith("raw://")
            return SimpleNamespace(document=FakeDocument())

    fake_module = SimpleNamespace(DocumentConverter=FakeConverter)
    monkeypatch.setitem(__import__("sys").modules, "docling.document_converter", fake_module)

    processed = processor.process_content("<h1>Converted</h1>", "html")

    assert processed.markdown_content == "# Converted"
    metadata = json.loads(processed.metadata_json or "{}")
    assert metadata["content_type"] == "html"
    assert metadata["has_tables"] is False
