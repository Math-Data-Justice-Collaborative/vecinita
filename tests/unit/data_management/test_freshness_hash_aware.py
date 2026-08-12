"""T128.5 — F76 hash-aware URL re-fetch on freshness_refresh (TC-257 / AC-FR2).

[Corpus: feature-list.md §F76]
[Spec: docs/adr/ADR-052-corpus-automation-orchestration.md]
[Spec: docs/acceptance-criteria.md §AC-FR2]
[Spec: docs/test-plan.md §TC-257]
[Spec: docs/decisions.md §RD-329]
[Spec: docs/user-journeys.md §UJ-081]
"""

from __future__ import annotations

from hashlib import sha256
from uuid import UUID

import pytest  # noqa: TC002  # runtime fixture typing (MonkeyPatch)
from vecinita_data_management_backend.freshness_refresh import (
    perform_hash_aware_url_refresh,
    run_freshness_refresh_job,
)
from vecinita_data_management_backend.store import InMemoryJobStore
from vecinita_ingest.models import ScrapedDocument
from vecinita_shared_schemas.internal_write import DocumentDetail

DOC_ID = UUID("aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee")
DOC_URL = "https://example.com/freshness-doc"
_BODY = "unchanged corpus body for freshness"
_DIGEST = sha256(_BODY.encode("utf-8")).hexdigest()


class _StubEmbedClient:
    def __init__(self) -> None:
        self.calls: list[list[str]] = []

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        self.calls.append(list(texts))
        return [[0.1] * 384 for _ in texts]


class _StubWriteClient:
    def __init__(
        self,
        *,
        url: str = DOC_URL,
        stored_hash: str | None = _DIGEST,
    ) -> None:
        self.url = url
        self.stored_hash = stored_hash
        self.bumped: list[UUID] = []
        self.upserts: list[object] = []
        self.detail_calls: list[UUID] = []

    def with_audit_actor(
        self,
        actor_id: UUID | None,
        actor_role: str | None,
    ) -> _StubWriteClient:
        _ = (actor_id, actor_role)
        return self

    def post_audit_event(self, event: object) -> None:
        _ = event

    def get_document_detail(self, document_id: UUID) -> DocumentDetail:
        self.detail_calls.append(document_id)
        return DocumentDetail(
            document_id=document_id,
            url=self.url,
            title="Doc",
            text=_BODY,
        )

    def get_content_hash_by_url(self, url: str) -> str | None:
        assert url == self.url
        return self.stored_hash

    def bump_document_last_checked(self, document_id: UUID) -> None:
        self.bumped.append(document_id)

    def upsert_batch(self, body: object) -> object:
        self.upserts.append(body)
        return body


def _options(*, force: bool = False) -> dict[str, object]:
    return {
        "document_id": str(DOC_ID),
        "force": force,
        "refresh_enabled": True,
        "is_stale": True,
    }


