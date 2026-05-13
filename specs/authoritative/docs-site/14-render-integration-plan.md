# docs-site — Render Integration Plan

> Auto-generated: 2026-05-12

## Overview

The docs-site is primarily configured for GitHub Pages deployment. Render deployment is available as an alternative using a static site service or Docker web service.

## Service Definition

Not currently defined in `render.yaml`. If deployed to Render:

| Property | Potential Value |
|----------|----------------|
| Name | `vecinita-docs-site` |
| Type | Static site or web service |
| Build command | `cd docs-site && npm install && npm run build` |
| Publish directory | `docs-site/build` |
| Plan | Free (static site) or Starter |
| Region | Virginia |

## Environment Variables

No environment variables required. Docusaurus site is fully static with no runtime configuration.

## Database Binding

None.

## Service-to-Service Bindings

None.

## Preview Environments

If deployed to Render, preview environments would automatically build and serve PR previews of the documentation site.

## GitHub Pages Configuration

Currently configured in `docusaurus.config.ts`:

| Property | Value |
|----------|-------|
| URL | `https://acadiagit.github.io` |
| Base URL | `/vecinita/` |
| Organization | `acadiagit` |
| Project | `vecinita` |
| Trailing slash | `false` |

## Cross-reference

- [Render Landscape](../render/current-landscape.md)

## Related Documents

- [Infrastructure Plan](12-infrastructure-plan.md)
- [Integration Points](03-integration-points.md)
