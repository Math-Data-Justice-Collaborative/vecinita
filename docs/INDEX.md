# Vecinita Documentation Index

Welcome to the organized documentation hub.

## Getting Started

- [Quick Start Guide](guides/QUICKSTART.md) - Get up and running quickly
- [Getting Started](guides/GETTING_STARTED.md) - Detailed setup instructions
- [Documentation Hub](README.md) - Role-based navigation
- [Testing Execution Plan](guides/TESTING_EXECUTION_PLAN.md) - Integration and E2E success criteria

## Architecture

- [Architecture Directory](architecture/) - All architecture and system design docs
- [Microservice Architecture](architecture/ARCHITECTURE_MICROSERVICE.md)
- [Embedding Service Architecture](architecture/EMBEDDING_SERVICE_ARCHITECTURE.md)
- [Modal Hybrid Architecture](architecture/MODAL_HYBRID_ARCHITECTURE.md)
- [Monorepo Refactor Blueprint](architecture/MONOREPO_REFACTOR_BLUEPRINT.md) - Target structure and migration phases for chat + data-management + modal services

## Deployment

- [Deployment Directory](deployment/) - Deployment docs and manifests
- [Multi-Repo CI/CD Orchestration](deployment/MULTI_REPO_CICD_ORCHESTRATION.md) - Parent workflow dispatch model for chat, data-management, proxy, and modal services
- [Microservices Compose Stack](deployment/MICROSERVICES_COMPOSE_STACK.md) - Local proxy-centric stack for chat + data-management + modal services
- [Render Deployment](deployment/RENDER_DEPLOYMENT_THREE_SERVICES.md)
- [Modal Setup](deployment/MODAL_SETUP.md)
- [Codespaces Secrets Setup](deployment/GITHUB_CODESPACES_SECRETS_SETUP.md)

## Guides & Diagnostics

- [Guides Directory](guides/) - Practical how-to guides
- [Diagnostics Directory](diagnostics/) - Troubleshooting and performance baselines
- [DB Search Diagnostic Guide](diagnostics/DB_SEARCH_DIAGNOSTIC_GUIDE.md)

## Reference & APIs

- [Reference Directory](reference/) - Specs, config, and policy docs
- [API Integration Spec](reference/API_INTEGRATION_SPEC.md)
- [Privacy Policy](reference/PRIVACY_POLICY.md)
- [Root File Organization Policy](reference/ROOT_FILE_ORGANIZATION_POLICY.md)
- [Stage 3 Deprecation Checklist](reference/STAGE3_DEPRECATION_CHECKLIST.md) - Low-risk checklist for root manifest deprecation
- [Stage 3 Dry-Run Audit](reference/STAGE3_DRY_RUN_AUDIT.md) - Go/no-go decisions with explicit evidence

Migration note: legacy root schema files were moved to `supabase/migrations/archive/` as part of Stage 1 organization. See `supabase/migrations/archive/README.md` for archive conventions.

## Reports

- [Implementation Reports](reports/implementation/) - Phase-by-phase implementation records
- [Project Reports](reports/project/) - Status, summaries, and completion reports

## Other Areas

- [Features](features/) - Feature-specific documentation
- [Tools](tools/) - Utilities and CLI docs
- [SQL Archive Conventions](../supabase/migrations/archive/README.md) - Legacy schema file archive rules
- [Backend Docs](../backend/docs/INDEX.md) - Backend-specific documentation
- [Frontend Docs](../frontend/docs/) - Frontend-specific documentation

---

**Latest Update**: February 2026
