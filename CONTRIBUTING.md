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
cd backend && uv sync
cd ../frontend && npm install

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
├── backend/           # FastAPI + LangChain/LangGraph
│   ├── src/          # Source code
│   ├── tests/        # Unit tests
│   └── pyproject.toml
├── frontend/          # React + TypeScript + Vite
│   ├── src/          # React components
│   ├── docs/         # Frontend documentation
│   └── package.json
├── tests/            # E2E and integration tests
├── docs/             # Project documentation
└── docker-compose.yml
```

### Canonical scraper

The **only** supported scraper implementation and orchestration code lives under
[`services/scraper/`](./services/scraper/) (the `vecinita_scraper` package used by Modal, Docker, and CI).

The **data-management-api** and other backends must **not** duplicate that logic: call a deployed
scraper over HTTP using `SCRAPER_SERVICE_BASE_URL` and the typed client in
[`services/data-management-api/packages/service-clients/`](./services/data-management-api/packages/service-clients/)
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
cd frontend
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
cd frontend
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
   - `cd backend && uv run pytest`
   - `cd frontend && npm test`
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
