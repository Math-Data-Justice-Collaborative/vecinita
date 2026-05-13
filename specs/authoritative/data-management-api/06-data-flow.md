# Data Management API — Data Flow

> Auto-generated: 2026-05-12

## Overview

The data-management API is a **pass-through orchestration layer** — it does not
persist data itself but routes requests between the browser SPA and backend
services, enriching responses with canonical metadata along the way.

## Inbound Data

| Source | Format | Trigger | Destination |
|--------|--------|---------|-------------|
| Data-management SPA | JSON over HTTP | User action (submit job, request embed/predict) | Scraper / Embedding / Model service |
| Gateway | JSON over HTTP | Proxy routing | Same upstream services |
| Render health probe | HTTP GET | Timer (30s interval) | Health aggregation logic |

## Internal Processing

| Stage | Input | Transformation | Output |
|-------|-------|----------------|--------|
| Job proxy | Raw HTTP request (method, path, body, headers) | `ScraperClient.forward_jobs()` relays verbatim; POST responses enriched with `source_of_truth`, `canonical_visibility_updated_at` | Upstream response mirrored to caller |
| Embed delegation | `EmbedRequest { text, model_version }` | Route to Modal SDK or HTTP; enrich response metadata | `EmbedResponse { embedding, model_version }` |
| Predict delegation | `PredictRequest { text, model_version }` | Route to Modal SDK or HTTP | `PredictResponse { label, score, model_version }` |
| Health aggregation | GET request | Validate `DATABASE_URL`, call scraper health | JSON health status |
| Corpus conflict resolution | Two corpus records with timestamps | `resolve_corpus_write_conflict()` — last-writer-wins by `updated_at`, tie-break by `document_id` | Winning record |

## Outbound Data

| Destination | Format | Trigger | Content |
|-------------|--------|---------|---------|
| Data-management SPA | JSON over HTTP | Response to inbound request | Job status, embed vectors, predictions |
| Scraper service | JSON over HTTP | `/jobs` proxy or health check | Forwarded request payload |
| Embedding service | JSON / Modal RPC | `/embed` request | Text and model version |
| Model service | JSON / Modal RPC | `/predict` request | Text and model version |

## Data Persistence

| Store | Technology | What's Stored | Retention |
|-------|------------|---------------|-----------|
| Render PostgreSQL | PostgreSQL 16 (vecinita-postgres) | Scraper pipeline state (jobs, URLs, content, chunks, embeddings) | Indefinite — managed by scraper service |

The DM API itself stores **nothing** — all persistence is delegated to the
scraper service which writes to the shared Postgres database. The DM API only
validates that `DATABASE_URL` points to a canonical Postgres instance.

## Diagrams

- [Data Flow Diagram](diagrams/data-flow.md)

## Related Documents

- [Data Models](02-data-models.md)
- [Integration Points](03-integration-points.md)
