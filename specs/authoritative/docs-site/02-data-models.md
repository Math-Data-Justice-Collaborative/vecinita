# docs-site — Data Models

> Auto-generated: 2026-05-12

## Overview

The docs-site has no data models. It is a static site generator that reads markdown files and produces HTML. There are no databases, APIs, or runtime data structures beyond Docusaurus internals.

## Models

N/A — static site with no application data models.

## Content Structure

The site's "data" is markdown documentation sourced from the monorepo:

| Content Source | Path | Description |
|----------------|------|-------------|
| Documentation root | `docs/` (monorepo root) | Main documentation directory |
| Included files | `docs/README.md`, `docs/guides/greeting.md` | Explicitly included docs |
| Excluded files | `**/INDEX.md` | Excluded from build |

**Source:** `docs-site/docusaurus.config.ts` — `docs.include` and `docs.exclude` arrays

## Relationships

N/A.

## Diagrams

- [ER Diagram](diagrams/data-models.md)

## Related Documents

- [API Contract](08-api-contract.md)
- [Data Flow](06-data-flow.md)
