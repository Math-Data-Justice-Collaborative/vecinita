---
name: fastapi-router-py
description: Guides creation of FastAPI routers with typed Pydantic request/response models, auth dependencies, and explicit HTTP status codes. Use when adding or refactoring API routes in this repo, expanding OpenAPI surfaces, or matching patterns from Microsoft fastapi-router-py for gateway or agent FastAPI apps.
---

# FastAPI router patterns (Vecinita)

Derived from [Microsoft `fastapi-router-py`](https://github.com/microsoft/skills/tree/main/.github/plugins/azure-sdk-python/skills/fastapi-router-py) and aligned with this codebase.

## Where code lives in Vecinita

- **Gateway app:** `backend/src/api/main.py` — mounts routers with `app.include_router(...)`.
- **Routers:** `backend/src/api/router_*.py` (e.g. `router_ask.py`, `router_documents.py`).
- **Models:** Often `backend/src/api/models.py` or colocated schemas; follow existing imports in neighboring routers.

Prefer **one module per feature area** (`router_<name>.py`) and a dedicated `APIRouter` instance, unless the route count is small.

## Quick start (template placeholders)

When starting from a resource template, replace:

| Placeholder | Example |
|-------------|---------|
| `{{ResourceName}}` | PascalCase: `Project` |
| `{{resource_name}}` | snake_case: `project` |
| `{{resource_plural}}` | plural: `projects` |

Upstream template lives in the Microsoft repo:  
`assets/template.py` under `fastapi-router-py` (copy from GitHub when bootstrapping a new resource).

## Authentication patterns

Match existing gateway dependencies:

- **Optional auth** — dependency returns `None` when unauthenticated (public endpoints with optional elevation).
- **Required auth** — dependency raises `401` when unauthenticated.

Use the same `Depends(...)` helpers as sibling routers in `backend/src/api/` (e.g. `middleware`, `auth` patterns already used on `/api/v1` routes).

## Response models

Always set `response_model` for stable OpenAPI and client contracts:

```python
@router.get("/items/{item_id}", response_model=Item)
async def get_item(item_id: str) -> Item:
    ...

@router.get("/items", response_model=list[Item])
async def list_items() -> list[Item]:
    ...
```

Use Pydantic v2 models shared with tests where possible so Schemathesis and contract tests stay aligned.

## HTTP status codes

Set explicit status codes on mutating routes:

```python
@router.post("/items", status_code=status.HTTP_201_CREATED)
@router.delete("/items/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
```

Use `fastapi.status` constants; document non-default bodies in OpenAPI (`responses=` on the decorator) when the API returns structured errors.

## Integration checklist

1. Add `router_<feature>.py` under `backend/src/api/` with an `APIRouter` and tags for OpenAPI grouping.
2. Add or extend Pydantic models (request/response) in the same style as `backend/src/api/models.py` or feature-local schemas.
3. **Mount** the router in `backend/src/api/main.py` with a consistent prefix (e.g. `/api/v1`).
4. Add **unit/integration tests** under `backend/tests/` (mirror existing `router_*` tests).
5. If the frontend consumes the route, update the client module under `frontend/src/...` and any contract tests.

## Testing and coverage

- **Offline API shape:** `make test-schemathesis-gateway` (gateway ASGI + OpenAPI).
- **Contract tests:** follow `tests/integration/test_service_integration_points_contract.py` for cross-service env and routing expectations.

## References

- Microsoft skill install: `npx skills add https://github.com/microsoft/skills --skill fastapi-router-py`
- FastAPI docs: [Tutorial — Bigger Applications](https://fastapi.tiangolo.com/tutorial/bigger-applications/)
