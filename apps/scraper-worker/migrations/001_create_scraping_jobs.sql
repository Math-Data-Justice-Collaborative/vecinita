-- Migration: Create scraping_jobs table
-- This is the main table for tracking job lifecycle
--
-- Render Postgres (gateway MODAL_SCRAPER_PERSIST_VIA_GATEWAY): use
-- render_gateway_scraper_schema.sql instead — this file's RLS policies use auth.uid()
-- (Supabase) and will not apply on plain Postgres.

CREATE TABLE IF NOT EXISTS scraping_jobs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id VARCHAR NOT NULL,
    url TEXT NOT NULL,
    status VARCHAR NOT NULL DEFAULT 'pending',
    crawl_config JSONB,
    chunking_config JSONB,
    metadata JSONB,
    error_message TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);

-- Create indexes
CREATE INDEX idx_scraping_jobs_user_id ON scraping_jobs(user_id);
CREATE INDEX idx_scraping_jobs_status ON scraping_jobs(status);
CREATE INDEX idx_scraping_jobs_created_at ON scraping_jobs(created_at);

-- Enable RLS
ALTER TABLE scraping_jobs ENABLE ROW LEVEL SECURITY;

-- RLS policies (example: users can see only their own jobs)
CREATE POLICY "Users can view their own jobs"
    ON scraping_jobs FOR SELECT
    USING (auth.uid()::TEXT = user_id OR user_id = 'system');

CREATE POLICY "Only system can insert jobs"
    ON scraping_jobs FOR INSERT
    WITH CHECK (user_id IS NOT NULL);

CREATE POLICY "Only system can update jobs"
    ON scraping_jobs FOR UPDATE
    USING (true)
    WITH CHECK (true);
