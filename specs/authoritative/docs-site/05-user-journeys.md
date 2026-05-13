# docs-site — User Journeys

> Auto-generated: 2026-05-12

## Overview

Journeys center on reading documentation and contributing documentation changes.

## Journeys

### Browse Architecture Documentation

**Persona:** Developer / Contributor
**Goal:** Understand the Vecinita platform architecture

| Step | Action | System Response | Notes |
|------|--------|-----------------|-------|
| 1 | Navigate to docs site | Home page with "Open Documentation Hub" button | |
| 2 | Click "Documentation Hub" | Docs sidebar and content displayed | |
| 3 | Browse sidebar navigation | Auto-generated from `docs/` directory structure | |
| 4 | Read architecture docs | Markdown rendered as HTML with syntax highlighting | |
| 5 | Follow cross-references | Navigate between related docs | |

**Happy path outcome:** Developer understands the platform architecture.
**Failure modes:** Broken links (Docusaurus warns), outdated content.

### Edit Documentation

**Persona:** Solo Developer
**Goal:** Update documentation and preview changes

| Step | Action | System Response | Notes |
|------|--------|-----------------|-------|
| 1 | Edit markdown files in `docs/` | Files saved | |
| 2 | Run `npm run start` in `docs-site/` | Dev server starts at `localhost:3000/vecinita/` | Hot reload enabled |
| 3 | Preview changes in browser | Updated content rendered immediately | |
| 4 | Run `npm run build` | Static site generated in `build/` | Validates links |
| 5 | Commit and push | CI/CD deploys updated site | |

**Happy path outcome:** Documentation updated and published.
**Failure modes:** Build fails due to broken markdown links (warnings in config).

### Contribute via "Edit this page"

**Persona:** Developer / Contributor
**Goal:** Fix a typo or add content

| Step | Action | System Response | Notes |
|------|--------|-----------------|-------|
| 1 | Click "Edit this page" link | GitHub editor opens for the markdown file | |
| 2 | Make edit in GitHub | GitHub UI editor | |
| 3 | Submit PR | PR created against main branch | |

**Happy path outcome:** Documentation improvement contributed.
**Failure modes:** Contributor doesn't have write access (fork workflow needed).

## Diagrams

- [User Journey Diagram](diagrams/user-journeys.md)

## Related Documents

- [User Personas](04-user-personas.md)
- [Behavior](01-behavior.md)
