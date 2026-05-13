# data-management-frontend — Dependencies

> Auto-generated: 2026-05-12

## Overview

React SPA with Tailwind CSS + Shadcn/ui, React Router 7, and comprehensive UI component library.

## Internal Dependencies (monorepo)

| Package/Module | Path | Purpose |
|----------------|------|---------|
| DM OpenAPI spec | `specs/005-wire-services-dm-front/artifacts/dm-openapi.snapshot.json` | Source for generated TypeScript types |

## External Dependencies (runtime)

| Package | Version | Purpose | Critical |
|---------|---------|---------|----------|
| react | 18.3.1 | UI framework | Yes |
| react-dom | 18.3.1 | DOM rendering | Yes |
| react-router | 7.13.0 | Client-side routing | Yes |
| sonner | 2.0.3 | Toast notifications | No |
| lucide-react | 0.487.0 | Icon library | No |
| tailwind-merge | 3.2.0 | Tailwind class merging | No |
| class-variance-authority | 0.7.1 | Component variants | No |
| clsx | 2.1.1 | Conditional classes | No |
| recharts | 2.15.2 | Dashboard charts | No |
| @radix-ui/* | Various | Accessible UI primitives | No |
| @mui/material | 7.3.5 | Material UI components | No |
| motion | 12.23.24 | Animations | No |

## Infrastructure Dependencies

| Resource | Provider | Purpose |
|----------|----------|---------|
| Vite dev server | Local | Development with HMR |
| openapi-typescript | Dev dependency | Type generation from OpenAPI spec |

## Service Dependencies (runtime calls)

| Service | Required | Fallback |
|---------|----------|----------|
| Data Management API | Yes | Falls back to in-memory mock data when `VITE_DM_API_BASE_URL` is unconfigured |

## Related Documents

- [Infrastructure Plan](12-infrastructure-plan.md)
- [Integration Points](03-integration-points.md)
