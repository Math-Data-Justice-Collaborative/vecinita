# docs-site — Testing Plan

> Auto-generated: 2026-05-12

## Overview

The docs-site has minimal testing requirements. The primary validation is the Docusaurus build itself, which checks for broken links and validates markdown.

## Test Layers

| Layer | Tool | Location | Scope |
|-------|------|----------|-------|
| Type check | TypeScript (`tsc --noEmit`) | `docs-site/tsconfig.json` | Config and component type safety |
| Build validation | Docusaurus build | `npm run build` | Broken links, invalid markdown, asset resolution |
| Link checking | Docusaurus `onBrokenLinks: "warn"` | Build output | Internal link integrity |

No unit, integration, or E2E tests — the site has no custom logic to test.

## Key Test Scenarios

| Scenario | Layer | Status |
|----------|-------|--------|
| Site builds without errors | Build | Covered |
| TypeScript compiles | Type check | Covered |
| Internal links resolve | Build (warnings) | Covered |
| Custom CSS applies correctly | Manual | Gap |
| Navigation renders correctly | Manual | Gap |

## CI Integration

| Target | Command | Trigger |
|--------|---------|---------|
| Type check | `npm run typecheck` | PR, push to main |
| Build | `npm run build` | PR, push to main (if configured) |

## Coverage Targets

N/A — no custom application code to measure coverage against.

## Related Documents

- [API Contract](08-api-contract.md)
- [Infrastructure Plan](12-infrastructure-plan.md)
