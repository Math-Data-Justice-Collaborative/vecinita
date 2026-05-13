"""Custom exceptions for Vecinita Scraper."""


class VecinitaError(Exception):
    """Base exception for Vecinita Scraper."""

    pass


class ValidationError(VecinitaError):
    """Raised when validation fails (URL, config, etc.)."""

    pass


class CrawlingError(VecinitaError):
    """Raised during crawling operations."""

    pass


class ProcessingError(VecinitaError):
    """Raised during document processing."""

    pass


class ChunkingError(VecinitaError):
    """Raised during chunking operations."""

    pass


class EmbeddingError(VecinitaError):
    """Raised during embedding operations."""

    pass


class DatabaseError(VecinitaError):
    """Raised during database operations."""

    pass


class ConfigError(VecinitaError):
    """Raised during configuration loading."""

    pass
