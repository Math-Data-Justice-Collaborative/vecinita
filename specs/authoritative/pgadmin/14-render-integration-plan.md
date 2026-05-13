# pgadmin — Render Integration Plan

> Auto-generated: 2026-05-12

## Overview

pgAdmin is not deployed to Render. It runs exclusively in local Docker Compose as a private developer tool. Direct database admin access in production is handled via Render's built-in database dashboard or psql shell.

## Service Definition

Not applicable — no Render service definition exists for pgAdmin.

## Environment Variables

None on Render.

## Database Binding

N/A — pgAdmin connects to PostgreSQL locally via Docker networking, not via Render database bindings.

## Service-to-Service Bindings

None.

## Preview Environments

N/A — pgAdmin is not part of the Render Blueprint.

## Future Consideration

If remote database admin access is ever needed, pgAdmin could be deployed as a Render **private service** (not publicly accessible) with:

| Property | Potential Value |
|----------|----------------|
| Type | Private web service |
| Image | `dpage/pgadmin4` |
| Plan | Starter |
| Access | Internal only (no public URL) |
| Database binding | `fromDatabase: vecinita-postgres` |

This is not currently planned due to security concerns and the availability of Render's built-in database tools.

## Cross-reference

- [Render Landscape](../render/current-landscape.md)

## Related Documents

- [Infrastructure Plan](12-infrastructure-plan.md)
- [Integration Points](03-integration-points.md)
