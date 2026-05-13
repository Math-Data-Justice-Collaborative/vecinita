# docs-site — Integration Points

> Auto-generated: 2026-05-12

## Overview

The docs-site has no runtime integrations. It is a completely static site with no API calls, database connections, or service dependencies.

## Internal Integrations

None. The docs-site is self-contained.

## External Integrations

None at runtime. Build-time integration only:

| Provider | Protocol | Purpose | When |
|----------|----------|---------|------|
| GitHub (acadiagit/vecinita) | HTTPS link | "Edit this page" links, repository links | Build time (config) |
| GitHub Pages | HTTPS | Hosting target (alternative to Render) | Deploy time |

## Integration Details

### Monorepo Documentation (`docs/`)

- **Relationship:** Build-time content source
- **Path:** `../docs/` (relative to `docs-site/`)
- **Mechanism:** Docusaurus `docs.path` config reads markdown files at build time
- **No runtime dependency:** Once built, the static site is fully independent

## Diagrams

- [Integration Diagram](diagrams/integration-points.md)
- [Sequence Flows](diagrams/sequence-flows.md)

## Related Documents

- [Architecture](07-architecture.md)
- [Dependencies](09-dependencies.md)
