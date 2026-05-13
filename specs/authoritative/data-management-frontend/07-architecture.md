# data-management-frontend — Architecture

> Auto-generated: 2026-05-12

## Overview

Single-page application (SPA) built with React, TypeScript, and Vite. Uses React Router v7 for file-based routing, Tailwind CSS + Shadcn/ui for styling, and a centralized API client for all DM API communication.

## Architecture Style

Client-side SPA with page-based routing, centralized API client, and context-based state.

## Component Map

| Component | Responsibility | Source Path |
|-----------|---------------|-------------|
| App | Root component, locale provider, scraper config diagnostic | `frontends/data-management/src/app/App.tsx` |
| Layout | Navigation sidebar/header wrapping all authenticated routes | `frontends/data-management/src/app/components/Layout.tsx` |
| Dashboard | Corpus statistics overview with cards and charts | `frontends/data-management/src/app/pages/Dashboard.tsx` |
| CorpusView | Paginated document list with search and filters | `frontends/data-management/src/app/pages/CorpusView.tsx` |
| AddDocument | Form for submitting scrape jobs or uploading documents | `frontends/data-management/src/app/pages/AddDocument.tsx` |
| DocumentDetail | Single document view with edit/delete capabilities | `frontends/data-management/src/app/pages/DocumentDetail.tsx` |
| ScrapeJobs | Scrape job list with status monitoring and cancellation | `frontends/data-management/src/app/pages/ScrapeJobs.tsx` |
| TagsView | Tag inventory browser with counts and locale filtering | `frontends/data-management/src/app/pages/TagsView.tsx` |
| Settings | Application settings page | `frontends/data-management/src/app/pages/Settings.tsx` |
| AdminAccess | Admin access configuration page | `frontends/data-management/src/app/pages/AdminAccess.tsx` |
| Login | Authentication login form | `frontends/data-management/src/app/pages/Login.tsx` |
| RequireAuth | Route guard for authenticated routes | `frontends/data-management/src/app/auth/RequireAuth.tsx` |
| AuthContext | API-key authentication state | `frontends/data-management/src/app/auth/AuthContext.tsx` |
| LocaleContext | i18n locale management (en/es) | `frontends/data-management/src/app/i18n/LocaleContext.tsx` |
| RAGApiClient | Centralized HTTP client for DM API | `frontends/data-management/src/app/api/rag-api.ts` |
| scraper-config | Scraper URL resolution and runtime config | `frontends/data-management/src/app/api/scraper-config.ts` |
| UI primitives | Shadcn/ui components (table, card, dialog, sidebar, etc.) | `frontends/data-management/src/app/components/ui/` |

## Runtime Characteristics

| Property | Value |
|----------|-------|
| Language / runtime | TypeScript / Browser (ES2020+) |
| Framework | React 18 + Vite 6 + React Router 7 |
| Entry point | `frontends/data-management/src/main.tsx` |
| Port | 5174 (dev), 10000 (Render production) |
| Health check | `/` (returns index.html) |

## Concurrency Model

Single-threaded browser event loop. Multiple API requests may run concurrently via `Promise.allSettled()` (e.g., parallel document + jobs fetch for dashboard stats). No Web Workers or service workers.

## Diagrams

- [Architecture Diagram](diagrams/architecture.md)

## Related Documents

- [Behavior](01-behavior.md)
- [Infrastructure Plan](12-infrastructure-plan.md)
