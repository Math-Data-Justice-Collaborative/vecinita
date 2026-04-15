"""Gateway-side registry for Modal ``FunctionCall`` handles (``modal.Dict`` or in-memory)."""

from __future__ import annotations

import asyncio
import os
import uuid
from datetime import datetime, timezone
from typing import Any

from src.services.modal.invoker import _get_modal_module

_KEY_PREFIX = "mj:"
_INDEX_KEY = "mj:__index__"
_MAX_INDEX = 200


def _registry_dict_name() -> str:
    return (os.getenv("MODAL_JOB_REGISTRY_DICT") or "vecinita-gateway-modal-jobs").strip()


def _use_modal_dict() -> bool:
    if str(os.getenv("MODAL_JOB_REGISTRY_DISABLE", "")).strip().lower() in {"1", "true", "yes"}:
        return False
    return True


class ModalJobRegistry:
    """Track spawned Modal calls for gateway CRUD (Modal Dict when available)."""

    def __init__(self) -> None:
        self._memory: dict[str, Any] = {}
        self._mem_lock = asyncio.Lock()
        self._dict_cache: Any = None

    def _modal_dict(self) -> Any:
        if self._dict_cache is not None:
            return self._dict_cache
        modal = _get_modal_module()
        self._dict_cache = modal.Dict.from_name(_registry_dict_name(), create_if_missing=True)
        return self._dict_cache

    def _key(self, job_id: str) -> str:
        return f"{_KEY_PREFIX}{job_id}"

    async def _dict_put(self, key: str, value: Any) -> None:
        d = self._modal_dict()
        await d.put.aio(key, value)

    async def _dict_get(self, key: str) -> Any:
        d = self._modal_dict()
        return await d.get.aio(key)

    async def _dict_pop(self, key: str) -> Any:
        d = self._modal_dict()
        return await d.pop.aio(key)

    async def _append_index_modal(self, job_id: str) -> None:
        d = self._modal_dict()
        cur = await d.get.aio(_INDEX_KEY)
        ids: list[str] = list(cur) if isinstance(cur, list) else []
        ids = [j for j in ids if j != job_id]
        ids.insert(0, job_id)
        ids = ids[:_MAX_INDEX]
        await d.put.aio(_INDEX_KEY, ids)

    async def create_tracked_call(
        self,
        *,
        kind: str,
        function_call_id: str,
        app_name: str,
        function_name: str,
        extra: dict[str, Any] | None = None,
    ) -> str:
        job_id = str(uuid.uuid4())
        record: dict[str, Any] = {
            "gateway_job_id": job_id,
            "kind": kind,
            "status": "pending",
            "modal_function_call_id": function_call_id,
            "modal_app": app_name,
            "modal_function": function_name,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "result": None,
            "error": None,
        }
        if extra:
            record["extra"] = extra

        if _use_modal_dict():
            try:
                await self._dict_put(self._key(job_id), record)
                await self._append_index_modal(job_id)
                return job_id
            except Exception:
                pass

        async with self._mem_lock:
            self._memory[self._key(job_id)] = record
            idx = list(self._memory.get(_INDEX_KEY, []) or [])
            if not isinstance(idx, list):
                idx = []
            idx = [j for j in idx if j != job_id]
            idx.insert(0, job_id)
            self._memory[_INDEX_KEY] = idx[:_MAX_INDEX]
        return job_id

    async def get_record(self, job_id: str) -> dict[str, Any] | None:
        key = self._key(job_id)
        if _use_modal_dict():
            try:
                got = await self._dict_get(key)
                if got is not None:
                    return got  # type: ignore[return-value]
            except Exception:
                pass
        async with self._mem_lock:
            row = self._memory.get(key)
            return dict(row) if isinstance(row, dict) else None

    async def update_record(self, job_id: str, updates: dict[str, Any]) -> None:
        key = self._key(job_id)
        cur = await self.get_record(job_id)
        if not cur:
            return
        merged = {**cur, **updates, "updated_at": datetime.now(timezone.utc).isoformat()}
        if _use_modal_dict():
            try:
                await self._dict_put(key, merged)
                return
            except Exception:
                pass
        async with self._mem_lock:
            self._memory[key] = merged

    async def delete_record(self, job_id: str) -> bool:
        key = self._key(job_id)
        removed = False
        if _use_modal_dict():
            try:
                prev = await self._dict_pop(key)
                removed = prev is not None
            except Exception:
                removed = False
        async with self._mem_lock:
            if key in self._memory:
                del self._memory[key]
                removed = True
            idx = list(self._memory.get(_INDEX_KEY, []) or [])
            if isinstance(idx, list) and job_id in idx:
                self._memory[_INDEX_KEY] = [j for j in idx if j != job_id]
        return removed

    async def list_recent_ids(self, limit: int = 50) -> list[str]:
        cap = max(1, min(200, limit))
        if _use_modal_dict():
            try:
                d = self._modal_dict()
                cur = await d.get.aio(_INDEX_KEY)
                if isinstance(cur, list):
                    return [str(x) for x in cur[:cap]]
            except Exception:
                pass
        async with self._mem_lock:
            idx = self._memory.get(_INDEX_KEY, [])
            if isinstance(idx, list):
                return [str(x) for x in idx[:cap]]
        return []


modal_job_registry = ModalJobRegistry()
