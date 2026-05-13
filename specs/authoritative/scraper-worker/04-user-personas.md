# User Personas: Scraper Worker
> Auto-generated: 2026-05-12

See [diagrams/user-personas.md](diagrams/user-personas.md) for the actor relationship diagram.

## Overview

The scraper worker serves automated systems, human operators, and downstream services. Direct human interaction is mediated through the gateway or DM frontend; the scraper itself receives programmatic invocations.

## Personas

### P1: Gateway Service (Automated System)

| Property | Value |
|----------|-------|
| Type | Internal service |
| Interaction | Modal SDK `.remote()` / `.spawn()` |
| Goals | Submit scrape jobs, check status, cancel jobs, trigger reindex |
| Pain points | Cold start latency, timeout coordination, error propagation |
| Frequency | On every user-initiated scrape or reindex action |

The gateway is the primary caller. It translates HTTP requests from frontends and operators into Modal function invocations against the scraper worker.

### P2: Data Management Frontend User (Human via DM Frontend)

| Property | Value |
|----------|-------|
| Type | End user (community researcher, content curator) |
| Interaction | HTTP REST via DM API facade on Render |
| Goals | Submit URLs to scrape, monitor job progress, browse ingested documents |
| Pain points | Long scrape times, unclear progress feedback, failed URLs without explanation |
| Frequency | 5-20 sessions/week |

These users interact through the DM frontend, which calls the Render-deployed FastAPI REST API. They care about job completion, not pipeline internals.

### P3: System Operator / DevOps (Human)

| Property | Value |
|----------|-------|
| Type | Platform operator |
| Interaction | Modal CLI, Modal dashboard, direct function invocation |
| Goals | Monitor pipeline health, debug failed jobs, trigger reindex, scale workers |
| Pain points | Queue depth visibility, debugging pipeline stage failures, cold start impact |
| Frequency | Daily monitoring, ad-hoc debugging |

Operators use the Modal dashboard to inspect queue depths, function logs, and container metrics. They may invoke functions directly for debugging.

### P4: Agent Service (Automated Consumer)

| Property | Value |
|----------|-------|
| Type | Internal service (downstream) |
| Interaction | PostgreSQL read queries |
| Goals | Retrieve chunks and embeddings for RAG retrieval |
| Pain points | Stale data if pipeline is backed up, chunk quality affecting retrieval accuracy |
| Frequency | On every user Q&A query |

The agent service does not call the scraper directly but depends on the data it produces. Data quality and freshness are critical.

### P5: Embedding Service (Automated Dependency)

| Property | Value |
|----------|-------|
| Type | Internal service (upstream dependency) |
| Interaction | HTTP / Modal SDK |
| Goals | Receive text chunks, return embeddings |
| Pain points | Batch size spikes, latency under load |
| Frequency | On every scrape job during embed stage |

## Persona × Function Matrix

| Function | P1 Gateway | P2 DM User | P3 Operator | P4 Agent | P5 Embedding |
|----------|-----------|------------|-------------|----------|-------------|
| `modal_scrape_job_submit` | Direct caller | Via DM API | Debug only | — | — |
| `modal_scrape_job_get` | Direct caller | Via DM API | Debug only | — | — |
| `modal_scrape_job_list` | Direct caller | Via DM API | Debug only | — | — |
| `modal_scrape_job_cancel` | Direct caller | Via DM API | Debug only | — | — |
| `trigger_reindex` | Direct caller | — | Direct caller | — | — |
| `scraper_worker` | — | — | Debug only | — | — |
| `drain_*_queue` | — | — | Monitor | — | Called during embed |
| REST API | — | Direct user | Health checks | — | — |
