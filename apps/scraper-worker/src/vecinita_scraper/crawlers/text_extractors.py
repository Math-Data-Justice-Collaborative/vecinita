"""Type-specific text extraction for direct PDF and plain-text fetches."""

from __future__ import annotations

from io import BytesIO
from typing import Final

from vecinita_scraper.core.outcome_kinds import FailureCategory

try:
    from charset_normalizer import from_bytes as charset_from_bytes
except ImportError:  # pragma: no cover
    charset_from_bytes = None  # type: ignore[assignment]

try:
    from pypdf import PdfReader
    from pypdf.errors import PdfReadError
except ImportError:  # pragma: no cover
    PdfReader = None  # type: ignore[misc, assignment]
    PdfReadError = Exception  # type: ignore[misc, assignment]


class DirectDocumentExtractError(Exception):
    """Direct fetch path could not yield usable text."""

    def __init__(self, category: FailureCategory, message: str) -> None:
        super().__init__(message)
        self.category = category


_MAX_CHARSET_PROBE: Final[int] = 500_000


def extract_pdf_text(data: bytes) -> str:  # noqa: C901
    """Extract Unicode text from PDF bytes."""
    if PdfReader is None:
        raise DirectDocumentExtractError(
            FailureCategory.PDF_CORRUPT_OR_UNREADABLE,
            "pypdf is not installed",
        )
    try:
        reader = PdfReader(BytesIO(data))
    except PdfReadError as exc:
        raise DirectDocumentExtractError(
            FailureCategory.PDF_CORRUPT_OR_UNREADABLE,
            f"Invalid PDF: {exc}",
        ) from exc
    except Exception as exc:  # noqa: BLE001
        raise DirectDocumentExtractError(
            FailureCategory.PDF_CORRUPT_OR_UNREADABLE,
            f"Could not open PDF: {exc}",
        ) from exc

    if getattr(reader, "is_encrypted", False):
        try:
            decrypt_rc = reader.decrypt("")
            if decrypt_rc == 0:
                raise DirectDocumentExtractError(
                    FailureCategory.PDF_PASSWORD_PROTECTED,
                    "PDF requires a password",
                )
        except DirectDocumentExtractError:
            raise
        except Exception as exc:
            raise DirectDocumentExtractError(
                FailureCategory.PDF_PASSWORD_PROTECTED,
                f"Encrypted PDF: {exc}",
            ) from exc

    parts: list[str] = []
    try:
        for page in reader.pages:
            parts.append(page.extract_text() or "")
    except Exception as exc:
        raise DirectDocumentExtractError(
            FailureCategory.PDF_CORRUPT_OR_UNREADABLE,
            f"Failed reading PDF pages: {exc}",
        ) from exc

    text = "\n".join(parts).strip()
    if not text:
        raise DirectDocumentExtractError(
            FailureCategory.PDF_EMPTY_NON_EXTRACTIVE,
            "No extractable text in PDF (may be image-only)",
        )
    return text


def decode_plain_text_bytes(data: bytes, declared_charset: str | None = None) -> str:
    """Decode text/plain bytes with charset fallbacks."""
    if not data:
        raise DirectDocumentExtractError(FailureCategory.TEXT_EMPTY, "Empty response body")

    if declared_charset:
        try:
            return data.decode(declared_charset.split(";")[0].strip(), errors="strict")
        except (LookupError, UnicodeDecodeError):
            pass

    if charset_from_bytes is not None:
        match = charset_from_bytes(data[:_MAX_CHARSET_PROBE])
        if match:
            best = match.best()
            if best is not None:
                return str(best)

    try:
        return data.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise DirectDocumentExtractError(
            FailureCategory.TEXT_ENCODING_FAILURE,
            f"Could not decode plain text: {exc}",
        ) from exc
