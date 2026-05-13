-- Rollback for schema-per-service migration
-- Moves all tables back to public schema and drops service schemas.

BEGIN;

-- Move gateway tables back
ALTER TABLE IF EXISTS gateway.scraping_jobs SET SCHEMA public;
ALTER TABLE IF EXISTS gateway.job_status SET SCHEMA public;
ALTER TABLE IF EXISTS gateway.api_keys SET SCHEMA public;
ALTER TABLE IF EXISTS gateway.rate_limits SET SCHEMA public;

-- Move agent tables back
ALTER TABLE IF EXISTS agent.conversations SET SCHEMA public;
ALTER TABLE IF EXISTS agent.messages SET SCHEMA public;
ALTER TABLE IF EXISTS agent.vectors SET SCHEMA public;
ALTER TABLE IF EXISTS agent.tool_results SET SCHEMA public;
ALTER TABLE IF EXISTS agent.embeddings_metadata SET SCHEMA public;
ALTER TABLE IF EXISTS agent.document_embeddings SET SCHEMA public;

-- Move data management tables back
ALTER TABLE IF EXISTS data_mgmt.documents SET SCHEMA public;
ALTER TABLE IF EXISTS data_mgmt.corpus_items SET SCHEMA public;
ALTER TABLE IF EXISTS data_mgmt.metadata SET SCHEMA public;
ALTER TABLE IF EXISTS data_mgmt.sources SET SCHEMA public;

-- Move shared tables back
ALTER TABLE IF EXISTS shared.migrations_log SET SCHEMA public;
ALTER TABLE IF EXISTS shared.feature_flags SET SCHEMA public;

-- Drop schemas (only if empty)
DROP SCHEMA IF EXISTS gateway CASCADE;
DROP SCHEMA IF EXISTS agent CASCADE;
DROP SCHEMA IF EXISTS data_mgmt CASCADE;
DROP SCHEMA IF EXISTS shared CASCADE;

COMMIT;
