"""Hotfix #235 / #243 — Drive shells, User-Agent, scrape soft-fail (HF-20260821)."""

from __future__ import annotations

from pathlib import Path
from typing import Never, cast

import httpx
import pytest
from vecinita_data_management_backend.pipeline import run_ingest_job
from vecinita_data_management_backend.store import InMemoryJobStore
from vecinita_ingest.drive import (
    DriveFetchError,
    is_drive_auth_shell,
    is_google_drive_url,
    rewrite_drive_fetch_url,
)
from vecinita_ingest.models import ScrapedDocument
from vecinita_ingest.scrape import (
    DEFAULT_SCRAPE_USER_AGENT,
    fetch_url,
    resolve_scrape_user_agent,
    scrape_headers,
)
from vecinita_tagging.vocabulary import SeedTag

_VOCAB = [
    SeedTag(slug="housing", label_en="Housing", label_es="Vivienda"),
]
_BODY = (
    "<html><head><title>OK</title></head>" +
    "<body><p>Good community resource text for chunking windows.</p></body></html>"
)


class _StubEmbedClient:
    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        return [[0.01] * 384 for _ in texts]


class _RecordingWriteClient:
    def __init__(self) -> None:
        self.last_batch: object | None = None

    def upsert_batch(self, body: object) -> None:
        self.last_batch = body

    def get_content_hash_by_url(self, url: str) -> str | None:
        _ = url
        return None


def test_scrape_headers_include_browser_user_agent() -> None:
    """#243: documented browser-like User-Agent is sent on HTML fetch."""
    headers = scrape_headers()
    assert "User-Agent" in headers
    assert headers["User-Agent"] == DEFAULT_SCRAPE_USER_AGENT
    assert "Mozilla" in headers["User-Agent"]


def test_fetch_url_sends_user_agent_header() -> None:
    """#243: owned httpx client GET includes User-Agent."""
    seen: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        ua = cast("str | None", request.headers.get("user-agent"))
        assert ua is not None
        seen.append(ua)
        return httpx.Response(200, text=_BODY)

    transport = httpx.MockTransport(handler)
    client = httpx.Client(
        transport=transport,
        headers=scrape_headers(),
        follow_redirects=True,
    )
    doc = fetch_url("https://example.com/page", client=client)
    assert doc.title == "OK"
    assert seen == [DEFAULT_SCRAPE_USER_AGENT]


def test_is_google_drive_url_detects_hosts() -> None:
    """#235: Drive / Docs / Sheets hosts are detected."""
    assert is_google_drive_url("https://drive.google.com/file/d/abc123/view")
    assert is_google_drive_url("https://docs.google.com/document/d/abc/edit")
    assert is_google_drive_url("https://docs.google.com/spreadsheets/d/abc/edit")
    assert not is_google_drive_url("https://example.com/drive")


def test_is_drive_auth_shell_detects_loading_sign_in() -> None:
    """#235: Loading… Sign in (and equivalents) are auth shells."""
    assert is_drive_auth_shell("Loading… Sign in")
    assert is_drive_auth_shell("Loading... Sign in to continue")
    assert is_drive_auth_shell("Sign in\nLoading")
    assert not is_drive_auth_shell(
        "Food pantry hours Monday to Friday at the community center downtown."
    )


def test_rewrite_drive_fetch_url_public_export() -> None:
    """#235: public Docs/Sheets/Drive file URLs rewrite to export/download."""
    assert (
        rewrite_drive_fetch_url("https://docs.google.com/document/d/DOCID/edit")
        == "https://docs.google.com/document/d/DOCID/export?format=txt"
    )
    assert (
        rewrite_drive_fetch_url("https://docs.google.com/spreadsheets/d/SHEETID/edit#gid=0")
        == "https://docs.google.com/spreadsheets/d/SHEETID/export?format=csv"
    )
    assert (
        rewrite_drive_fetch_url("https://drive.google.com/file/d/FILEID/view?usp=sharing")
        == "https://drive.google.com/uc?export=download&id=FILEID"
    )


