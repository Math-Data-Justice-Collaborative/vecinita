"""Root pytest configuration — shared fixtures for integration and e2e."""

pytest_plugins = [
    "tests.integration.data_management.conftest",
    "tests.integration.chat_rag.conftest",
]
