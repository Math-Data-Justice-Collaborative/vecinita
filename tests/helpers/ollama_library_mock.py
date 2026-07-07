"""Mock Ollama library client for catalog route tests."""

from __future__ import annotations


class MockOllamaLibraryClient:
    """In-memory stand-in for ollama.com/library scraper."""

    def __init__(self) -> None:
        """Seed catalog families and tags for integration tests."""
        self.families = ["llama3.2", "qwen2.5"]
        self.tags_by_slug: dict[str, list[str]] = {
            "qwen2.5": [
                "qwen2.5:1.5b-instruct",
                "qwen2.5:3b-instruct",
                "qwen2.5:3b-instruct-q4_K_M",
            ],
            "llama3.2": ["llama3.2:1b", "llama3.2:3b"],
        }

    def list_families(self) -> list[str]:
        """Return seeded model family slugs."""
        return list(self.families)

    def list_tags(self, slug: str) -> list[str]:
        """Return seeded tags for one family slug."""
        return list(self.tags_by_slug.get(slug, []))

    def close(self) -> None:
        """Match OllamaLibraryClient lifecycle for create_app teardown."""
        return
