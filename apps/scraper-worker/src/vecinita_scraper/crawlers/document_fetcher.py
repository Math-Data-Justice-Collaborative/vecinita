"""Bounded GET and sniff for direct PDF and plain-text URLs (bypass browser)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final

import httpx

from vecinita_scraper.core.models import CrawlConfig
from vecinita_scraper.core.outcome_kinds import FailureCategory, ResponseKind
from vecinita_scraper.crawlers.text_extractors import (
    DirectDocumentExtractError,
    decode_plain_text_bytes,
    extract_pdf_text,
)

_PDF_MAGIC: Final[bytes] = b"%PDF"


@dataclass(slots=True)
class RoutedDocument:
    """Result of a non-browser direct fetch."""

    response_kind: ResponseKind
    text: str
    status_code: int
    success: bool
    failure_category: FailureCategory | None
    operator_summary: str | None
    declared_content_type: str | None


def _normalize_ctype(value: str | None) -> str | None:
    if not value:
        return None
    return value.split(";")[0].strip().lower() or None


def _charset_from_ctype(ctype_full: str | None) -> str | None:
    if not ctype_full or "charset=" not in ctype_full.lower():
        return None
    return ctype_full.split("charset=", 1)[-1].strip().strip('"')


def _looks_pdf(body: bytes, ctype: str | None) -> bool:
    if ctype == "application/pdf":
        return True
    return bool(body) and body.startswith(_PDF_MAGIC)


def _looks_html(body: bytes, ctype: str | None) -> bool:
    if ctype in {"text/html", "application/xhtml+xml"}:
        return True
    probe = body[:400].lstrip().lower()
    return probe.startswith(b"<html") or probe.startswith(b"<!doctype")


async def _read_body_capped(
    client: httpx.AsyncClient,
    url: str,
    max_bytes: int,
) -> tuple[bytes, int, str | None]:
    async with client.stream("GET", url) as response:
        status = int(response.status_code)
        ctype_full = response.headers.get("content-type")
        chunks: list[bytes] = []
        total = 0
        async for chunk in response.aiter_bytes():
            if not chunk:
                continue
            take = min(len(chunk), max_bytes - total)
            chunks.append(chunk[:take])
            total += take
            if total >= max_bytes:
                break
        return b"".join(chunks), status, ctype_full


async def try_direct_document_fetch(  # noqa: C901
    url: str, config: CrawlConfig
) -> RoutedDocument | None:
    """
    Return RoutedDocument when URL is handled as PDF or plain text.

    Return None to fall back to Crawl4AI (HTML / unknown binary).
    """
    connect_s = min(30.0, float(config.timeout_seconds))
    timeout = httpx.Timeout(config.timeout_seconds, connect=connect_s)
    limits = httpx.Limits(max_keepalive_connections=2, max_connections=5)
    async with httpx.AsyncClient(timeout=timeout, follow_redirects=True, limits=limits) as client:
        try:
            body, status, ctype_full = await _read_body_capped(
                client, url, config.max_direct_fetch_bytes
            )
        except httpx.RequestError as exc:
            return RoutedDocument(
                response_kind=ResponseKind.UNKNOWN,
                text="",
                status_code=0,
                success=False,
                failure_category=FailureCategory.TRANSPORT_ERROR,
                operator_summary=f"Network error during direct fetch: {exc}",
                declared_content_type=None,
            )

    ctype = _normalize_ctype(ctype_full)

    if status >= 400:
        return RoutedDocument(
            response_kind=ResponseKind.UNKNOWN,
            text="",
            status_code=status,
            success=False,
            failure_category=FailureCategory.HTTP_ERROR,
            operator_summary=f"HTTP {status} when fetching document.",
            declared_content_type=ctype,
        )

    if _looks_html(body, ctype):
        return None

    if _looks_pdf(body, ctype):
        allowed_pdf_ct = {None, "application/pdf", "application/octet-stream"}
        if ctype not in allowed_pdf_ct and not body.startswith(_PDF_MAGIC):
            return RoutedDocument(
                response_kind=ResponseKind.PDF,
                text="",
                status_code=status,
                success=False,
                failure_category=FailureCategory.FORMAT_MISMATCH,
                operator_summary="Content-Type does not match PDF body.",
                declared_content_type=ctype,
            )
        try:
            text = extract_pdf_text(body)
        except DirectDocumentExtractError as exc:
            return RoutedDocument(
                response_kind=ResponseKind.PDF,
                text="",
                status_code=status,
                success=False,
                failure_category=exc.category,
                operator_summary=str(exc),
                declared_content_type=ctype,
            )
        return RoutedDocument(
            response_kind=ResponseKind.PDF,
            text=text,
            status_code=status,
            success=True,
            failure_category=None,
            operator_summary=None,
            declared_content_type=ctype,
        )

    if ctype is not None and (
        ctype.startswith("text/")
        or ctype in {"application/json", "application/xml", "text/xml"}
    ):
        if _looks_pdf(body, None):
            return RoutedDocument(
                response_kind=ResponseKind.PLAIN_TEXT,
                text="",
                status_code=status,
                success=False,
                failure_category=FailureCategory.FORMAT_MISMATCH,
                operator_summary="Declared text but body looks like a PDF.",
                declared_content_type=ctype,
            )
        charset = _charset_from_ctype(ctype_full)
        try:
            text = decode_plain_text_bytes(body, charset)
        except DirectDocumentExtractError as exc:
            return RoutedDocument(
                response_kind=ResponseKind.PLAIN_TEXT,
                text="",
                status_code=status,
                success=False,
                failure_category=exc.category,
                operator_summary=str(exc),
                declared_content_type=ctype,
            )
        return RoutedDocument(
            response_kind=ResponseKind.PLAIN_TEXT,
            text=text,
            status_code=status,
            success=True,
            failure_category=None,
            operator_summary=None,
            declared_content_type=ctype,
        )

    octet_types = {None, "application/octet-stream", "binary/octet-stream"}
    if ctype in octet_types and body and not _looks_html(body, None):
        if body.startswith(_PDF_MAGIC):
            try:
                text = extract_pdf_text(body)
            except DirectDocumentExtractError as exc:
                return RoutedDocument(
                    response_kind=ResponseKind.PDF,
                    text="",
                    status_code=status,
                    success=False,
                    failure_category=exc.category,
                    operator_summary=str(exc),
                    declared_content_type=ctype,
                )
            return RoutedDocument(
                response_kind=ResponseKind.PDF,
                text=text,
                status_code=status,
                success=True,
                failure_category=None,
                operator_summary=None,
                declared_content_type=ctype,
            )

    return None
