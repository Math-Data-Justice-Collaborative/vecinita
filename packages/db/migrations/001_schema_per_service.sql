-- Schema-per-service migration (spec 023)
-- Creates gateway, agent, data_mgmt, and shared schemas,
-- moves tables from public into their service-owned schemas,
-- and grants cross-schema access where needed.
--
-- Run: psql $DATABASE_URL -f packages/db/migrations/001_schema_per_service.sql
-- Rollback: psql $DATABASE_URL -f packages/db/migrations/001_schema_per_service_rollback.sql

BEGIN;

-- Create service schemas
CREATE SCHEMA IF NOT EXISTS gateway;
CREATE SCHEMA IF NOT EXISTS agent;
CREATE SCHEMA IF NOT EXISTS data_mgmt;
CREATE SCHEMA IF NOT EXISTS shared;

-- Move gateway tables
ALTER TABLE IF EXISTS public.scraping_jobs SET SCHEMA gateway;
ALTER TABLE IF EXISTS public.job_status SET SCHEMA gateway;
ALTER TABLE IF EXISTS public.api_keys SET SCHEMA gateway;
ALTER TABLE IF EXISTS public.rate_limits SET SCHEMA gateway;

-- Move agent tables
ALTER TABLE IF EXISTS public.conversations SET SCHEMA agent;
ALTER TABLE IF EXISTS public.messages SET SCHEMA agent;
ALTER TABLE IF EXISTS public.vectors SET SCHEMA agent;
ALTER TABLE IF EXISTS public.tool_results SET SCHEMA agent;
ALTER TABLE IF EXISTS public.embeddings_metadata SET SCHEMA agent;

-- Move data management tables
ALTER TABLE IF EXISTS public.documents SET SCHEMA data_mgmt;
ALTER TABLE IF EXISTS public.corpus_items SET SCHEMA data_mgmt;
ALTER TABLE IF EXISTS public.metadata SET SCHEMA data_mgmt;
ALTER TABLE IF EXISTS public.sources SET SCHEMA data_mgmt;

-- Move shared tables
ALTER TABLE IF EXISTS public.migrations_log SET SCHEMA shared;
ALTER TABLE IF EXISTS public.feature_flags SET SCHEMA shared;

-- Move document_embeddings (created by embedding/indexing workers)
ALTER TABLE IF EXISTS public.document_embeddings SET SCHEMA agent;

-- Ensure pgvector stays in public
-- (No action needed - extensions are schema-independent when in public)

-- Cross-schema access grants
-- Agent reads data_mgmt.documents (RAG context retrieval)
GRANT USAGE ON SCHEMA data_mgmt TO CURRENT_USER;
GRANT SELECT ON ALL TABLES IN SCHEMA data_mgmt TO CURRENT_USER;

-- All services can read shared schema
GRANT USAGE ON SCHEMA shared TO CURRENT_USER;
GRANT SELECT ON ALL TABLES IN SCHEMA shared TO CURRENT_USER;

-- Ensure default privileges for future tables
ALTER DEFAULT PRIVILEGES IN SCHEMA gateway GRANT SELECT ON TABLES TO CURRENT_USER;
ALTER DEFAULT PRIVILEGES IN SCHEMA agent GRANT SELECT ON TABLES TO CURRENT_USER;
ALTER DEFAULT PRIVILEGES IN SCHEMA data_mgmt GRANT SELECT ON TABLES TO CURRENT_USER;
ALTER DEFAULT PRIVILEGES IN SCHEMA shared GRANT SELECT ON TABLES TO CURRENT_USER;

COMMIT;
