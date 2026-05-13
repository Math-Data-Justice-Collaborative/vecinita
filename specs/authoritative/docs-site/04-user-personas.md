# docs-site — User Personas

> Auto-generated: 2026-05-12

## Overview

The docs-site serves developers and contributors who need to understand the Vecinita platform.

## Personas

### Developer / Contributor

| Attribute | Value |
|-----------|-------|
| Role | Current or potential contributor to the Vecinita project |
| Interaction mode | Web browser (read-only) |
| Goals | Understand architecture, find API references, follow deployment guides, onboard to the project |
| Pain points | Documentation may be incomplete or out of date, need to cross-reference multiple docs |

### Solo Developer (Maintainer)

| Attribute | Value |
|-----------|-------|
| Role | Primary developer maintaining the project |
| Interaction mode | Web browser + local dev server for previewing changes |
| Goals | Keep documentation up to date, preview changes before publishing, ensure docs match code |
| Pain points | Documentation maintenance overhead, keeping docs in sync with rapid development |

## Actor-System Map

| Persona | Touchpoint | Access Level |
|---------|------------|--------------|
| Developer / Contributor | Documentation Hub (`/docs`) | Read (public) |
| Developer / Contributor | Home page (`/`) | Read (public) |
| Solo Developer | Local dev server (`localhost:3000`) | Read/Write (local) |

## Diagrams

- [User Personas Diagram](diagrams/user-personas.md)

## Related Documents

- [User Journeys](05-user-journeys.md)
- [Behavior](01-behavior.md)
