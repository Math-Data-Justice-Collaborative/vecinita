# Contributing to Vecinita

Thank you for your interest in contributing to Vecinita! This document provides guidelines and instructions for contributing to our project.

## Getting Started

### Prerequisites
- **Backend**: Python 3.10+, uv package manager
- **Frontend**: Node.js 20+, npm
- **Services**: Docker & Docker Compose (for local development)

### Setting Up Development

```bash
# Clone the repository
git clone https://github.com/Math-Data-Justice-Collaborative/vecinita
cd vecinita

# Install dependencies
cd apps/gateway && uv sync
cd ../apps/chat-frontend && npm install

# Start the full stack in tmux
make dev

# Or start services individually
make dev-backend
make dev-gateway
make dev-frontend
```

## Project Structure

```
vecinita/
├── apps/gateway/      # Gateway FastAPI + shared Python `src/`, tests, uv lockfile
├── apps/agent/        # Agent Dockerfile + canonical `src/agent/` (symlinked from gateway `src/agent`)
│   ├── src/          # Source code
│   ├── tests/        # Unit tests
│   └── pyproject.toml
├── apps/chat-frontend/    # React + TypeScript + Vite (chat UI submodule)
│   ├── src/          # React components
│   ├── docs/         # Frontend documentation
│   └── package.json
├── tests/            # E2E and integration tests
├── docs/             # Project documentation
└── docker-compose.yml
```

### Canonical scraper

The **only** supported scraper implementation and orchestration code lives under
[`apps/scraper-worker/`](./apps/scraper-worker/) (the `vecinita_scraper` package used by Modal, Docker, and CI).

The **data-management-api** and other backends must **not** duplicate that logic: call a deployed
scraper over HTTP using `SCRAPER_SERVICE_BASE_URL` and the typed client in
[`apps/data-management-api/packages/service-clients/`](./apps/data-management-api/packages/service-clients/)
(`ScraperClient`). See the normative remote contract in
[`specs/003-consolidate-scraper-dm/contracts/dm-api-remote-service-integration.md`](./specs/003-consolidate-scraper-dm/contracts/dm-api-remote-service-integration.md).

## Code Standards

### Python (Backend)

- **Formatter**: Black
- **Linter**: Ruff
- **Type Checker**: mypy
- **Style**: PEP 8

```bash
make format-backend
make lint-backend
make typecheck-backend
```

### JavaScript/TypeScript (Frontend)

- **Formatter**: Prettier
- **Linter**: ESLint
- **Package Manager**: npm

```bash
make format-frontend
make lint-frontend
make typecheck-frontend

# Or run frontend scripts directly
cd apps/chat-frontend
npm run format
npm run format:write
npm run lint
npm run lint:fix
npm run typecheck
```

### Root Makefile

Use the root Makefile for the common workflows:

```bash
make help
make dev
make lint
make typecheck
make format
make test-unit
make test-integration
make test-e2e
make test-microservices-contracts
```

### CI attestation gate (feature 019)

Merge blocking for the manifest-defined bar uses **committed JSON** under `.ci/` plus a single GitHub Actions job (**`ci-attestation-gate.yml`**, job **`attestation-gate`**). Hosted CI does **not** re-run `make ci` for merge proof (**Option A**); you run checks locally and refresh the attestation.

```bash
make ci-attestation           # runs manifest commands (includes make ci), writes .ci/ci-attestation.json
make ci-attestation-validate  # same validation as CI
```

- **Changing checks:** edit `.ci/required-checks.json`, then rerun `make ci-attestation` and commit both files.
- **Risks (must be documented for contributors):** no mandatory hosted re-run of manifest checks for merge; fork/untrusted machine attestation; environment drift; bad-faith or mistaken claims. Optional mitigations stay advisory unless promoted via manifest + **FR-010** (see `specs/019-contract-ci-json-gate/spec.md` **SC-005**).
- **Details:** [`specs/019-contract-ci-json-gate/quickstart.md`](./specs/019-contract-ci-json-gate/quickstart.md).

