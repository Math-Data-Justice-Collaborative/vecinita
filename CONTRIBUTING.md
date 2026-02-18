# Contributing to Vecinita

Thank you for your interest in contributing to Vecinita! This document provides guidelines and instructions for contributing to our project.

## Getting Started

### Prerequisites
- **Backend**: Python 3.10+, uv package manager
- **Frontend**: Node.js 18+, npm
- **Services**: Docker & Docker Compose (for local development)

### Setting Up Development

```bash
# Clone the repository
git clone https://github.com/acadiagit/vecinita
cd vecinita

# Backend
cd backend
uv sync
uv run uvicorn src.agent.main:app --reload

# Frontend (in another terminal)
cd frontend
npm install
npm run dev

# Tests (in another terminal)
cd tests
uv sync
uv run pytest -v
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

## Code Standards

### Python (Backend)

- **Formatter**: Black
- **Linter**: Ruff
- **Type Checker**: Pyright
- **Style**: PEP 8

```bash
cd backend
uv run black src tests
uv run ruff check --fix src tests
uv run pyright src
```

### JavaScript/TypeScript (Frontend)

- **Formatter**: Prettier
- **Linter**: ESLint
- **Package Manager**: npm

```bash
cd frontend
npm run format      # Format code
npm run lint        # Check linting
npm run lint:fix    # Fix linting issues
```

### Configuration

- **EditorConfig**: `.editorconfig` for consistent settings

## Testing

### Backend Tests

```bash
cd backend

# All tests
uv run pytest

# With coverage
uv run pytest --cov

# Specific test file
uv run pytest tests/test_name.py

# Unit tests only
uv run pytest backend/tests/ -m "not integration"
```

### Frontend Tests

```bash
cd frontend

# All tests
npm test

# Watch mode
npm run test:watch

# With coverage
npm run test:coverage
```

### E2E and Integration Tests

```bash
cd tests

# All tests (requires backend + frontend running)
uv run pytest -v

# Integration only
uv run pytest -v -m integration

# E2E only
uv run pytest -v -m e2e
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

Thank you for contributing to Vecinita! 🎉
