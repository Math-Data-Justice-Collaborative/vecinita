"""Serialize Postgres corpus mutations across pytest workers and make invocations."""

from __future__ import annotations

import fcntl
import hashlib
import os
import threading
from pathlib import Path

_local = threading.local()


def _lock_path() -> Path:
    url = os.environ.get(
        "DATABASE_URL",
        "postgresql+psycopg://vecinita:vecinita@localhost:5432/vecinita",
    )
    digest = hashlib.sha256(url.encode()).hexdigest()[:16]
    return Path(f"/tmp/vecinita-corpus-db-{digest}.lock")


class corpus_db_lock:
    """Reentrant process-wide exclusive lock for the shared corpus Postgres DB."""

    def __enter__(self) -> corpus_db_lock:
        depth = int(getattr(_local, "depth", 0))
        if depth == 0:
            lock_path = _lock_path()
            lock_path.parent.mkdir(parents=True, exist_ok=True)
            fd = os.open(lock_path, os.O_CREAT | os.O_RDWR, 0o600)
            fcntl.flock(fd, fcntl.LOCK_EX)
            _local.fd = fd
        _local.depth = depth + 1
        return self

    def __exit__(self, *_exc: object) -> None:
        depth = int(getattr(_local, "depth", 1)) - 1
        _local.depth = depth
        if depth == 0:
            fd = getattr(_local, "fd", None)
            if fd is not None:
                fcntl.flock(fd, fcntl.LOCK_UN)
                os.close(fd)
                _local.fd = None
