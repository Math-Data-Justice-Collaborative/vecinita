# pgadmin — User Personas

> Auto-generated: 2026-05-12

## Overview

pgadmin serves a single persona: the solo developer who maintains the Vecinita platform. There are no other users, automated systems, or service-to-service consumers.

## Personas

### Solo Developer

| Attribute | Value |
|-----------|-------|
| Role | Platform developer and database administrator |
| Interaction mode | Web UI (browser) |
| Goals | Inspect database state, run diagnostic queries, verify migrations, debug data issues, manage schemas |
| Pain points | No CLI alternative for quick queries in containerized environments; need visual schema navigation for complex joins |

## Actor-System Map

| Persona | Touchpoint | Access Level |
|---------|------------|--------------|
| Solo Developer | pgAdmin Web UI (port 5050) | Full admin (superuser) |

## Diagrams

- [User Personas Diagram](diagrams/user-personas.md)

## Related Documents

- [User Journeys](05-user-journeys.md)
- [Behavior](01-behavior.md)
