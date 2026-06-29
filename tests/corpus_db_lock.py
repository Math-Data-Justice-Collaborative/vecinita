"""Serialize Postgres corpus mutations across pytest workers and make invocations."""

from __future__ import annotations

import fcntl
import hashlib
import os
import tempfile
import threading
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Self


class _ThreadState:
    fd: int | None = None
    depth: int = 0


_local = threading.local()


def _state() -> _ThreadState:
    state = getattr(_local, "state", None)
    if not isinstance(state, _ThreadState):
        state = _ThreadState()
        _local.state = state
    return state


def _lock_path() -> Path:
    url = os.environ.get(
        "DATABASE_URL",
        "postgresql+psycopg://vecinita:vecinita@localhost:5432/vecinita",
    )
    digest = hashlib.sha256(url.encode()).hexdigest()[:16]
    return Path(tempfile.gettempdir()) / f"vecinita-corpus-db-{digest}.lock"


class corpus_db_lock:  # noqa: N801  # lowercase context-manager factory; renaming breaks importers
    """Reentrant process-wide exclusive lock for the shared corpus Postgres DB."""

    def __enter__(self) -> Self:
        """Acquire the exclusive corpus DB lock (reentrant within a thread)."""
        state = _state()
        if state.depth == 0:
            lock_path = _lock_path()
            lock_path.parent.mkdir(parents=True, exist_ok=True)
            fd = os.open(lock_path, os.O_CREAT | os.O_RDWR, 0o600)
            fcntl.flock(fd, fcntl.LOCK_EX)
            state.fd = fd
        state.depth += 1
        return self

    def __exit__(self, *_exc: object) -> None:
        """Release the corpus DB lock when the outermost context exits."""
        state = _state()
        state.depth -= 1
        if state.depth == 0 and state.fd is not None:
            fcntl.flock(state.fd, fcntl.LOCK_UN)
            os.close(state.fd)
            state.fd = None
