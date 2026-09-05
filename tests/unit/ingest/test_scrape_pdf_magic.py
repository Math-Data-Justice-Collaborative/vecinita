"""Unit coverage for PDF magic sniff / octet-stream extract (BUG-2026-09-03).

Bug regression also lives in tests/bugs/; CI coverage gate uses tests/unit only.
"""

from __future__ import annotations

from pathlib import Path

import httpx
import pytest
from vecinita_ingest.drive import DriveFetchError
from vecinita_ingest.scrape import ScrapeFetchError, fetch_url, scrape_headers

_FIXTURES = Path(__file__).resolve().parents[3] / "data" / "fixtures" / "ingest"


def test_drive_pdf_octet_stream_extracts_text() -> None:
    """Drive download with octet-stream + %PDF magic extracts text."""
    text_pdf = (_FIXTURES / "sample-text.pdf").read_bytes()

    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            content=text_pdf,
            headers={"content-type": "application/octet-stream"},
        )

    client = httpx.Client(
        transport=httpx.MockTransport(handler),
        headers=scrape_headers(),
        follow_redirects=True,
    )
    doc = fetch_url("https://drive.google.com/file/d/FILEID/view", client=client)
    assert "Hello PDF" in doc.text
    assert not doc.text.startswith("%PDF")


def test_drive_pdf_octet_stream_empty_raises_drive_unsupported() -> None:
    """Empty Drive PDF via octet-stream → drive_unsupported."""
    empty_pdf = (_FIXTURES / "empty.pdf").read_bytes()

    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            content=empty_pdf,
            headers={"content-type": "application/octet-stream"},
        )

    client = httpx.Client(
        transport=httpx.MockTransport(handler),
        headers=scrape_headers(),
        follow_redirects=True,
    )
    with pytest.raises(DriveFetchError) as exc_info:
        _ = fetch_url("https://drive.google.com/file/d/EMPTY/view", client=client)
    assert exc_info.value.error_code == "drive_unsupported"


def test_public_pdf_url_suffix_extracts_text() -> None:
    """Non-Drive .pdf URL suffix triggers extract without application/pdf."""
    text_pdf = (_FIXTURES / "sample-text.pdf").read_bytes()

    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            content=text_pdf,
            headers={"content-type": "application/octet-stream"},
        )

    client = httpx.Client(
        transport=httpx.MockTransport(handler),
        headers=scrape_headers(),
        follow_redirects=True,
    )
    doc = fetch_url("https://example.com/resources/guide.pdf?dl=1", client=client)
    assert "Hello PDF" in doc.text


def test_public_empty_pdf_raises_pdf_extract_failed() -> None:
    """Non-Drive empty PDF → pdf_extract_failed."""
    empty_pdf = (_FIXTURES / "empty.pdf").read_bytes()

    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            content=b"   " + empty_pdf,
            headers={"content-type": "text/plain"},
        )

    client = httpx.Client(
        transport=httpx.MockTransport(handler),
        headers=scrape_headers(),
        follow_redirects=True,
    )
    with pytest.raises(ScrapeFetchError) as exc_info:
        _ = fetch_url("https://example.com/brochure", client=client)
    assert exc_info.value.error_code == "pdf_extract_failed"
