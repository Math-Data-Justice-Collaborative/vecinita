"""Shared flock for repo Make/npm hooks to prevent concurrent node_modules corruption."""

from __future__ import annotations

import fcntl
import hashlib
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path


def lock_path(repo: Path, name: str) -> Path:
    digest = hashlib.sha256(str(repo.resolve()).encode()).hexdigest()[:16]
    return Path("/tmp") / f"vecinita-{name}-{digest}.lock"


@contextmanager
def repo_lock(repo: Path, name: str, *, exclusive: bool, blocking: bool) -> Iterator[bool]:
    path = lock_path(repo, name)
    path.touch(exist_ok=True)
    handle = path.open("w")
    acquired = False
    try:
        operation = fcntl.LOCK_EX if exclusive else fcntl.LOCK_SH
        if not blocking:
            operation |= fcntl.LOCK_NB
        try:
            fcntl.flock(handle.fileno(), operation)
            acquired = True
        except BlockingIOError:
            acquired = False
        yield acquired
    finally:
        if acquired:
            fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
        handle.close()
