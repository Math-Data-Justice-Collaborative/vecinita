"""EV-016 #159 offline dense-retrieval ablation (E0/E1/E2) on staging corpus.

Loads chunk texts from DATABASE_URL (read-only), embeds via Modal
``spike_embed_models_modal.MultiEmbedSpike``, scores golden hit@k by locale.

Usage (from repo root, with .env + Modal auth)::

  uv run python docs/sessions/S019-retrieval-quality/scripts/spike_embed_retrieval.py
"""

from __future__ import annotations

import json
import math
import os
import sys
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Literal
from urllib.parse import urlparse

_REPO = Path(__file__).resolve().parents[4]
_FIXTURE = _REPO / "data" / "fixtures" / "eval" / "qa_pairs_staging.json"
_OUT_DIR = (
    _REPO
    / "docs"
    / "sessions"
    / "S019-retrieval-quality"
    / "reports"
    / "eval-experiments"
)
_MODAL_SCRIPT = Path(__file__).resolve().parent / "spike_embed_models_modal.py"

CellId = Literal["E0", "E1", "E2"]
CELLS: tuple[CellId, ...] = ("E0", "E1", "E2")
TOP_K = 5
BATCH = 64


@dataclass(frozen=True, slots=True)
class CorpusChunk:
    """One staging chunk used for offline dense retrieval."""

    chunk_id: str
    url: str
    language: str
    text: str


@dataclass(frozen=True, slots=True)
class GoldenHitCase:
    """Scored golden hit case (retrieval_expectation=hit)."""

    case_id: str
    locale: str
    question: str
    expected_doc_url: str


def cosine_similarity(a: list[float], b: list[float]) -> float:
    """Cosine similarity for equal-length vectors."""
    if len(a) != len(b):
        msg = f"dim mismatch {len(a)} vs {len(b)}"
        raise ValueError(msg)
    dot = 0.0
    na = 0.0
    nb = 0.0
    for x, y in zip(a, b, strict=True):
        dot += x * y
        na += x * x
        nb += y * y
    if na <= 0.0 or nb <= 0.0:
        return 0.0
    return dot / math.sqrt(na * nb)


def top_k_urls(
    query_vec: list[float],
    chunk_vecs: list[list[float]],
    chunks: list[CorpusChunk],
    *,
    top_k: int,
) -> list[str]:
    """Return distinct document URLs for the top_k most similar chunks."""
    scored = [
        (cosine_similarity(query_vec, vec), chunks[i].url)
        for i, vec in enumerate(chunk_vecs)
    ]
    scored.sort(key=lambda item: item[0], reverse=True)
    urls: list[str] = []
    seen: set[str] = set()
    for _score, url in scored:
        if url in seen:
            continue
        seen.add(url)
        urls.append(url)
        if len(urls) >= top_k:
            break
    return urls


def url_match(expected: str, retrieved: list[str]) -> bool:
    """Match expected URL allowing trailing-slash variants."""
    exp = expected.rstrip("/")
    return any(item.rstrip("/") == exp for item in retrieved)


def summarize_hits(
    rows: list[tuple[GoldenHitCase, bool]],
) -> dict[str, float | int]:
    """Aggregate hit rate overall and by locale."""
    if not rows:
        return {"n": 0, "hit_rate": 0.0, "en_n": 0, "en_hit": 0.0, "es_n": 0, "es_hit": 0.0}
    en = [(case, ok) for case, ok in rows if case.locale == "en"]
    es = [(case, ok) for case, ok in rows if case.locale == "es"]

    def _rate(items: list[tuple[GoldenHitCase, bool]]) -> float:
        if not items:
            return 0.0
        return sum(1 for _c, ok in items if ok) / len(items)

    return {
        "n": len(rows),
        "hit_rate": _rate(rows),
        "en_n": len(en),
        "en_hit": _rate(en),
        "es_n": len(es),
        "es_hit": _rate(es),
    }


def _assert_staging_db(url: str) -> None:
    host = urlparse(url).hostname or ""
    if "ondigitalocean.com" not in host:
        msg = f"expected staging DO Postgres host, got {host!r}"
        raise RuntimeError(msg)


