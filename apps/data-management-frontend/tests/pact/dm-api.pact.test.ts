/**
 * Pact consumer: DM SPA ↔ data-management API over HTTP(S) (`VITE_DM_API_BASE_URL` → `/health`, `/jobs`, …).
 *
 * Covers:
 * - Health-style check: ``GET {origin}/health``
 * - Auth probe: ``GET {origin}/jobs?limit=1`` with ``Authorization: Bearer …`` (see ``validateApiKey``)
 * - Corpus: ``GET /documents?...``
 * - Scraper jobs: ``GET /jobs``, ``POST /jobs``, ``GET /jobs/{id}``, ``POST /jobs/{id}/cancel``
 *
 * The mock provider URL is always a non-Modal host; the app must never treat ``*.modal.run`` as
 * a browser-accessible DM API base (SC-001 / SC-005).
 */
import { afterEach, describe, expect, it, vi } from 'vitest';
import { PactV3 } from '@pact-foundation/pact';
import {
  DM_API_PACT_CONSUMER,
  DM_SCRAPER_API_PROVIDER,
  resolveDmPactLogLevel,
  resolveDmPactOutputDir,
} from './pactSetup';

const jobsListBody = {
  user_id: 'frontend-user',
  limit: 100,
  jobs: [
    {
      id: 'pact-job-1',
      user_id: 'frontend-user',
      status: 'completed',
      created_at: '2026-01-01T00:00:00.000Z',
      updated_at: '2026-01-01T00:05:00.000Z',
      url: 'https://example.com/pact',
    },
  ],
  total: 1,
};

const jobStatusBody = {
  job_id: 'pact-submit-1',
  status: 'pending',
  created_at: '2026-01-01T00:00:00.000Z',
  updated_at: '2026-01-01T00:00:01.000Z',
  chunk_count: 0,
  crawl_url_count: 0,
  embedding_count: 0,
  current_step: 'pending',
  progress_pct: 5,
  url: 'https://example.com/pact-submit',
};

const documentsListBody = {
  documents: [
    {
      id: 'doc-pact-1',
      title: 'Pact corpus row',
      description: 'Contract fixture',
      url: 'https://example.com/doc',
      resource_type: 'document',
      format: 'PDF',
      language: 'en',
      organization: 'Vecinita',
      embedding_status: 'completed',
      source_of_truth: 'postgres',
      canonical_visibility_updated_at: '2026-01-01T00:00:00.000Z',
      created_at: '2026-01-01T00:00:00.000Z',
      updated_at: '2026-01-01T00:00:00.000Z',
      tags: [],
    },
  ],
  total: 1,
  page: 1,
};

const probeJobsBody = {
  jobs: [],
  user_id: 'frontend-user',
  limit: 1,
  total: 0,
};

const pactEnvKeys = [
  'VITE_DM_API_BASE_URL',
  'VITE_DEFAULT_SCRAPER_USER_ID',
] as const;

const PROBE_TOKEN = 'pact-probe-token';

afterEach(() => {
  for (const key of pactEnvKeys) {
    delete process.env[key];
  }
  vi.unstubAllEnvs();
  vi.resetModules();
});

