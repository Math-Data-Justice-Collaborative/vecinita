# docs-site — High-Level Behavior

> Auto-generated: 2026-05-12

## Purpose

The docs-site is a Docusaurus-based static documentation site that publishes the Vecinita project's architecture documentation, API guides, deployment runbooks, and developer onboarding materials. It reads markdown files from the repository's top-level `docs/` directory and serves them as a navigable documentation hub.

## Responsibilities

| Responsibility | Description |
|----------------|-------------|
| Documentation hosting | Serve markdown documentation as a navigable, searchable website |
| Content aggregation | Pull docs from the monorepo's `docs/` directory into a structured site |
| Navigation | Auto-generate sidebars from directory structure |
| Branding | Apply Vecinita branding (logo, colors, footer) |
| Edit links | Provide "Edit this page" links to the GitHub repository |

## Key Behaviors

### Serve Documentation

- **Trigger:** User navigates to the docs site URL
- **Process:** Docusaurus serves pre-built static HTML/CSS/JS from the `build/` directory. Sidebar navigation auto-generated from the `docs/` directory structure.
- **Outcome:** User can browse, search, and navigate documentation

### Build Static Site

- **Trigger:** `npm run build` or CI/CD pipeline
- **Process:** Docusaurus reads markdown from `../docs/` (relative to `docs-site/`), applies theme and configuration from `docusaurus.config.ts`, generates static HTML
- **Outcome:** Production-ready static site in `build/` directory

### Local Development

- **Trigger:** `npm run start`
- **Process:** Docusaurus dev server starts with hot reload, serves docs at `http://localhost:3000/vecinita/`
- **Outcome:** Live preview of documentation changes

## Boundaries

- Does NOT interact with any Vecinita backend services (purely static)
- Does NOT have runtime dependencies on databases, APIs, or external services
- Does NOT generate or modify documentation content (content lives in `docs/`)
- Does NOT require authentication (public documentation)
- Does NOT include blog functionality (disabled in config)

## Related Documents

- [Architecture](07-architecture.md)
- [Integration Points](03-integration-points.md)
- [Architecture Diagram](diagrams/architecture.md)