def load_corpus(database_url: str) -> list[CorpusChunk]:
    """Read-only load of live chunks + document URL/language."""
    import psycopg

    _assert_staging_db(database_url)
    out: list[CorpusChunk] = []
    with psycopg.connect(database_url) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT c.id::text, d.url, coalesce(d.language, ''), c.text
                FROM chunks c
                JOIN documents d ON d.id = c.document_id
                ORDER BY d.url, c.chunk_index
                """
            )
            for chunk_id, doc_url, language, text in cur.fetchall():
                out.append(
                    CorpusChunk(
                        chunk_id=str(chunk_id),
                        url=str(doc_url),
                        language=str(language),
                        text=str(text),
                    )
                )
    return out


def load_hit_cases(fixture_path: Path) -> list[GoldenHitCase]:
    """Load hit-expectation golden rows with an expected URL."""
    raw = json.loads(fixture_path.read_text(encoding="utf-8"))
    if not isinstance(raw, list):
        msg = f"expected JSON array in {fixture_path}"
        raise TypeError(msg)
    cases: list[GoldenHitCase] = []
    for item in raw:
        if not isinstance(item, dict):
            continue
        if item.get("retrieval_expectation") != "hit":
            continue
        expected = item.get("expected_doc_url")
        question = item.get("question")
        case_id = item.get("id")
        locale = item.get("locale")
        if not (
            isinstance(expected, str)
            and isinstance(question, str)
            and isinstance(case_id, str)
            and isinstance(locale, str)
        ):
            continue
        cases.append(
            GoldenHitCase(
                case_id=case_id,
                locale=locale,
                question=question,
                expected_doc_url=expected,
            )
        )
    return cases


def _embed_all(
    cell_id: CellId,
    texts: list[str],
    *,
    remote: object,
    for_query: bool = False,
) -> list[list[float]]:
    vectors: list[list[float]] = []
    for start in range(0, len(texts), BATCH):
        batch = texts[start : start + BATCH]
        part = remote.embed_batch.remote(  # type: ignore[attr-defined]
            cell_id,
            batch,
            for_query=for_query,
        )
        assert isinstance(part, list)
        vectors.extend(part)
    return vectors


def main() -> int:
    """Run E0/E1/E2 offline retrieval ablation and write JSON report."""
    database_url = os.environ.get("DATABASE_URL", "").strip()
    if not database_url:
        print("DATABASE_URL required", file=sys.stderr)
        return 2

    sys.path.insert(0, str(_MODAL_SCRIPT.parent))
    import modal

    from spike_embed_models_modal import MultiEmbedSpike  # noqa: PLC0415

    chunks = load_corpus(database_url)
    cases = load_hit_cases(_FIXTURE)
    print(f"corpus_chunks={len(chunks)} golden_hits={len(cases)}")
    if not chunks or not cases:
        return 1

    MultiEmbed = modal.Cls.from_name("vecinita-spike-embed-models", "MultiEmbedSpike")
    # Deploy app if needed
    print("ensuring Modal app deployed…")
    import subprocess

    subprocess.run(
        ["modal", "deploy", str(_MODAL_SCRIPT)],
        check=True,
        cwd=str(_REPO),
    )
    remote = MultiEmbed()

    report: dict[str, object] = {
        "started_at": datetime.now(UTC).isoformat(),
        "top_k": TOP_K,
        "fixture": str(_FIXTURE),
        "corpus_chunks": len(chunks),
        "golden_hits": len(cases),
        "cells": {},
    }
    chunk_texts = [c.text for c in chunks]
    questions = [c.question for c in cases]

    for cell_id in CELLS:
        print(f"embedding corpus+queries for {cell_id}…")
        chunk_vecs = _embed_all(cell_id, chunk_texts, remote=remote, for_query=False)
        query_vecs = _embed_all(cell_id, questions, remote=remote, for_query=True)

        rows: list[tuple[GoldenHitCase, bool]] = []
        detail: list[dict[str, object]] = []
        for case, qvec in zip(cases, query_vecs, strict=True):
            urls = top_k_urls(qvec, chunk_vecs, chunks, top_k=TOP_K)
            ok = url_match(case.expected_doc_url, urls)
            rows.append((case, ok))
            detail.append(
                {
                    "id": case.case_id,
                    "locale": case.locale,
                    "hit": ok,
                    "expected": case.expected_doc_url,
                    "retrieved": urls,
                }
            )
        summary = summarize_hits(rows)
        print(cell_id, summary)
        report["cells"][cell_id] = {"summary": summary, "rows": detail}

    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    out = _OUT_DIR / f"{stamp}_embed-sweep.json"
    _OUT_DIR.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print("wrote", out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
