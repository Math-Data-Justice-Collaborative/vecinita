# data-management-frontend — Modal Integration Plan

> Auto-generated: 2026-05-12

## Overview

N/A — the data-management frontend is a browser-based SPA. It interacts with Modal indirectly through the DM API, which proxies scrape job requests to Modal workers. The frontend itself has no Modal integration.

## Modal App

Not applicable.

## Functions

None.

## Volumes and Secrets

None.

## Invocation Pattern

The frontend submits scrape jobs via `POST /jobs` to the DM API, which in turn invokes Modal functions. The frontend tracks job status via `GET /jobs/:job_id` polling. The `modal-types.ts` file contains TypeScript types that mirror Modal job status shapes.

**Source:** `frontends/data-management/src/app/api/modal-types.ts`

## Environment Variables

None related to Modal directly. The DM API handles all Modal communication.

## Cross-reference

- [Modal Landscape](../modal/current-landscape.md)

## Related Documents

- [Integration Points](03-integration-points.md)
- [Infrastructure Plan](12-infrastructure-plan.md)
