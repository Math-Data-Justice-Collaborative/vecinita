# chat-frontend — Dependencies

> Auto-generated: 2026-05-12

## Overview

React SPA with Tailwind CSS styling, Shadcn/ui components, and Vite build tooling.

## Internal Dependencies (monorepo)

| Package/Module | Path | Purpose |
|----------------|------|---------|
| None | — | Chat frontend is self-contained; no shared monorepo packages |

## External Dependencies (runtime)

| Package | Version | Purpose | Critical |
|---------|---------|---------|----------|
| react | 18.3.1 | UI framework | Yes |
| react-dom | 18.3.1 | DOM rendering | Yes |
| react-router-dom | ^6.30.3 | Client-side routing | Yes |
| react-markdown | ^10.1.0 | Render agent responses as markdown | Yes |
| remark-gfm | ^4.0.1 | GitHub-flavored markdown support | Yes |
| uuid | ^13.0.0 | Generate thread and message IDs | Yes |
| lucide-react | ^0.487.0 | Icon library | No |
| tailwind-merge | ^3.2.0 | Tailwind class merging utility | No |
| class-variance-authority | ^0.7.1 | Component variant styles | No |
| clsx | ^2.1.1 | Conditional CSS class joining | No |
| sonner | 2.0.3 | Toast notifications | No |
| @radix-ui/* | Various | Accessible UI primitives (dialog, tooltip, etc.) | No |
| @mui/material | 7.3.5 | Material UI components (supplementary) | No |
| motion | 12.23.24 | Animation library | No |

## Infrastructure Dependencies

| Resource | Provider | Purpose |
|----------|----------|---------|
| Vite dev server | Local | Development server with HMR |
| nginx | Docker (production) | Static file serving on Render |

## Service Dependencies (runtime calls)

| Service | Required | Fallback |
|---------|----------|----------|
| Gateway API | Yes | Frontend loads but chat is non-functional; config fetch retries with fallback URLs |

## Related Documents

- [Infrastructure Plan](12-infrastructure-plan.md)
- [Integration Points](03-integration-points.md)
