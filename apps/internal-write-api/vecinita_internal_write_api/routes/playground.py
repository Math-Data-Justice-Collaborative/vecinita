"""Playground model list, pull, and catalog routes (ADR-037)."""

from __future__ import annotations

from fastapi import FastAPI, HTTPException, status
from vecinita_llm_client import LlmClientError
from vecinita_shared_schemas.playground_catalog import playground_catalog_tag_available
from vecinita_shared_schemas.playground_hf_registry import resolve_hf_repo
from vecinita_shared_schemas.playground_models import (
    PlaygroundModelCatalogFamiliesResponse,
    PlaygroundModelCatalogFamily,
    PlaygroundModelCatalogFamilyTagsResponse,
    PlaygroundModelCatalogTag,
    PlaygroundModelListResponse,
    PlaygroundModelPullRequest,
    PlaygroundModelPullResponse,
)

from vecinita_internal_write_api.deps import SuperAdminActorDep, WriteActorDep
from vecinita_internal_write_api.playground_library_client import (
    PlaygroundLibraryClientError,
    PlaygroundLibraryClientProtocol,
)
from vecinita_internal_write_api.playground_service import (
    LlmModelsClientProtocol,
    merge_playground_model_list,
    playground_volume_availability,
    vllm_fallback_model_list,
)


def register_playground_routes(
    app: FastAPI,
    *,
    playground_models: LlmModelsClientProtocol | None,
    playground_library: PlaygroundLibraryClientProtocol,
) -> None:
    """Register playground model list, pull, and catalog routes."""

    @app.get(
        "/internal/v1/models/ollama",
        response_model=PlaygroundModelListResponse,
    )
    def list_playground_models_route(  # pyright: ignore[reportUnusedFunction]
        _actor: WriteActorDep,
    ) -> PlaygroundModelListResponse:
        if playground_models is None:
            return vllm_fallback_model_list()
        try:
            return merge_playground_model_list(playground_models.list_models())
        except LlmClientError:
            return vllm_fallback_model_list()

    @app.post(
        "/internal/v1/models/ollama/pull",
        response_model=PlaygroundModelPullResponse,
        status_code=status.HTTP_202_ACCEPTED,
    )
    def pull_playground_model_route(  # pyright: ignore[reportUnusedFunction]
        _actor: SuperAdminActorDep,
        body: PlaygroundModelPullRequest,
    ) -> PlaygroundModelPullResponse:
        if playground_models is None:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Playground models client not configured",
            )
        try:
            resolve_hf_repo(body.model_id)
        except ValueError as exc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(exc),
            ) from exc
        try:
            return playground_models.start_pull(body.model_id)
        except LlmClientError as exc:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=str(exc),
            ) from exc

    @app.get(
        "/internal/v1/models/ollama/catalog",
        response_model=PlaygroundModelCatalogFamiliesResponse,
    )
    def list_playground_catalog_families_route(  # pyright: ignore[reportUnusedFunction]
        _actor: SuperAdminActorDep,
    ) -> PlaygroundModelCatalogFamiliesResponse:
        try:
            slugs = playground_library.list_families()
        except PlaygroundLibraryClientError as exc:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=str(exc),
            ) from exc
        return PlaygroundModelCatalogFamiliesResponse(
            families=[PlaygroundModelCatalogFamily(slug=slug) for slug in slugs],
        )

    @app.get(
        "/internal/v1/models/ollama/catalog/{slug}",
        response_model=PlaygroundModelCatalogFamilyTagsResponse,
    )
    def list_playground_catalog_family_tags_route(  # pyright: ignore[reportUnusedFunction]
        slug: str,
        _actor: SuperAdminActorDep,
    ) -> PlaygroundModelCatalogFamilyTagsResponse:
        availability = playground_volume_availability(playground_models)
        try:
            tags = playground_library.list_tags(slug)
        except PlaygroundLibraryClientError as exc:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=str(exc),
            ) from exc
        # RD-168 / ISS-004: only tags resolve_hf_repo accepts (blocks NC + unmapped).
        allowed_tags: list[str] = []
        for tag in tags:
            try:
                resolve_hf_repo(tag)
            except ValueError:
                continue
            allowed_tags.append(tag)
        return PlaygroundModelCatalogFamilyTagsResponse(
            slug=slug,
            tags=[
                PlaygroundModelCatalogTag(
                    model_id=tag,
                    available=playground_catalog_tag_available(tag, availability),
                )
                for tag in allowed_tags
            ],
        )
