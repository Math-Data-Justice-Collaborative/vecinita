"""Best-effort PDF text extraction for ingest (F59 / ADR-045)."""

from __future__ import annotations

from io import BytesIO

from pypdf import PdfReader


class PdfExtractError(ValueError):
    """Raised when a PDF has no extractable text (soft-fail at job layer)."""


def extract_pdf_text(data: bytes) -> str:
    """Extract text from PDF bytes; raise ``PdfExtractError`` if empty."""
    reader = PdfReader(BytesIO(data))
    parts: list[str] = []
    for page in reader.pages:
        extracted = page.extract_text()
        stripped = extracted.strip()
        if stripped:
            parts.append(stripped)
    text = "\n".join(parts).strip()
    if not text:
        msg = "PDF has no extractable text"
        raise PdfExtractError(msg)
    return text