#### SC-003 — Documentation-only review checklist (five questions)

For reviewers **not** involved in authoring the gate docs: **30 minutes**, published contributor docs only, answer all five. **Success:** ≥4 correct per reviewer; average across **three** independent reviewers on the same doc revision. Maintainer answer key: [`specs/019-contract-ci-json-gate/artifacts/sc-003-review-answer-key.md`](./specs/019-contract-ci-json-gate/artifacts/sc-003-review-answer-key.md).

1. If `.ci/ci-attestation.json` is missing but `.ci/required-checks.json` is valid, does the attestation gate job pass?
2. Does merge under this gate require GitHub Actions to re-run `make ci` on the PR runner for the same change?
3. Name **two** of the **minimum accepted risks** that contributor-facing docs must list verbatim (see **SC-005**).
4. You add a new `id` to `.ci/required-checks.json`. What must you do before the gate can pass again?
5. The attestation’s `generated_at` is **older** than the configured maximum age when the gate runs. Does the job pass?

### OpenAPI clients and env (feature 015)

Canonical commands live in the root **README** under *OpenAPI clients and Modal HTTP ban* (`make openapi-codegen`, `make openapi-codegen-verify`, `make check-modal-http`). For operator-oriented setup, schema URLs, and staging notes, use [`specs/015-openapi-sdk-clients/quickstart.md`](./specs/015-openapi-sdk-clients/quickstart.md).

### Configuration

- **EditorConfig**: `.editorconfig` for consistent settings

## Testing

### Backend Tests

```bash
make test-backend-unit
make test-all-integration
make test-integration-gateway-fast
make test-integration-gateway-full
```

### Frontend Tests

```bash
cd apps/chat-frontend
npm run test:unit
npm run test:watch
npm run test:coverage

# Or use Make aliases
make test-frontend-unit
make test-frontend-e2e
```

### E2E and Integration Tests

```bash
# Cross-stack suites (requires services running)
make test-cross-integration
make test-cross-e2e

# Aggregate targets
make test-integration
make test-e2e
```

## Pull Request Process

1. **Create a branch** from `main`:
   ```bash
   git checkout -b feature/description-of-feature
   git checkout -b fix/description-of-fix
   ```

2. **Write code** following project standards

3. **Run tests locally**:
   - `cd apps/gateway && uv run pytest`
   - `cd apps/chat-frontend && npm test`
   - `cd tests && uv run pytest -v`

4. **Commit with clear messages**:
   ```bash
   git commit -m "feat: add feature description"
   git commit -m "fix: resolve issue description"
   ```

5. **Push to your branch**:
   ```bash
   git push origin feature/your-branch-name
   ```

6. **Create Pull Request** with:
   - Clear description of changes
   - References to any related issues
   - Screenshots/demos if UI-related

## Branch Naming Conventions

- `feature/description` - New features
- `fix/description` - Bug fixes
- `docs/description` - Documentation updates
- `refactor/description` - Code refactoring
- `test/description` - Test additions

## Commit Message Conventions

Follow [Conventional Commits](https://www.conventionalcommits.org/):

```
type(scope): subject

body

footer
```

Examples:
- `feat(agent): add LangGraph workflow integration`
- `fix(api): resolve CORS issue on /ask endpoint`
- `docs(backend): update API documentation`
- `test(integration): add end-to-end test coverage`

## Code Review Process

- At least one approving review before merge
- CI/CD checks must pass
- Tests coverage maintained or improved
- Code follows project standards

## Reporting Issues

- Use GitHub Issues
- Include clear description
- Add reproduction steps if applicable
- Attach logs or screenshots when helpful

## Questions?

- Check existing issues/discussions
- Review documentation in `/docs`
- Ask in GitHub Discussions

## License

By contributing, you agree your work will be licensed under the MIT License.

---

Thank you for contributing to Vecinita!
