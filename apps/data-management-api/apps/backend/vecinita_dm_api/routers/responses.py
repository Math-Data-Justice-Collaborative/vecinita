"""Map httpx responses from upstream scraper to Starlette/FastAPI responses."""

from __future__ import annotations

import json

from httpx import Response as HttpxResponse
from starlette.responses import JSONResponse, Response


def httpx_to_starlette(resp: HttpxResponse) -> Response:
    """Preserve status code and JSON or raw body from an upstream httpx response."""
    if resp.status_code == 204 or not resp.content:
        return Response(status_code=resp.status_code)
    ct = (resp.headers.get("content-type") or "").lower()
    if "application/json" in ct:
        try:
            payload = resp.json()
        except json.JSONDecodeError:
            payload = None
        if isinstance(payload, (dict, list)):
            return JSONResponse(status_code=resp.status_code, content=payload)
    media = resp.headers.get("content-type")
    media_type = media.split(";")[0].strip() if media else None
    return Response(
        status_code=resp.status_code,
        content=resp.content,
        media_type=media_type,
    )
