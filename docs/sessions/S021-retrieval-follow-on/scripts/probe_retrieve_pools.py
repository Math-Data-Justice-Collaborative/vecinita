#!/usr/bin/env python3
"""Read-only staging probe for F46 empty retrieve (T99.2).

Does NOT truncate, seed, or mutate corpus. Requires DATABASE_URL + embed URL.

Usage (repo root)::

  set -a && source .env && set +a
  uv run python docs/sessions/S021-retrieval-follow-on/scripts/probe_retrieve_pools.py
"""

from __future__ import annotations

import json
import os
import sys
from collections import Counter
from pathlib import Path
from urllib.parse import urlparse

from sqlalchemy import create_engine, text
from vecinita_embedding_client import EmbeddingClient
from vecinita_eval.golden import load_golden_rows
from vecinita_rag.retriever import CorpusPgvectorRetriever

_REPO = Path(__file__).resolve().parents[4]
_FIXTURE = _REPO / "data" / "fixtures" / "eval" / "qa_pairs_staging.json"
_OUT = (
    _REPO
    / "docs"
    / "sessions"
    / "S021-retrieval-follow-on"
    / "reports"
    / "probe-retrieve-pools.json"
)


def _host(database_url: str) -> str:
    normalized = database_url.replace("postgresql+psycopg://", "postgresql://")
    return urlparse(normalized).hostname or ""


def main() -> int:
    database_url = os.environ.get("DATABASE_URL", "")
    if not database_url:
        print("ERROR: DATABASE_URL unset", file=sys.stderr)
        return 1
    host = _host(database_url)
    print(f"==> host={host}")
    if not host.endswith(".ondigitalocean.com"):
        print("WARN: host is not DO managed staging; continuing read-only")

    min_score = float(os.environ.get("SPIKE_MIN_SCORE", "0.2"))
    retrieve_n = int(os.environ.get("SPIKE_RETRIEVE_N", "20"))
    sample_n = int(os.environ.get("PROBE_SAMPLE_N", "8"))

    engine = create_engine(database_url)
    with engine.connect() as conn:
        docs = int(conn.execute(text("SELECT COUNT(*) FROM documents")).scalar_one())
        chunks = int(conn.execute(text("SELECT COUNT(*) FROM chunks")).scalar_one())
        embeds = int(conn.execute(text("SELECT COUNT(*) FROM embeddings")).scalar_one())
        dim_row = conn.execute(
            text(
                """
                SELECT vector_dims(embedding) AS dim
                FROM embeddings
                LIMIT 1
                """
            )
        ).first()
        embed_dim = int(dim_row[0]) if dim_row is not None else None
        urls = {
            str(r[0])
            for r in conn.execute(text("SELECT url FROM documents WHERE url IS NOT NULL")).all()
        }
    engine.dispose()

    rows = load_golden_rows(fixture_path=_FIXTURE)[:sample_n]
    expected_urls = {row.expected_doc_url for row in rows if row.expected_doc_url}
    missing_urls = sorted(u for u in expected_urls if u not in urls)

    print(f"==> corpus docs={docs} chunks={chunks} embeddings={embeds} dim={embed_dim}")
    print(f"==> golden sample={len(rows)} missing_expected_urls={len(missing_urls)}")
    for url in missing_urls[:10]:
        print(f"    missing: {url}")

    embed = EmbeddingClient(timeout=120.0)
    probe_vec = embed.embed("housing rights rhode island")
    print(f"==> live embed dim={len(probe_vec)}")

    retriever = CorpusPgvectorRetriever(
        embed_fn=embed.embed,
        database_url=database_url,
        top_k=retrieve_n,
        score_threshold=min_score,
    )
    retriever_zero = CorpusPgvectorRetriever(
        embed_fn=embed.embed,
        database_url=database_url,
        top_k=retrieve_n,
        score_threshold=0.0,
    )

    pools: list[dict[str, object]] = []
    empty_at_02 = 0
    empty_at_00 = 0
    for row in rows:
        pool_02 = retriever.retrieve_chunks(row.question)
        pool_00 = retriever_zero.retrieve_chunks(row.question)
        if not pool_02:
            empty_at_02 += 1
        if not pool_00:
            empty_at_00 += 1
        top = pool_00[0] if pool_00 else None
        pools.append(
            {
                "id": row.id,
                "locale": row.locale,
                "pool_min_0_2": len(pool_02),
                "pool_min_0_0": len(pool_00),
                "top_score": top.score if top is not None else None,
                "top_url": top.url if top is not None else None,
            }
        )
        print(
            f"    {row.id}/{row.locale}: pool@0.2={len(pool_02)} "
            f"pool@0.0={len(pool_00)} top={top.score if top else None}"
        )

    sizes = Counter(int(p["pool_min_0_2"]) for p in pools)
    report = {
        "host": host,
        "docs": docs,
        "chunks": chunks,
        "embeddings": embeds,
        "corpus_embed_dim": embed_dim,
        "live_embed_dim": len(probe_vec),
        "dim_match": embed_dim == len(probe_vec) if embed_dim is not None else None,
        "min_score": min_score,
        "retrieve_n": retrieve_n,
        "sample_n": len(rows),
        "missing_expected_urls": missing_urls,
        "empty_rows_min_0_2": empty_at_02,
        "empty_rows_min_0_0": empty_at_00,
        "pool_size_histogram_min_0_2": dict(sizes),
        "rows": pools,
    }
    _OUT.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"==> wrote {_OUT}")
    print(
        f"==> summary empty@0.2={empty_at_02}/{len(rows)} "
        f"empty@0.0={empty_at_00}/{len(rows)} dim_match={report['dim_match']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
