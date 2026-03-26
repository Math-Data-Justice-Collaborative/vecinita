"""Contract check: matrix must include every Gateway API v1 endpoint."""

from __future__ import annotations

import re
from pathlib import Path

import pytest

ROUTERS = {
    "router_ask.py": "/ask",
    "router_scrape.py": "/scrape",
    "router_embed.py": "/embed",
    "router_admin.py": "/admin",
    "router_documents.py": "/documents",
}

ROUTE_PATTERN = re.compile(r'@router\\.(get|post|patch|delete)\\("([^"]*)"\\)')
MATRIX_PATTERN = re.compile(r"\\|\\s*(GET|POST|PATCH|DELETE)\\s*\\|\\s*([^|]+?)\\s*\\|")


@pytest.mark.unit
@pytest.mark.api
def test_gateway_matrix_covers_all_v1_routes() -> None:
    backend_root = Path(__file__).resolve().parents[2]
    api_dir = backend_root / "src" / "api"
    matrix_file = Path(__file__).resolve().parent / "MATRIX_GATEWAY_V1.md"

    source_routes: set[tuple[str, str]] = set()

    for router_file, router_prefix in ROUTERS.items():
        text = (api_dir / router_file).read_text(encoding="utf-8")
        for method, route_path in ROUTE_PATTERN.findall(text):
            full_path = f"/api/v1{router_prefix}{route_path}"
            source_routes.add((method.upper(), full_path))

    matrix_text = matrix_file.read_text(encoding="utf-8")
    matrix_routes = {(method, path.strip()) for method, path in MATRIX_PATTERN.findall(matrix_text)}

    missing = sorted(source_routes - matrix_routes)

    assert not missing, "MATRIX_GATEWAY_V1.md is missing endpoints: " + ", ".join(
        f"{method} {path}" for method, path in missing
    )
