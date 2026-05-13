# chat-frontend — User Personas

> Auto-generated: 2026-05-12

## Overview

The chat frontend serves two primary personas: community members seeking civic information, and an admin/developer persona who manages the system.

## Personas

### Community Member

| Attribute | Value |
|-----------|-------|
| Role | End user seeking civic information |
| Interaction mode | Web UI (browser) — desktop and mobile |
| Goals | Find relevant civic resources (food banks, legal aid, housing), get answers in English or Spanish, receive source-cited responses |
| Pain points | Cold start delays when backend warms up, unfamiliar with AI chat interfaces, may need clarification prompts explained |

### Admin / Developer

| Attribute | Value |
|-----------|-------|
| Role | Platform administrator and sole developer |
| Interaction mode | Web UI (browser) with admin auth |
| Goals | Access admin routes, inspect documents dashboard, verify agent behavior, debug streaming responses |
| Pain points | Need to configure env credentials for admin access, no user management UI |

## Actor-System Map

| Persona | Touchpoint | Access Level |
|---------|------------|--------------|
| Community Member | Chat page (`/`) | Read (public) |
| Community Member | Documents dashboard (`/documents`) | Read (public) |
| Admin / Developer | Admin route (`/admin`) | Read/Write (authenticated) |
| Admin / Developer | Login page (`/login`) | Write (auth flow) |

## Diagrams

- [User Personas Diagram](diagrams/user-personas.md)

## Related Documents

- [User Journeys](05-user-journeys.md)
- [Behavior](01-behavior.md)
