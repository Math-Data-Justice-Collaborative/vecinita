"""OpenAPI security scheme helpers for FastAPI apps (ADR-011)."""

from __future__ import annotations

from typing import TYPE_CHECKING, cast

from fastapi.openapi.utils import get_openapi

from vecinita_shared_schemas.json_types import JsonObject

if TYPE_CHECKING:
    from collections.abc import Mapping

    from fastapi import FastAPI


_BEARER_JWT: JsonObject = {
    "type": "http",
    "scheme": "bearer",
    "bearerFormat": "JWT",
    "description": "Supabase access token (operator JWT)",
}

_INTERNAL_API_KEY: JsonObject = {
    "type": "http",
    "scheme": "bearer",
    "bearerFormat": "API key",
    "description": "VECINITA_INTERNAL_API_KEY as Authorization: Bearer <key>",
}

_MODAL_PROXY: JsonObject = {
    "type": "apiKey",
    "in": "header",
    "name": "X-Vecinita-Proxy-Key",
    "description": "VECINITA_MODAL_PROXY_KEY (not Modal-Key — reserved by Modal)",
}


def attach_openapi_security_schemes(
    app: FastAPI,
    schemes: Mapping[str, JsonObject],
) -> None:
    """Publish ``components.securitySchemes`` on the app's generated OpenAPI.

    FastAPI does not emit schemes for custom Header/Depends auth unless declared.
    Call once after routes are registered.
    """

    def custom_openapi() -> dict[str, object]:
        if app.openapi_schema is not None:
            return cast("dict[str, object]", app.openapi_schema)
        raw_schema = get_openapi(
            title=app.title,
            version=app.version,
            openapi_version=app.openapi_version,
            description=app.description,
            routes=app.routes,
        )
        schema = cast("dict[str, object]", raw_schema)
        components_obj = schema.get("components")
        components: dict[str, object]
        if isinstance(components_obj, dict):
            components = cast("dict[str, object]", components_obj)
        else:
            components = {}
            schema["components"] = components
        existing = components.get("securitySchemes")
        merged: dict[str, object] = (
            {
                str(scheme_name): scheme_body
                for scheme_name, scheme_body in cast("dict[str, object]", existing).items()
            }
            if isinstance(existing, dict)
            else {}
        )
        merged.update(schemes)
        components["securitySchemes"] = merged
        app.openapi_schema = schema
        return schema

    app.openapi = custom_openapi


def internal_write_security_schemes() -> dict[str, JsonObject]:
    """Bearer JWT + internal API key schemes for the DO write API."""
    return {
        "bearerAuth": dict(_BEARER_JWT),
        "internalApiKey": dict(_INTERNAL_API_KEY),
    }


def data_management_security_schemes() -> dict[str, JsonObject]:
    """Bearer JWT + Modal proxy key schemes for the DM ASGI app."""
    return {
        "bearerAuth": dict(_BEARER_JWT),
        "modalProxyAuth": dict(_MODAL_PROXY),
    }