def test_fetch_url_drive_auth_shell_raises_drive_fetch_error() -> None:
    """#235: Drive view HTML that is only Loading/Sign in fails loud (no junk doc)."""

    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            text=(
                "<html><head><title>Google Drive</title></head>" +
                "<body><p>Loading…</p><p>Sign in</p></body></html>"
            ),
        )

    client = httpx.Client(
        transport=httpx.MockTransport(handler),
        headers=scrape_headers(),
        follow_redirects=True,
    )
    with pytest.raises(DriveFetchError, match=r"(?i)auth|sign.?in|loading") as exc_info:
        _ = fetch_url("https://drive.google.com/file/d/abc123/view", client=client)
    assert exc_info.value.error_code == "drive_auth_required"


def test_fetch_url_drive_docs_export_success() -> None:
    """#235: public Docs export path returns real text (mocked)."""

    def handler(request: httpx.Request) -> httpx.Response:
        assert "/export" in str(request.url)
        return httpx.Response(
            200,
            text="Pantry hours: Monday 9am-5pm. Bring an ID if you have one.",
            headers={"content-type": "text/plain; charset=utf-8"},
        )

    client = httpx.Client(
        transport=httpx.MockTransport(handler),
        headers=scrape_headers(),
        follow_redirects=True,
    )
    doc = fetch_url("https://docs.google.com/document/d/DOCID/view", client=client)
    assert "Pantry hours" in doc.text
    assert "Sign in" not in doc.text


def test_run_ingest_job_non_crawl_soft_fails_url_errors() -> None:
    """#243: multi-URL non-crawl soft-fails per URL; completes when ≥1 succeeds."""

    def fetch_doc(url: str) -> ScrapedDocument:
        if "blocked" in url:
            msg = "403 Forbidden"
            raise httpx.HTTPStatusError(
                msg,
                request=httpx.Request("GET", url),
                response=httpx.Response(403, request=httpx.Request("GET", url)),
            )
        return ScrapedDocument(url=url, title="ok", text=_BODY)

    store = InMemoryJobStore()
    write_client = _RecordingWriteClient()
    record = store.create_job(
        urls=[
            "https://example.com/blocked",
            "https://example.com/good",
        ],
        options={"chunk_size_tokens": 64},
    )

    run_ingest_job(
        record.job_id,
        store=store,
        embed_client=_StubEmbedClient(),  # type: ignore[arg-type]
        write_client=write_client,  # type: ignore[arg-type]
        fetch_document=fetch_doc,
        tag_vocabulary=_VOCAB,
    )

    updated = store.get_job(record.job_id)
    assert updated is not None
    assert updated.status == "completed"
    assert updated.metrics is not None
    assert updated.metrics.get("urls_failed_scrape") == 1
    failures_raw = updated.metrics.get("url_failures")
    assert isinstance(failures_raw, list)
    typed_failures = cast("list[object]", failures_raw)
    assert len(typed_failures) == 1
    first_raw = typed_failures[0]
    assert isinstance(first_raw, dict)
    first_map = cast("dict[str, object]", first_raw)
    url_value = first_map.get("url")
    assert isinstance(url_value, str)
    assert "blocked" in url_value
    assert write_client.last_batch is not None


def test_run_ingest_job_all_urls_fail_surfaces_drive_error_code() -> None:
    """#235/#243: all-URL failure keeps operator-readable Drive error_code."""

    def fetch_doc(url: str) -> Never:
        _ = url
        msg = "Google Drive returned an auth/loading shell"
        raise DriveFetchError(msg, error_code="drive_auth_required")

    store = InMemoryJobStore()
    record = store.create_job(
        urls=["https://drive.google.com/file/d/abc/view"],
        options={"chunk_size_tokens": 64},
    )

    with pytest.raises(DriveFetchError):
        run_ingest_job(
            record.job_id,
            store=store,
            embed_client=_StubEmbedClient(),  # type: ignore[arg-type]
            write_client=_RecordingWriteClient(),  # type: ignore[arg-type]
            fetch_document=fetch_doc,
            tag_vocabulary=_VOCAB,
        )

    updated = store.get_job(record.job_id)
    assert updated is not None
    assert updated.status == "failed"
    assert updated.error_code == "drive_auth_required"


def test_is_google_drive_url_rejects_missing_host() -> None:
    """Relative / host-less URLs are not Drive hosts."""
    assert not is_google_drive_url("/file/d/abc/view")
    assert not is_google_drive_url("not-a-url")


def test_is_drive_auth_shell_edge_cases() -> None:
    """Empty, marker-only, and long bodies for shell detection."""
    assert is_drive_auth_shell("   ")
    assert is_drive_auth_shell("Loading")
    assert is_drive_auth_shell("login")
    assert not is_drive_auth_shell("x" * 500)


