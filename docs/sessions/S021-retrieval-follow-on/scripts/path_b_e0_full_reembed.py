#!/usr/bin/env python3
"""T99.3 Path B — full E0 shadow re-embed of live chunks + optional promote.

Store-backed F41 reembed needs body_text; staging has only 9/49 docs filled.
This ops script re-embeds **existing live chunk texts** with prod Modal E0
(``BAAI/bge-small-en-v1.5``), writes a dry_run shadow rebuild, then promotes.

Does not TRUNCATE. Does not call attach_embeddings / test helpers.

Usage (repo root)::

  set -a && source .env && set +a
  # shadow only (inspect counts first):
  uv run python docs/sessions/S021-retrieval-follow-on/scripts/path_b_e0_full_reembed.py
  # then promote:
  uv run python docs/sessions/S021-retrieval-follow-on/scripts/path_b_e0_full_reembed.py \\
    --promote --rebuild-run-id <uuid>
  # or one-shot:
  uv run python docs/sessions/S021-retrieval-follow-on/scripts/path_b_e0_full_reembed.py --promote
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import cast
from urllib.parse import urlparse
from uuid import UUID

import psycopg
from vecinita_embedding_client import EMBEDDING_DIMENSION, EmbeddingClient

_REPO = Path(__file__).resolve().parents[4]
_OUT = (
    _REPO
    / "docs"
    / "sessions"
    / "S021-retrieval-follow-on"
    / "reports"
    / "path-b-e0-rebuild.json"
)
_E0_MODEL_ID = "BAAI/bge-small-en-v1.5"
_BATCH_DOCS = 8
_EMBED_BATCH = 32


def _assert_staging_db(url: str) -> None:
    host = urlparse(url.replace("postgresql+psycopg://", "postgresql://")).hostname or ""
    if "ondigitalocean.com" not in host:
        msg = f"expected staging DO Postgres, got {host!r}"
        raise RuntimeError(msg)


def _http_json(
    method: str,
    url: str,
    *,
    token: str,
    payload: dict[str, object] | None = None,
) -> dict[str, object]:
    data = None if payload is None else json.dumps(payload).encode()
    req = urllib.request.Request(
        url,
        data=data,
        method=method,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=300) as resp:
            body = resp.read().decode()
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode()
        msg = f"{method} {url} -> {exc.code}: {detail[:800]}"
        raise RuntimeError(msg) from exc
    loaded = json.loads(body) if body else {}
    if not isinstance(loaded, dict):
        msg = f"expected JSON object from {url}"
        raise TypeError(msg)
    return cast("dict[str, object]", loaded)


def load_live_docs(database_url: str) -> list[dict[str, object]]:
    """Group live chunks by document URL for shadow batch upload."""
    _assert_staging_db(database_url)
    by_url: dict[str, list[dict[str, object]]] = {}
    with psycopg.connect(database_url) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT d.url, c.chunk_index, c.text
                FROM documents d
                JOIN chunks c ON c.document_id = d.id
                ORDER BY d.url, c.chunk_index
                """
            )
            for url, chunk_index, text in cur.fetchall():
                by_url.setdefault(str(url), []).append(
                    {"chunk_index": int(chunk_index), "text": str(text)}
                )
    return [{"url": url, "chunks": chunks} for url, chunks in by_url.items()]


def _is_http_url(url: str) -> bool:
    return url.startswith("http://") or url.startswith("https://")


def _vector_literal(values: list[float]) -> str:
    return "[" + ",".join(str(v) for v in values) + "]"


def _embed_docs(
    batch_docs: list[dict[str, object]],
    *,
    embed_client: EmbeddingClient,
    label: str,
) -> None:
    texts: list[str] = []
    owners: list[tuple[int, int]] = []
    for di, doc in enumerate(batch_docs):
        chunks = cast("list[dict[str, object]]", doc["chunks"])
        for ci, chunk in enumerate(chunks):
            texts.append(str(chunk["text"]))
            owners.append((di, ci))
    vectors: list[list[float]] = []
    for t0 in range(0, len(texts), _EMBED_BATCH):
        part = embed_client.embed_batch(texts[t0 : t0 + _EMBED_BATCH])
        vectors.extend(part)
        print(f"  embed {label} texts={min(t0 + len(part), len(texts))}/{len(texts)}")
    if len(vectors) != len(texts):
        msg = f"embed count mismatch: {len(vectors)} != {len(texts)}"
        raise RuntimeError(msg)
    for (di, ci), vec in zip(owners, vectors, strict=True):
        chunks = cast("list[dict[str, object]]", batch_docs[di]["chunks"])
        chunks[ci]["embedding"] = vec