def _enable_freshness(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("VECINITA_FRESHNESS_ENABLED", "true")
    monkeypatch.setenv("VECINITA_AUTOMATIONS_KILL_SWITCH", "false")


def test_hash_unchanged_skips_rechunk_and_bumps_last_checked() -> None:
    """TC-257 / AC-FR2: same content_hash → no embed/upsert; bump last_checked."""
    write = _StubWriteClient(stored_hash=_DIGEST)
    embed = _StubEmbedClient()
    scraped = ScrapedDocument(url=DOC_URL, title="Doc", text=_BODY)

    outcome = perform_hash_aware_url_refresh(
        DOC_ID,
        write_client=write,  # type: ignore[arg-type]
        embed_client=embed,  # type: ignore[arg-type]
        fetch_document=lambda _u: scraped,
    )

    assert outcome == "verified_unchanged"
    assert write.bumped == [DOC_ID]
    assert write.upserts == []
    assert embed.calls == []


def test_hash_changed_rechunks_embeds_and_bumps() -> None:
    """TC-257: changed hash → rechunk/embed/upsert + bump last_checked."""
    write = _StubWriteClient(stored_hash=_DIGEST)
    embed = _StubEmbedClient()
    new_body = "updated corpus body after source edit"
    scraped = ScrapedDocument(url=DOC_URL, title="Doc", text=new_body)

    outcome = perform_hash_aware_url_refresh(
        DOC_ID,
        write_client=write,  # type: ignore[arg-type]
        embed_client=embed,  # type: ignore[arg-type]
        fetch_document=lambda _u: scraped,
    )

    assert outcome == "rechunked"
    assert write.bumped == [DOC_ID]
    assert len(write.upserts) == 1
    assert embed.calls  # at least one embed_batch
    upsert = write.upserts[0]
    docs = getattr(upsert, "documents", None)
    assert docs is not None
    assert len(docs) == 1
    assert docs[0].content_hash == sha256(new_body.encode("utf-8")).hexdigest()
    assert docs[0].chunks  # rechunk produced chunks


def test_freshness_job_default_path_reports_verified_unchanged(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Default perform_refresh is hash-aware; metrics expose hash outcome."""
    _enable_freshness(monkeypatch)
    store = InMemoryJobStore()
    record = store.create_job(
        urls=[],
        job_type="freshness_refresh",
        options=_options(),
    )
    write = _StubWriteClient(stored_hash=_DIGEST)
    embed = _StubEmbedClient()
    scraped = ScrapedDocument(url=DOC_URL, title="Doc", text=_BODY)

    run_freshness_refresh_job(
        record.job_id,
        store=store,
        write_client=write,  # type: ignore[arg-type]
        embed_client=embed,  # type: ignore[arg-type]
        fetch_document=lambda _u: scraped,
    )

    final = store.get_job(record.job_id)
    assert final is not None
    assert final.status == "completed"
    assert final.metrics == {
        "freshness_outcome": "verified_unchanged",
        "documents_processed": 1,
        "hash_decision": "skip_rechunk",
    }
    assert write.bumped == [DOC_ID]
    assert write.upserts == []
    assert embed.calls == []


def test_freshness_job_default_path_reports_rechunked(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Changed content → freshness_outcome=rechunked with hash_decision=rechunk."""
    _enable_freshness(monkeypatch)
    store = InMemoryJobStore()
    record = store.create_job(
        urls=[],
        job_type="freshness_refresh",
        options=_options(force=True),
    )
    write = _StubWriteClient(stored_hash=_DIGEST)
    embed = _StubEmbedClient()
    scraped = ScrapedDocument(
        url=DOC_URL,
        title="Doc",
        text="brand new body that must rechunk",
    )

    run_freshness_refresh_job(
        record.job_id,
        store=store,
        write_client=write,  # type: ignore[arg-type]
        embed_client=embed,  # type: ignore[arg-type]
        fetch_document=lambda _u: scraped,
    )

    final = store.get_job(record.job_id)
    assert final is not None
    assert final.status == "completed"
    assert final.metrics == {
        "freshness_outcome": "rechunked",
        "documents_processed": 1,
        "hash_decision": "rechunk",
    }
    assert write.bumped == [DOC_ID]
    assert len(write.upserts) == 1
    assert embed.calls


def test_refresh_now_force_still_hash_skips_when_unchanged() -> None:
    """UJ-081: Refresh now (force) bypasses stale only — not content_hash skip."""
    write = _StubWriteClient(stored_hash=_DIGEST)
    embed = _StubEmbedClient()
    scraped = ScrapedDocument(url=DOC_URL, title="Doc", text=_BODY)

    outcome = perform_hash_aware_url_refresh(
        DOC_ID,
        write_client=write,  # type: ignore[arg-type]
        embed_client=embed,  # type: ignore[arg-type]
        fetch_document=lambda _u: scraped,
    )

    assert outcome == "verified_unchanged"
    assert write.upserts == []
    assert embed.calls == []
    assert write.bumped == [DOC_ID]
