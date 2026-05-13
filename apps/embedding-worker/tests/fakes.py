from __future__ import annotations

from collections.abc import Sequence


class FakeVector:
    def __init__(self, values: Sequence[float]) -> None:
        self._values = list(values)

    def tolist(self) -> list[float]:
        return list(self._values)


class FakeEmbedder:
    def __init__(self, vectors: Sequence[Sequence[float]] | None = None) -> None:
        self.calls: list[list[str]] = []
        self._vectors = list(vectors or ([0.1, 0.2, 0.3], [0.4, 0.5, 0.6]))

    def embed(self, texts: Sequence[str]) -> list[FakeVector]:
        self.calls.append(list(texts))
        if len(texts) > len(self._vectors):
            raise RuntimeError("not enough fake vectors configured")
        return [FakeVector(self._vectors[index]) for index, _ in enumerate(texts)]


class FailingEmbedder:
    def embed(self, texts: Sequence[str]) -> list[FakeVector]:
        raise RuntimeError("backend unavailable")
