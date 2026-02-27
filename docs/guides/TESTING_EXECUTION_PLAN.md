# Testing Execution Plan

This plan defines how Vecinita verifies the present state of backend and frontend, and how we iterate until quality gates are complete.

## Scope

- Backend unit and integration reliability
- Frontend unit/integration reliability
- Frontend E2E critical and extended journeys
- Coverage visibility at service level (backend and frontend)

## Commands (Baseline + Iteration Loop)

### Backend

```bash
cd backend
uv sync
uv run pytest -q --cov=src --cov-report=xml --cov-report=term
uv run pytest -q -m "integration and not db and not llm"
```

### Frontend

```bash
cd frontend
npm ci
npm run test -- --run --coverage
npm run test:e2e
```

## Use-Case Matrix (Integration + E2E)

| Use Case | Integration Coverage | E2E Coverage | Gate |
|---|---|---|---|
| Chat interface | Hook/component integration around send, stream, and render | Community flow sends messages in page + widget | Must pass |
| Documents tab | Dashboard integration for data render + filtering + source actions | Community flow loads documents and opens source links | Must pass |
| Login flow | Login page integration for submit/error/redirect | Community flow reaches login route and validates form controls | Must pass |
| Admin actions | Admin dashboard integration for source/tag management | Admin E2E logs in and performs source actions (when env credentials present) | Must pass (or explicit env-gated skip) |
| Upload actions | Admin dashboard integration for upload form + completion state | Admin E2E performs click upload and drag-drop upload | Must pass (or explicit env-gated skip) |
| Link clicking | Source-card/link integration assertions with URL/target checks | Documents E2E requires link count > 0 and click-through popup | Must pass |

## Success Criteria

All criteria must be true before completion:

1. Root README exposes separate backend and frontend coverage badges.
2. Backend coverage workflow passes and publishes coverage artifacts.
3. Frontend coverage workflow passes and publishes coverage artifacts.
4. No conditional-pass loophole for document/source-link E2E checks.
5. Login flow has dedicated integration coverage for submit + failure + redirect.
6. Documents has dedicated integration coverage for filtering and actionable links.
7. Admin and upload flows are covered in both integration and E2E suites, with explicit env-gated behavior documented.

## Iteration Protocol

For any gate failure:

1. Reproduce failure with the smallest affected command.
2. Fix root cause in the closest layer (test, fixture, or implementation).
3. Re-run focused test(s), then re-run full layer command.
4. Update this plan only if scope or gates changed.
