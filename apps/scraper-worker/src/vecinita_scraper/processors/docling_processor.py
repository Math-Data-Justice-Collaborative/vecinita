"""Docling integration for normalizing crawled documents into structured markdown."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

from vecinita_scraper.core.errors import ProcessingError
from vecinita_scraper.core.logger import get_logger

logger = get_logger(__name__)


@dataclass(slots=True)
class ProcessedDocument:
    """Normalized processed document output."""

    markdown_content: str
    tables_json: str | None
    metadata_json: str | None


class DoclingProcessor:
    """Convert raw crawled content into a structured document representation."""

    def process_content(self, raw_content: str, content_type: str) -> ProcessedDocument:
        """Process content based on its detected type."""
        normalized_type = content_type.lower()
        if normalized_type in {"pdf", "docx", "html"}:
            return self._process_with_docling(raw_content, normalized_type)
        return self._process_plain_markdown(raw_content, normalized_type)

    def _process_with_docling(self, raw_content: str, content_type: str) -> ProcessedDocument:
        """Use Docling for richer document understanding when appropriate."""
        try:
            from docling.document_converter import DocumentConverter
        except ImportError as exc:
            raise ProcessingError(
                "docling is not installed. Install project dependencies"
                " before processing documents."
            ) from exc

        try:
            converter = DocumentConverter()
            result = converter.convert(self._build_source(raw_content, content_type))
        except Exception as exc:
            logger.exception("Docling conversion failed", content_type=content_type)
            raise ProcessingError(
                f"Docling failed to process {content_type} content: {exc}"
            ) from exc

        document = result.document
        markdown_content = document.export_to_markdown()
        tables = self._extract_tables(document)
        metadata = {
            "content_type": content_type,
            "has_tables": bool(tables),
            "markdown_length": len(markdown_content),
        }
        return ProcessedDocument(
            markdown_content=markdown_content,
            tables_json=json.dumps(tables) if tables else None,
            metadata_json=json.dumps(metadata),
        )

    def _process_plain_markdown(self, raw_content: str, content_type: str) -> ProcessedDocument:
        """Fallback path for already-normalized markdown/text content."""
        metadata = {
            "content_type": content_type,
            "normalized": True,
            "markdown_length": len(raw_content),
        }
        return ProcessedDocument(
            markdown_content=raw_content.strip(),
            tables_json=None,
            metadata_json=json.dumps(metadata),
        )

    @staticmethod
    def _build_source(raw_content: str, content_type: str) -> str:
        """Build a Docling-compatible source reference."""
        if content_type == "html":
            return f"raw://{raw_content}"
        return raw_content

    @staticmethod
    def _extract_tables(document: Any) -> list[dict[str, Any]]:
        """Best-effort table extraction from a Docling document."""
        tables_attr = getattr(document, "tables", None)
        if not isinstance(tables_attr, list):
            return []

        tables: list[dict[str, Any]] = []
        for index, table in enumerate(tables_attr):
            export = getattr(table, "export_to_dataframe", None)
            if callable(export):
                dataframe = export()
                tables.append(
                    {
                        "index": index,
                        "columns": list(getattr(dataframe, "columns", [])),
                        "records": dataframe.to_dict(orient="records"),
                    }
                )
            else:
                tables.append({"index": index, "value": str(table)})
        return tables