def _shadow_batch_http(
    *,
    write_url: str,
    token: str,
    rebuild_run_id: UUID,
    batch_docs: list[dict[str, object]],
) -> int:
    payload_docs: list[dict[str, object]] = []
    for doc in batch_docs:
        chunks_out = [
            {
                "chunk_index": chunk["chunk_index"],
                "text": chunk["text"],
                "embedding": chunk["embedding"],
            }
            for chunk in cast("list[dict[str, object]]", doc["chunks"])
        ]
        payload_docs.append(
            {
                "url": doc["url"],
                "rebuild_run_id": str(rebuild_run_id),
                "chunks": chunks_out,
            }
        )
    result = _http_json(
        "POST",
        f"{write_url.rstrip('/')}/internal/v1/rebuild/{rebuild_run_id}/shadow/batch",
        token=token,
        payload={"documents": payload_docs},
    )
    return int(result.get("upserted_chunks") or 0)


def _shadow_batch_sql_fixture(
    *,
    database_url: str,
    rebuild_run_id: UUID,
    batch_docs: list[dict[str, object]],
) -> int:
    """Write shadow rows for fixture:// URLs (write API rejects non-http schemes)."""
    upserted = 0
    with psycopg.connect(database_url) as conn:
        with conn.cursor() as cur:
            for doc in batch_docs:
                url = str(doc["url"])
                cur.execute(
                    """
                    SELECT id FROM documents
                    WHERE rtrim(url, '/') = rtrim(%s, '/')
                    """,
                    (url,),
                )
                row = cur.fetchone()
                if row is None:
                    msg = f"document not found for fixture url={url}"
                    raise RuntimeError(msg)
                doc_id = row[0]
                for chunk in cast("list[dict[str, object]]", doc["chunks"]):
                    embedding = cast("list[float]", chunk["embedding"])
                    cur.execute(
                        """
                        INSERT INTO shadow_chunks (
                            rebuild_run_id, document_id, chunk_index, text
                        )
                        VALUES (%s, %s, %s, %s)
                        ON CONFLICT (rebuild_run_id, document_id, chunk_index)
                        DO UPDATE SET text = EXCLUDED.text
                        RETURNING id
                        """,
                        (
                            str(rebuild_run_id),
                            doc_id,
                            int(cast("object", chunk["chunk_index"])),
                            str(chunk["text"]),
                        ),
                    )
                    shadow_chunk_id = cur.fetchone()
                    assert shadow_chunk_id is not None
                    cur.execute(
                        """
                        INSERT INTO shadow_embeddings (shadow_chunk_id, embedding)
                        VALUES (%s, %s::vector)
                        ON CONFLICT (shadow_chunk_id)
                        DO UPDATE SET embedding = EXCLUDED.embedding
                        """,
                        (shadow_chunk_id[0], _vector_literal(embedding)),
                    )
                    upserted += 1
        conn.commit()
    return upserted


