"""BUG-2026-09-03 — Drive PDF without application/pdf must not yield NUL body_text.

[Spec: docs/bug-reports/BUG-2026-09-03-drive-pdf-nul-body.md]
[Corpus: feature-list.md §F59 §F76]
"""

from __future__ import annotations

from pathlib import Path

import httpx
import pytest
from vecinita_ingest.drive import DriveFetchError
from vecinita_ingest.scrape import fetch_url, scrape_headers

_FIXTURES = Path(__file__).resolve().parents[2] / "data" / "fixtures" / "ingest"
_DRIVE_VIEW = "https://drive.google.com/file/d/FILEID/view"


def test_bug_2026_09_03_drive_pdf_octet_stream_extracts_text_not_binary() -> None:
    """Drive download with octet-stream + %PDF magic must extract text (no NULs)."""
    text_pdf = (_FIXTURES / "sample-text.pdf").read_bytes()
    assert b"\x00" in text_pdf or text_pdf.startswith(b"%PDF")

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
    doc = fetch_url(_DRIVE_VIEW, client=client)
    assert "Hello PDF" in doc.text
    assert "\x00" not in doc.text
    assert not doc.text.startswith("%PDF")
    assert "endobj" not in doc.text
    assert "startxref" not in doc.text


def test_bug_2026_09_03_drive_pdf_octet_stream_empty_soft_fails() -> None:
    """Empty PDF via octet-stream still surfaces drive_unsupported."""
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
