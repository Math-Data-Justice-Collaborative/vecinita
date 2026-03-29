"""Pytest configuration for E2E and integration tests.

This folder contains tests that require:
- Running backend service (FastAPI)
- Running frontend service (Vite dev server)
- External dependencies (Playwright, etc.)

Tests here run independently from backend/tests/ and should not
depend on backend project structure or imports.
"""

import os
import sys
from pathlib import Path

import pytest

# Add src to path for imports
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))


def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers", 
        "e2e: end-to-end tests (requires Playwright and running services)"
    )
    config.addinivalue_line(
        "markers",
        "integration: integration tests (requires running backend/frontend)"
    )
    config.addinivalue_line(
        "markers",
        "api: API endpoint tests (requires running backend service)"
    )
    config.addinivalue_line(
        "markers",
        "frontend_required: tests that require frontend service"
    )
    config.addinivalue_line(
        "markers",
        "backend_required: tests that require backend service"
    )
    config.addinivalue_line(
        "markers",
        "requires_services: tests that require both services"
    )


class ServiceConfig:
    """Configuration for backend and frontend services."""
    
    def __init__(self):
        """Load service configuration from environment."""
        # Default to gateway port 8004 (API v1), can override with BACKEND_URL for agent port 8000
        self.backend_url = os.getenv("BACKEND_URL", "http://localhost:8004")
        self.frontend_url = os.getenv("FRONTEND_URL", "http://localhost:5173")
        self.skip_e2e = os.getenv("SKIP_E2E", "").lower() in ("true", "1", "yes")
        self.skip_integration = os.getenv("SKIP_INTEGRATION", "").lower() in ("true", "1", "yes")
        self.playwright_headless = os.getenv("PLAYWRIGHT_HEADLESS", "true").lower() in ("true", "1", "yes")
        self.api_timeout = int(os.getenv("API_TIMEOUT", "10"))
        self.e2e_timeout = int(os.getenv("E2E_TIMEOUT", "30"))


@pytest.fixture(scope="session")
def service_config() -> ServiceConfig:
    """Provide service configuration for the test session."""
    return ServiceConfig()


@pytest.fixture
def backend_url(service_config) -> str:
    """Get backend service URL."""
    return service_config.backend_url


@pytest.fixture
def frontend_url(service_config) -> str:
    """Get frontend service URL."""
    return service_config.frontend_url


@pytest.fixture
def api_timeout(service_config) -> int:
    """Get API timeout in seconds."""
    return service_config.api_timeout


def pytest_collection_modifyitems(config, items):
    """Skip tests based on environment configuration."""
    service_cfg = ServiceConfig()
    
    for item in items:
        # Skip E2E tests if requested
        if service_cfg.skip_e2e and item.get_closest_marker("e2e"):
            item.add_marker(pytest.mark.skip(reason="E2E tests disabled (set SKIP_E2E=false to enable)"))
        
        # Skip integration tests if requested
        if service_cfg.skip_integration and item.get_closest_marker("integration"):
            item.add_marker(pytest.mark.skip(reason="Integration tests disabled"))
        
        # Skip tests requiring services if they're not available
        if item.get_closest_marker("requires_services"):
            if not _services_available(service_cfg):
                item.add_marker(pytest.mark.skip(reason="Backend/frontend services not available"))


def _services_available(config: ServiceConfig) -> bool:
    """Check if required services are available."""
    import httpx
    
    try:
        with httpx.Client(timeout=2) as client:
            # Check backend
            try:
                response = client.get(f"{config.backend_url}/health", follow_redirects=True)
                backend_ok = response.status_code in (200, 404)  # 404 is fine if /health doesn't exist
            except Exception:
                backend_ok = False
            
            return backend_ok
    except Exception:
        return False
