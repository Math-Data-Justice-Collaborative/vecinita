# docs-site — Infrastructure Plan

> Auto-generated: 2026-05-12

## Overview

Static site built by Docusaurus and deployed to GitHub Pages or Render as static files.

## Build

| Property | Value |
|----------|-------|
| Dockerfile | N/A (or optional for Render deployment) |
| Build context | `docs-site/` |
| Build command | `npm run build` (Docusaurus build) |
| Build output | `docs-site/build/` |
| Node requirement | Node.js 20+ |

## Deployment

| Property | Value |
|----------|-------|
| Platform | GitHub Pages (primary) or Render (alternative) |
| Service type | Static site |
| Plan/tier | Free (GitHub Pages) or Starter (Render) |
| Region | GitHub CDN (Pages) or Virginia (Render) |
| Auto-deploy | Push to main (GitHub Actions) or checksPass (Render) |

## Scaling

| Property | Value |
|----------|-------|
| Min instances | N/A — static files served by CDN/platform |
| Max instances | N/A |
| Scaling trigger | N/A — static content scales automatically |

## Observability

| Concern | Tool | Config |
|---------|------|--------|
| Logging | N/A — static site | No server logs |
| Health check | N/A — static files always available if hosting platform is up | |
| Build monitoring | GitHub Actions or Render build logs | Build failures |

## Related Documents

- [Render Integration Plan](14-render-integration-plan.md)
- [Modal Integration Plan](13-modal-integration-plan.md)