describe('Pact: dm-frontend → vecinita-data-management-api (direct)', () => {
  it('covers /health, auth probe /jobs, /documents, and /jobs CRUD-style calls', async () => {
    const pact = new PactV3({
      consumer: DM_API_PACT_CONSUMER,
      provider: DM_SCRAPER_API_PROVIDER,
      dir: resolveDmPactOutputDir(),
      logLevel: resolveDmPactLogLevel(),
    });

    await pact
      .addInteraction({
        uponReceiving: 'a health check against the DM API origin',
        withRequest: {
          method: 'GET',
          path: '/health',
        },
        willRespondWith: {
          status: 200,
          headers: { 'Content-Type': 'application/json' },
          body: { status: 'ok', service: 'dm-scraper' },
        },
      })
      .addInteraction({
        uponReceiving: 'an API key probe (GET /jobs?limit=1 with bearer token)',
        withRequest: {
          method: 'GET',
          path: '/jobs',
          query: { limit: '1' },
          headers: { Authorization: `Bearer ${PROBE_TOKEN}` },
        },
        willRespondWith: {
          status: 200,
          headers: { 'Content-Type': 'application/json' },
          body: probeJobsBody,
        },
      })
      .addInteraction({
        uponReceiving: 'list corpus documents (GET /documents)',
        withRequest: {
          method: 'GET',
          path: '/documents',
          query: { page: '1', limit: '100' },
          headers: { 'Content-Type': 'application/json' },
        },
        willRespondWith: {
          status: 200,
          headers: { 'Content-Type': 'application/json' },
          body: documentsListBody,
        },
      })
      .addInteraction({
        uponReceiving: 'a scrape job list request (GET /jobs)',
        withRequest: {
          method: 'GET',
          path: '/jobs',
          query: {
            user_id: 'frontend-user',
            limit: '100',
          },
          headers: { 'Content-Type': 'application/json' },
        },
        willRespondWith: {
          status: 200,
          headers: { 'Content-Type': 'application/json' },
          body: jobsListBody,
        },
      })
      .addInteraction({
        uponReceiving: 'submit scrape job via POST /jobs on the DM API',
        withRequest: {
          method: 'POST',
          path: '/jobs',
          headers: { 'Content-Type': 'application/json' },
          body: {
            url: 'https://example.com/pact-submit',
            user_id: 'frontend-user',
            crawl_config: {
              max_depth: 1,
              headless: true,
              wait_for_content: true,
              include_links: false,
              include_images: false,
            },
            metadata: {
              auto_tag: false,
              source: 'vecinita-data-management-frontend',
            },
          },
        },
        willRespondWith: {
          status: 200,
          headers: { 'Content-Type': 'application/json' },
          body: {
            job_id: 'pact-submit-1',
            status: 'pending',
            created_at: '2026-01-01T00:00:00.000Z',
            url: 'https://example.com/pact-submit',
          },
        },
      })
      .addInteraction({
        uponReceiving: 'poll scrape job status (GET /jobs/{job_id})',
        withRequest: {
          method: 'GET',
          path: '/jobs/pact-submit-1',
          headers: { 'Content-Type': 'application/json' },
        },
        willRespondWith: {
          status: 200,
          headers: { 'Content-Type': 'application/json' },
          body: jobStatusBody,
        },
      })
      .addInteraction({
        uponReceiving: 'cancel scrape job (POST /jobs/{job_id}/cancel)',
        withRequest: {
          method: 'POST',
          path: '/jobs/pact-submit-1/cancel',
          headers: { 'Content-Type': 'application/json' },
        },
        willRespondWith: {
          status: 200,
          headers: { 'Content-Type': 'application/json' },
          body: {
            job_id: 'pact-submit-1',
            previous_status: 'pending',
            new_status: 'cancelled',
          },
        },
      })
      .executeTest(async (mockServer) => {
        const base = mockServer.url.replace(/\/$/, '');
        expect(new URL(base).hostname.toLowerCase().endsWith('modal.run')).toBe(false);

        process.env.VITE_DM_API_BASE_URL = base;
        process.env.VITE_DEFAULT_SCRAPER_USER_ID = 'frontend-user';
        vi.resetModules();

        const { getScraperHealthUrl } = await import('../../src/app/api/scraper-config');
        const healthUrl = getScraperHealthUrl();
        expect(healthUrl).toBe(`${base}/health`);

        const healthResponse = await fetch(healthUrl!);
        expect(healthResponse.ok).toBe(true);

        const { validateApiKey } = await import('../../src/app/auth/apiKeyAuth');
        await expect(validateApiKey(PROBE_TOKEN)).resolves.toBeUndefined();

        const { ragApi } = await import('../../src/app/api/rag-api');
        const docs = await ragApi.getDocuments({ page: 1, limit: 100 });
        expect(docs.total).toBe(1);
        expect(docs.documents[0]?.id).toBe('doc-pact-1');
        expect((docs.documents[0] as Record<string, unknown>)?.source_of_truth).toBe('postgres');

        const jobs = await ragApi.getScrapeJobs();
        expect(jobs.jobs).toHaveLength(1);
        expect(jobs.jobs[0]?.job_id).toBe('pact-job-1');

        const created = await ragApi.scrapeUrl({
          url: 'https://example.com/pact-submit',
          depth: 0,
          user_id: 'frontend-user',
        });
        expect(created.job_id).toBe('pact-submit-1');

        const status = await ragApi.getScrapeStatus('pact-submit-1');
        expect(status.job_id).toBe('pact-submit-1');
        expect(status.backend_status).toBe('pending');

        const cancelled = await ragApi.cancelScrapeJob('pact-submit-1');
        expect(cancelled.new_status).toBe('cancelled');
      });
  });
});
