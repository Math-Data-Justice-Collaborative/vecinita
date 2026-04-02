"""ChromaDB storage service for Vecinita.

Centralizes Chroma client-server access and collection operations used by
agent retrieval, scraper ingestion, and gateway admin/documents endpoints.
"""

from __future__ import annotations

import json
import logging
import os
from collections.abc import Iterable
from datetime import datetime, timezone
from typing import Any, cast

import chromadb  # type: ignore[import-not-found]

logger = logging.getLogger(__name__)


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _safe_metadata(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return value
    if isinstance(value, str):
        text = value.strip()
        if not text:
            return {}
        try:
            parsed = json.loads(text)
            if isinstance(parsed, dict):
                return parsed
        except Exception:
            return {}
    return {}


def _safe_tags(value: Any) -> list[str]:
    if isinstance(value, list):
        result: list[str] = []
        for item in value:
            if isinstance(item, str):
                tag = item.strip().lower()
                if tag and tag not in result:
                    result.append(tag)
        return result
    return []


def _distance_to_similarity(distance: float | None) -> float:
    if distance is None:
        return 0.0
    try:
        d = float(distance)
    except Exception:
        return 0.0
    return 1.0 / (1.0 + max(0.0, d))


class ChromaStore:
    def __init__(self) -> None:
        self.host = os.getenv("CHROMA_HOST", "chroma")
        self.port = int(os.getenv("CHROMA_PORT", "8000"))
        self.ssl = os.getenv("CHROMA_SSL", "false").lower() in {"1", "true", "yes"}
        self.chunks_collection = os.getenv("CHROMA_COLLECTION_CHUNKS", "vecinita_chunks")
        self.sources_collection = os.getenv("CHROMA_COLLECTION_SOURCES", "vecinita_sources")
        self.queue_collection = os.getenv("CHROMA_COLLECTION_QUEUE", "vecinita_queue")

        self._client: chromadb.HttpClient | None = None
        self._chunks = None
        self._sources = None
        self._queue = None

    def _get_client(self) -> chromadb.HttpClient:
        if self._client is None:
            self._client = chromadb.HttpClient(host=self.host, port=self.port, ssl=self.ssl)
        return self._client

    def heartbeat(self) -> bool:
        try:
            self._get_client().heartbeat()
            logger.info(
                "Chroma heartbeat OK host=%s port=%s ssl=%s",
                self.host,
                self.port,
                self.ssl,
            )
            return True
        except Exception as exc:
            logger.warning(
                "Chroma heartbeat failed host=%s port=%s ssl=%s error=%s",
                self.host,
                self.port,
                self.ssl,
                exc,
            )
            return False

    def chunks(self):
        if self._chunks is None:
            self._chunks = self._get_client().get_or_create_collection(name=self.chunks_collection)
        return self._chunks

    def sources(self):
        if self._sources is None:
            self._sources = self._get_client().get_or_create_collection(
                name=self.sources_collection
            )
        return self._sources

    def queue(self):
        if self._queue is None:
            self._queue = self._get_client().get_or_create_collection(name=self.queue_collection)
        return self._queue

    def upsert_chunks(self, rows: list[dict[str, Any]]) -> int:
        if not rows:
            return 0

        ids: list[str] = []
        documents: list[str] = []
        embeddings: list[list[float]] = []
        metadatas: list[dict[str, Any]] = []

        for row in rows:
            row_id = str(row.get("id") or "")
            if not row_id:
                continue
            embedding = row.get("embedding")
            if not isinstance(embedding, list):
                continue

            metadata = _safe_metadata(row.get("metadata"))
            metadata.update(
                {
                    "source_url": str(row.get("source_url") or ""),
                    "source_domain": str(row.get("source_domain") or ""),
                    "chunk_index": int(row.get("chunk_index") or 0),
                    "total_chunks": int(row.get("total_chunks") or 0),
                    "chunk_size": int(row.get("chunk_size") or len(str(row.get("content") or ""))),
                    "document_title": str(row.get("document_title") or ""),
                    "updated_at": str(row.get("updated_at") or _now_iso()),
                    "created_at": str(row.get("created_at") or _now_iso()),
                    "processing_status": str(row.get("processing_status") or "completed"),
                    "is_processed": bool(row.get("is_processed", True)),
                }
            )
            safe_tags = _safe_tags(metadata.get("tags"))
            if safe_tags:
                metadata["tags"] = safe_tags
            else:
                metadata.pop("tags", None)

            ids.append(row_id)
            documents.append(str(row.get("content") or ""))
            embeddings.append([float(x) for x in embedding])
            metadatas.append(metadata)

        if not ids:
            return 0

        self.chunks().upsert(
            ids=ids, documents=documents, embeddings=embeddings, metadatas=metadatas
        )
        return len(ids)

    def query_chunks(
        self,
        *,
        query_embedding: list[float],
        n_results: int,
        where: dict[str, Any] | None = None,
        where_document: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        params: dict[str, Any] = {
            "query_embeddings": [query_embedding],
            "n_results": int(n_results),
            "include": ["documents", "metadatas", "distances"],
        }
        if where:
            params["where"] = where
        if where_document:
            params["where_document"] = where_document

        result = self.chunks().query(**params)
        ids = (result.get("ids") or [[]])[0]
        docs = (result.get("documents") or [[]])[0]
        metas = (result.get("metadatas") or [[]])[0]
        dists = (result.get("distances") or [[]])[0]

        rows: list[dict[str, Any]] = []
        for idx, row_id in enumerate(ids):
            metadata = _safe_metadata(metas[idx] if idx < len(metas) else {})
            distance = dists[idx] if idx < len(dists) else None
            rows.append(
                {
                    "id": row_id,
                    "content": docs[idx] if idx < len(docs) else "",
                    "source_url": metadata.get("source_url", ""),
                    "source_domain": metadata.get("source_domain", ""),
                    "chunk_index": metadata.get("chunk_index"),
                    "total_chunks": metadata.get("total_chunks"),
                    "chunk_size": metadata.get("chunk_size"),
                    "document_title": metadata.get("document_title"),
                    "metadata": metadata,
                    "distance": distance,
                    "similarity": _distance_to_similarity(distance),
                    "created_at": metadata.get("created_at"),
                    "updated_at": metadata.get("updated_at"),
                    "processing_status": metadata.get("processing_status"),
                    "is_processed": metadata.get("is_processed", True),
                }
            )
        return rows

    def get_chunks(
        self, *, where: dict[str, Any] | None = None, limit: int = 100, offset: int = 0
    ) -> dict[str, Any]:
        params: dict[str, Any] = {
            "limit": int(limit),
            "offset": int(offset),
            "include": ["documents", "metadatas"],
        }
        if where:
            params["where"] = where
        return cast(dict[str, Any], self.chunks().get(**params))

    def iter_all_chunks(self, batch_size: int = 500) -> Iterable[dict[str, Any]]:
        offset = 0
        while True:
            result = self.get_chunks(limit=batch_size, offset=offset)
            ids = result.get("ids") or []
            docs = result.get("documents") or []
            metas = result.get("metadatas") or []
            if not ids:
                break

            for idx, row_id in enumerate(ids):
                metadata = _safe_metadata(metas[idx] if idx < len(metas) else {})
                yield {
                    "id": row_id,
                    "content": docs[idx] if idx < len(docs) and docs[idx] is not None else "",
                    "metadata": metadata,
                }

            offset += len(ids)
            if len(ids) < batch_size:
                break

    def delete_chunks(
        self, *, ids: list[str] | None = None, where: dict[str, Any] | None = None
    ) -> None:
        params: dict[str, Any] = {}
        if ids:
            params["ids"] = ids
        if where:
            params["where"] = where
        if params:
            self.chunks().delete(**params)

    def upsert_source(
        self,
        *,
        url: str,
        metadata: dict[str, Any],
        title: str | None = None,
        is_active: bool = True,
    ) -> None:
        source_meta = _safe_metadata(metadata)
        source_tags = _safe_tags(source_meta.get("tags"))
        if source_tags:
            source_meta["tags"] = source_tags
        else:
            source_meta.pop("tags", None)
        source_meta["url"] = url
        source_meta["is_active"] = bool(is_active)
        source_meta["updated_at"] = _now_iso()
        if "created_at" not in source_meta:
            source_meta["created_at"] = _now_iso()

        self.sources().upsert(
            ids=[url],
            documents=[title or url],
            metadatas=[source_meta],
        )

    def get_source(self, url: str) -> dict[str, Any] | None:
        result = self.sources().get(ids=[url], include=["documents", "metadatas"])
        ids = result.get("ids") or []
        if not ids:
            return None
        docs = result.get("documents") or []
        metas = result.get("metadatas") or []
        return {
            "id": ids[0],
            "title": docs[0] if docs else url,
            "metadata": _safe_metadata(metas[0] if metas else {}),
        }

    def list_sources(self, limit: int = 1000, offset: int = 0) -> list[dict[str, Any]]:
        result = self.sources().get(limit=limit, offset=offset, include=["documents", "metadatas"])
        ids = result.get("ids") or []
        docs = result.get("documents") or []
        metas = result.get("metadatas") or []

        rows: list[dict[str, Any]] = []
        for idx, source_id in enumerate(ids):
            metadata = _safe_metadata(metas[idx] if idx < len(metas) else {})
            rows.append(
                {
                    "url": source_id,
                    "title": docs[idx] if idx < len(docs) else source_id,
                    "metadata": metadata,
                    "tags": _safe_tags(metadata.get("tags")),
                    "is_active": bool(metadata.get("is_active", True)),
                    "created_at": metadata.get("created_at"),
                    "updated_at": metadata.get("updated_at"),
                }
            )
        return rows

    def delete_source(self, url: str) -> None:
        self.sources().delete(ids=[url])

    def add_queue_job(self, *, job_id: str, payload: dict[str, Any]) -> None:
        meta = _safe_metadata(payload)
        meta.setdefault("status", "pending")
        meta.setdefault("created_at", _now_iso())
        self.queue().upsert(
            ids=[job_id],
            documents=[str(payload.get("url") or payload.get("file_path") or "")],
            metadatas=[meta],
        )

    def list_queue_jobs(
        self, *, status: str | None = None, limit: int = 100
    ) -> list[dict[str, Any]]:
        where = {"status": status} if status else None
        result = self.queue().get(where=where, limit=limit, include=["documents", "metadatas"])
        ids = result.get("ids") or []
        docs = result.get("documents") or []
        metas = result.get("metadatas") or []

        rows: list[dict[str, Any]] = []
        for idx, row_id in enumerate(ids):
            metadata = _safe_metadata(metas[idx] if idx < len(metas) else {})
            rows.append(
                {"id": row_id, "document": docs[idx] if idx < len(docs) else "", **metadata}
            )
        rows.sort(key=lambda x: str(x.get("created_at") or ""), reverse=True)
        return rows


_store_singleton: ChromaStore | None = None


def get_chroma_store() -> ChromaStore:
    global _store_singleton
    if _store_singleton is None:
        _store_singleton = ChromaStore()
    return _store_singleton
