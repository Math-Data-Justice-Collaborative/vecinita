"""BFS frontier: queue + per-run visited URLs."""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass


@dataclass(frozen=True)
class QueuedURL:
    url: str
    depth: int
    seed_root: str


class CrawlFrontier:
    """Queue + visited set; caps enforced in runner."""

    def __init__(self, *, max_depth: int) -> None:
        self.max_depth = max_depth
        self._q: deque[QueuedURL] = deque()
        self._visited: set[str] = set()

    def seed(self, url: str, seed_root: str) -> None:
        self.enqueue(QueuedURL(url=url, depth=0, seed_root=seed_root))

    def enqueue(self, item: QueuedURL) -> bool:
        if item.depth > self.max_depth:
            return False
        if item.url in self._visited:
            return False
        self._visited.add(item.url)
        self._q.append(item)
        return True

    def dequeue(self) -> QueuedURL | None:
        if not self._q:
            return None
        return self._q.popleft()
