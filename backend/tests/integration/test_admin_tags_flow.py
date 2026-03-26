"""Integration-style tests for admin metadata tagging flow."""

from typing import Any

import pytest
from fastapi.testclient import TestClient

pytestmark = pytest.mark.integration


class _Result:
    def __init__(self, data: Any):
        self.data = data


class _Table:
    def __init__(self, db: "FakeDB", name: str):
        self.db = db
        self.name = name
        self._where = {}
        self._payload = None

    def insert(self, payload):
        self._payload = payload
        return self

    def upsert(self, payload, on_conflict=None):
        self._payload = payload
        self._on_conflict = on_conflict
        return self

    def select(self, *_args, **_kwargs):
        return self

    def update(self, payload):
        self._payload = payload
        return self

    def eq(self, key, value):
        self._where[key] = value
        return self

    def execute(self):
        if self.name == "sources":
            payload = self._payload
            if isinstance(payload, dict):
                self.db.sources[payload["url"]] = payload
            return _Result([payload] if payload else [])

        if self.name == "processing_queue":
            if isinstance(self._payload, dict):
                self.db.queue.append(self._payload)
            return _Result([self._payload] if self._payload else [])

        if self.name == "document_chunks":
            if self._payload and self._where.get("id"):
                for chunk in self.db.chunks:
                    if chunk["id"] == self._where["id"]:
                        chunk["metadata"] = self._payload.get("metadata", {})
                return _Result([])

            if self._where.get("source_url"):
                rows = [
                    row
                    for row in self.db.chunks
                    if row.get("source_url") == self._where["source_url"]
                ]
                return _Result(rows)

            return _Result(self.db.chunks)

        return _Result([])


class FakeDB:
    def __init__(self):
        self.sources = {}
        self.queue = []
        self.chunks = [
            {"id": "chunk-1", "source_url": "https://example.com", "metadata": {}},
            {"id": "chunk-2", "source_url": "https://example.com", "metadata": {"tags": ["old"]}},
        ]

    def table(self, name: str):
        return _Table(self, name)

    def rpc(self, name: str, params=None):
        class _RPC:
            def __init__(self, outer: "FakeDB", rpc_name: str, rpc_params):
                self.outer = outer
                self.rpc_name = rpc_name
                self.rpc_params = rpc_params or {}

            def execute(self):
                if self.rpc_name == "get_all_metadata_tags":
                    tags = sorted(
                        {
                            tag
                            for source in self.outer.sources.values()
                            for tag in (source.get("metadata", {}).get("tags", []) or [])
                        }
                    )
                    return _Result([{"tag": tag} for tag in tags])
                if self.rpc_name == "get_sources_with_counts":
                    return _Result(
                        [
                            {
                                "url": url,
                                "chunk_count": sum(
                                    1
                                    for chunk in self.outer.chunks
                                    if chunk.get("source_url") == url
                                ),
                                "metadata": data.get("metadata", {}),
                            }
                            for url, data in self.outer.sources.items()
                        ]
                    )
                return _Result([])

        return _RPC(self, name, params)


class FakeChromaStore:
    def __init__(self):
        self.sources = {}
        self.chunk_rows = [
            {
                "id": "chunk-1",
                "document": "Doc 1",
                "metadata": {"source_url": "https://example.com", "tags": []},
                "embedding": [0.1, 0.2],
            },
            {
                "id": "chunk-2",
                "document": "Doc 2",
                "metadata": {"source_url": "https://example.com", "tags": ["old"]},
                "embedding": [0.3, 0.4],
            },
        ]
        self.queue = []

    def upsert_source(
        self, *, url: str, metadata: dict, title: str | None = None, is_active: bool = True
    ):
        self.sources[url] = {
            "url": url,
            "title": title or url,
            "metadata": metadata,
            "is_active": is_active,
            "tags": metadata.get("tags", []),
            "created_at": metadata.get("created_at"),
            "updated_at": metadata.get("updated_at"),
        }

    def add_queue_job(self, *, job_id: str, payload: dict):
        self.queue.append({"id": job_id, **payload})

    def get_source(self, url: str):
        return self.sources.get(url)

    def get_chunks(self, *, where=None, limit=100, offset=0):
        where = where or {}
        source_url = where.get("source_url")
        rows = [
            c
            for c in self.chunk_rows
            if not source_url or c["metadata"].get("source_url") == source_url
        ]
        rows = rows[offset : offset + limit]
        return {
            "ids": [r["id"] for r in rows],
            "documents": [r["document"] for r in rows],
            "metadatas": [r["metadata"] for r in rows],
        }

    def upsert_chunks(self, rows):
        by_id = {c["id"]: c for c in self.chunk_rows}
        for row in rows:
            rid = row["id"]
            by_id[rid] = {
                "id": rid,
                "document": row.get("content", ""),
                "metadata": row.get("metadata", {}),
                "embedding": row.get("embedding", [0.0]),
            }
        self.chunk_rows = list(by_id.values())
        return len(rows)

    def list_sources(self, limit=1000, offset=0):
        return list(self.sources.values())[offset : offset + limit]

    def iter_all_chunks(self, batch_size=500):
        for chunk in self.chunk_rows:
            yield {"id": chunk["id"], "content": chunk["document"], "metadata": chunk["metadata"]}

    def chunks(self):
        class _Chunks:
            def __init__(self, outer):
                self.outer = outer

            def get(self, ids=None, include=None):
                ids = ids or []
                rows = [c for c in self.outer.chunk_rows if c["id"] in ids]
                return {"embeddings": [r.get("embedding", [0.0]) for r in rows]}

        return _Chunks(self)


@pytest.fixture
def integration_client(env_vars, monkeypatch):
    for key, value in env_vars.items():
        monkeypatch.setenv(key, value)

    from src.api import router_admin
    from src.api.main import app

    db = FakeDB()
    store = FakeChromaStore()

    async def _fake_ingest_source_url(url: str, depth: int, normalized_tags: list[str]):
        metadata = {
            "source_url": url,
            "source_domain": "example.com",
            "tags": normalized_tags,
        }
        store.upsert_source(url=url, metadata=metadata, title=url, is_active=True)
        return {
            "status": "queued",
            "url": url,
            "depth": depth,
            "tags": normalized_tags,
        }

    app.dependency_overrides[router_admin.get_database_client] = lambda: db
    app.dependency_overrides[router_admin._verify_admin] = lambda: {"id": "admin-user"}
    monkeypatch.setattr(router_admin, "get_chroma_store", lambda: store)
    monkeypatch.setattr(router_admin, "_ingest_source_url", _fake_ingest_source_url)

    client = TestClient(app)
    yield client

    app.dependency_overrides.clear()


def test_admin_tagging_flow(integration_client):
    add_response = integration_client.post(
        "/api/v1/admin/sources",
        data={"url": "https://example.com", "depth": 1, "tags": "Housing,Food"},
    )
    assert add_response.status_code == 200
    assert add_response.json()["tags"] == ["housing", "food"]

    edit_response = integration_client.patch(
        "/api/v1/admin/sources/tags",
        json={"url": "https://example.com", "tags": ["benefits", "Housing"]},
    )
    assert edit_response.status_code == 200
    assert edit_response.json()["tags"] == ["benefits", "housing"]

    tags_response = integration_client.get("/api/v1/admin/tags")
    assert tags_response.status_code == 200
    assert "benefits" in tags_response.json()["tags"]

    sources_response = integration_client.get("/api/v1/admin/sources")
    assert sources_response.status_code == 200
    assert sources_response.json()["sources"][0]["tags"] == ["benefits", "housing"]