def test_rewrite_drive_presentation_and_passthrough() -> None:
    """Presentation rewrite + already-export URLs pass through."""
    assert (
        rewrite_drive_fetch_url("https://docs.google.com/presentation/d/PID/edit")
        == "https://docs.google.com/presentation/d/PID/export/txt"
    )
    export = "https://docs.google.com/document/d/DOC/export?format=txt"
    assert rewrite_drive_fetch_url(export) == export
    download = "https://drive.google.com/uc?export=download&id=FILE"
    assert rewrite_drive_fetch_url(download) == download


def test_rewrite_drive_folder_raises_unsupported() -> None:
    """Folder share links are unsupported."""
    with pytest.raises(DriveFetchError) as exc_info:
        _ = rewrite_drive_fetch_url("https://drive.google.com/drive/folders/FOLDERID")
    assert exc_info.value.error_code == "drive_unsupported"


def test_resolve_scrape_user_agent_env_override(monkeypatch: pytest.MonkeyPatch) -> None:
    """VECINITA_SCRAPE_USER_AGENT overrides the browser-like default."""
    monkeypatch.setenv("VECINITA_SCRAPE_USER_AGENT", "CustomBot/9.9")
    assert resolve_scrape_user_agent() == "CustomBot/9.9"
    assert scrape_headers()["User-Agent"] == "CustomBot/9.9"


def test_fetch_url_drive_pdf_success_and_empty() -> None:
    """Drive download PDF path uses extract_pdf_text; empty PDF fails loud."""
    fixtures = Path(__file__).resolve().parents[3] / "data" / "fixtures" / "ingest"
    text_pdf = (fixtures / "sample-text.pdf").read_bytes()
    empty_pdf = (fixtures / "empty.pdf").read_bytes()

    def ok_handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            content=text_pdf,
            headers={"content-type": "application/pdf"},
        )

    client = httpx.Client(
        transport=httpx.MockTransport(ok_handler),
        headers=scrape_headers(),
        follow_redirects=True,
    )
    doc = fetch_url("https://drive.google.com/file/d/FILEID/view", client=client)
    assert "Hello PDF" in doc.text

    def empty_handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            content=empty_pdf,
            headers={"content-type": "application/pdf"},
        )

    empty_client = httpx.Client(
        transport=httpx.MockTransport(empty_handler),
        headers=scrape_headers(),
        follow_redirects=True,
    )
    with pytest.raises(DriveFetchError) as exc_info:
        _ = fetch_url("https://drive.google.com/file/d/EMPTY/view", client=empty_client)
    assert exc_info.value.error_code == "drive_unsupported"


def test_fetch_url_drive_empty_text_export_raises() -> None:
    """Empty text/csv Drive export is treated as an auth/loading shell."""

    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            text="   ",
            headers={"content-type": "text/csv"},
        )

    client = httpx.Client(
        transport=httpx.MockTransport(handler),
        headers=scrape_headers(),
        follow_redirects=True,
    )
    with pytest.raises(DriveFetchError) as exc_info:
        _ = fetch_url("https://docs.google.com/spreadsheets/d/SHEET/edit", client=client)
    assert exc_info.value.error_code == "drive_auth_required"


def test_run_ingest_job_all_urls_fail_generic_error_code() -> None:
    """Non-Drive soft-fail all-URL failure surfaces ValueError error_code."""

    def fetch_doc(url: str) -> Never:
        _ = url
        msg = "403 Forbidden"
        raise RuntimeError(msg)

    store = InMemoryJobStore()
    record = store.create_job(
        urls=["https://example.com/blocked"],
        options={"chunk_size_tokens": 64},
    )

    with pytest.raises(ValueError, match="all URLs failed"):
        run_ingest_job(
            record.job_id,
            store=store,
            embed_client=_StubEmbedClient(),  # type: ignore[arg-type]
            write_client=_RecordingWriteClient(),  # type: ignore[arg-type]
            fetch_document=fetch_doc,
            tag_vocabulary=_VOCAB,
        )

    updated = store.get_job(record.job_id)
    assert updated is not None
    assert updated.status == "failed"
    assert updated.error_code == "ValueError"
    assert updated.metrics is not None
    assert updated.metrics.get("urls_failed_scrape") == 1