def populate_e0_shadow(
    *,
    write_url: str,
    token: str,
    database_url: str,
    embed_client: EmbeddingClient,
) -> UUID:
    """Create rebuild_run and upload E0 shadow embeddings for the full live corpus."""
    created = _http_json(
        "POST",
        f"{write_url.rstrip('/')}/internal/v1/rebuild/runs",
        token=token,
        payload={
            "mode": "reembed",
            "dry_run": True,
            "force": True,
            "status": "running",
            "embedding_model_id": _E0_MODEL_ID,
            "embedding_dim": EMBEDDING_DIMENSION,
            "chunk_size_tokens": 512,
        },
    )
    rebuild_run_id = UUID(str(created["rebuild_run_id"]))
    print(f"rebuild_run_id={rebuild_run_id}")

    docs = load_live_docs(database_url)
    http_docs = [d for d in docs if _is_http_url(str(d["url"]))]
    fixture_docs = [d for d in docs if not _is_http_url(str(d["url"]))]
    n_chunks = sum(len(cast("list[object]", d["chunks"])) for d in docs)
    print(
        f"live_docs={len(docs)} chunks={n_chunks} "
        f"http={len(http_docs)} fixture={len(fixture_docs)}"
    )

    for start in range(0, len(http_docs), _BATCH_DOCS):
        batch_docs = http_docs[start : start + _BATCH_DOCS]
        label = f"http docs={start + 1}-{min(start + _BATCH_DOCS, len(http_docs))}"
        _embed_docs(batch_docs, embed_client=embed_client, label=label)
        upserted = _shadow_batch_http(
            write_url=write_url,
            token=token,
            rebuild_run_id=rebuild_run_id,
            batch_docs=batch_docs,
        )
        print(f"  shadow http upserted={upserted}")

    for start in range(0, len(fixture_docs), _BATCH_DOCS):
        batch_docs = fixture_docs[start : start + _BATCH_DOCS]
        label = f"fixture docs={start + 1}-{min(start + _BATCH_DOCS, len(fixture_docs))}"
        _embed_docs(batch_docs, embed_client=embed_client, label=label)
        upserted = _shadow_batch_sql_fixture(
            database_url=database_url,
            rebuild_run_id=rebuild_run_id,
            batch_docs=batch_docs,
        )
        print(f"  shadow fixture upserted={upserted}")

    _http_json(
        "PATCH",
        f"{write_url.rstrip('/')}/internal/v1/rebuild/{rebuild_run_id}",
        token=token,
        payload={"status": "completed"},
    )
    print(f"rebuild_run completed: {rebuild_run_id}")
    return rebuild_run_id


def promote(write_url: str, token: str, rebuild_run_id: UUID) -> dict[str, object]:
    """Promote completed shadow rebuild to live."""
    result = _http_json(
        "POST",
        f"{write_url.rstrip('/')}/internal/v1/rebuild/{rebuild_run_id}/promote",
        token=token,
        payload={},
    )
    print(
        "promoted="
        f"{result.get('promoted')} docs={result.get('documents_promoted')} "
        f"chunks={result.get('chunks_promoted')}"
    )
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--promote",
        action="store_true",
        help="Promote after populate (or promote existing --rebuild-run-id)",
    )
    parser.add_argument(
        "--rebuild-run-id",
        type=str,
        default="",
        help="Skip populate; promote this completed rebuild_run_id",
    )
    parser.add_argument(
        "--populate-only",
        action="store_true",
        help="Write shadow only (default when --promote omitted)",
    )
    args = parser.parse_args()

    database_url = os.environ.get("DATABASE_URL", "")
    write_url = os.environ.get("VECINITA_STAGING_WRITE_URL", "") or os.environ.get(
        "VECINITA_WRITE_URL", ""
    )
    token = os.environ.get("VECINITA_INTERNAL_API_KEY", "")
    if not database_url or not write_url or not token:
        print(
            "ERROR: need DATABASE_URL, VECINITA_STAGING_WRITE_URL, VECINITA_INTERNAL_API_KEY",
            file=sys.stderr,
        )
        return 1
    _assert_staging_db(database_url)

    report: dict[str, object] = {
        "model_id": _E0_MODEL_ID,
        "embedding_dim": EMBEDDING_DIMENSION,
    }

    rebuild_run_id: UUID | None = None
    if args.rebuild_run_id:
        rebuild_run_id = UUID(args.rebuild_run_id)
        report["rebuild_run_id"] = str(rebuild_run_id)
        report["populate_skipped"] = True
    else:
        embed_client = EmbeddingClient()
        try:
            rebuild_run_id = populate_e0_shadow(
                write_url=write_url,
                token=token,
                database_url=database_url,
                embed_client=embed_client,
            )
        finally:
            embed_client.close()
        report["rebuild_run_id"] = str(rebuild_run_id)
        report["populate_skipped"] = False

    if args.promote and not args.populate_only:
        assert rebuild_run_id is not None
        report["promote"] = promote(write_url, token, rebuild_run_id)
    else:
        report["promote"] = None
        print("shadow ready — re-run with --promote --rebuild-run-id", rebuild_run_id)

    _OUT.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {_OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
