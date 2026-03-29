"""HTTP client utilities for integration tests.

Provides convenient clients for testing backend and frontend services.
"""

import httpx
from typing import Dict, Any


class APIClient:
    """HTTP client for testing backend API."""
    
    def __init__(self, base_url: str = "http://localhost:8004", timeout: int = 10):
        """Initialize API client.
        
        Args:
            base_url: Backend service URL (defaults to gateway at port 8004)
            timeout: Request timeout in seconds
        """
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.client = httpx.Client(base_url=self.base_url, timeout=timeout)
    
    def ask(self, query: str, language: str = "en", **kwargs) -> Dict[str, Any]:
        """Call /api/v1/ask endpoint.
        
        Args:
            query: User question (for backward compatibility, maps to 'question')
            language: Language code (en, es) - currently informational only
            **kwargs: Additional query parameters
            
        Returns:
            Response JSON
        """
        params = {
            "question": query,  # API v1 uses 'question' parameter
            **kwargs
        }
        response = self.client.get("/api/v1/ask", params=params)
        response.raise_for_status()
        return response.json()
    
    def health(self) -> Dict[str, Any]:
        """Check service health.
        
        Returns:
            Health status response
        """
        try:
            # Try v1 endpoint first
            response = self.client.get("/api/v1/admin/health")
            return response.json()
        except Exception:
            # Fallback to legacy health endpoint
            try:
                response = self.client.get("/health")
                return response.json()
            except Exception:
                return {"status": "unavailable"}
    
    def get(self, path: str, **kwargs) -> httpx.Response:
        """Make GET request.
        
        Args:
            path: API path
            **kwargs: Request kwargs
            
        Returns:
            Response object
        """
        return self.client.get(path, **kwargs)
    
    def post(self, path: str, **kwargs) -> httpx.Response:
        """Make POST request.
        
        Args:
            path: API path
            **kwargs: Request kwargs
            
        Returns:
            Response object
        """
        return self.client.post(path, **kwargs)
    
    def close(self):
        """Close the client."""
        self.client.close()
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, *args):
        """Context manager exit."""
        self.close()
