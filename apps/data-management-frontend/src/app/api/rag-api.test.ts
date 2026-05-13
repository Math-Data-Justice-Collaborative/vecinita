import { beforeEach, describe, expect, it, vi } from 'vitest';

async function importMockModeClient() {
  vi.resetModules();
  vi.doMock('./scraper-config', () => ({
    browserDmHttpApiBase: () => '',
    scraperRuntimeConfig: {
      apiBaseUrl: '',
      defaultUserId: 'test-user',
    },
    scraperJobsApiRoot: () => '',
  }));

  return import('./rag-api');
}

async function importRemoteModeClient() {
  vi.resetModules();
  vi.doMock('./scraper-config', () => {
    const base = 'https://scraper.example.com';
    return {
      browserDmHttpApiBase: () => base,
      scraperRuntimeConfig: {
        apiBaseUrl: base,
        defaultUserId: 'test-user',
      },
      scraperJobsApiRoot: () => `${base}/jobs`,
    };
  });

  return import('./rag-api');
}

async function importDmJobsRagApi() {
  vi.resetModules();
  vi.doMock('./scraper-config', () => {
    const dm = 'http://127.0.0.1:8005';
    return {
      browserDmHttpApiBase: () => dm,
      scraperRuntimeConfig: {
        apiBaseUrl: dm,
        defaultUserId: 'job-user',
      },
      scraperJobsApiRoot: () => `${dm}/jobs`,
    };
  });

  return import('./rag-api');
}

describe('ragApi (mock mode)', () => {
  beforeEach(() => {
    vi.restoreAllMocks();
    localStorage.clear();
  });

  it('stores and returns scrape jobs created in mock mode', async () => {
    const { ragApi } = await importMockModeClient();

    const created = await ragApi.scrapeUrl({
      url: 'https://example.com',
      depth: 1,
    });

    expect(created.status).toBe('queued');

    const jobsResponse = await ragApi.getScrapeJobs();
    expect(jobsResponse.jobs).toHaveLength(1);
    expect(jobsResponse.jobs[0]).toMatchObject({
      job_id: created.job_id,
      url: 'https://example.com',
      status: 'queued',
      backend_status: 'pending',
    });
  });

  it('throws when requesting scrape status for an unknown mock job', async () => {
    const { ragApi } = await importMockModeClient();

    await expect(ragApi.getScrapeStatus('missing-job')).rejects.toThrow('Job not found');
  });

  it('filters documents in mock corpus by search, type, and tags', async () => {
    const { ragApi } = await importMockModeClient();

    const response = await ragApi.getDocuments({
      search: 'food bank',
      resource_type: 'website',
      tags: ['food-assistance'],
      page: 1,
      limit: 10,
    });

    expect(response.total).toBe(1);
    expect(response.documents[0].title).toContain('RI Food Bank');
  });

  it('returns empty known jobs when local storage is corrupted', async () => {
    const { ragApi } = await importMockModeClient();
    localStorage.setItem('vecinita.scrape-jobs', '{broken-json');

    const response = await ragApi.getScrapeJobs();
    expect(response.jobs).toEqual([]);
  });
});

describe('ragApi (remote mode)', () => {
  beforeEach(() => {
    vi.restoreAllMocks();
    localStorage.clear();
  });

  it('lists scrape jobs via data-management API /jobs base', async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({ jobs: [], user_id: 'job-user', limit: 100, total: 0 }),
    } as Response);
    vi.stubGlobal('fetch', fetchMock);

    const { ragApi } = await importDmJobsRagApi();
    await ragApi.getScrapeJobs();

    expect(String(fetchMock.mock.calls[0]?.[0])).toMatch(
      /^http:\/\/127\.0\.0\.1:8005\/jobs\?/,
    );
  });

  it('does not add browser modal auth headers for request-based calls', async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({
        job_id: 'job-1',
        previous_status: 'pending',
        new_status: 'cancelled',
      }),
    } as Response);
    vi.stubGlobal('fetch', fetchMock);

    const { ragApi } = await importRemoteModeClient();
    await ragApi.cancelScrapeJob('job-1');

    expect(fetchMock).toHaveBeenCalledWith(
      'https://scraper.example.com/jobs/job-1/cancel',
      expect.objectContaining({
        method: 'POST',
        headers: expect.any(Headers),
      }),
    );

    const headers = fetchMock.mock.calls[0][1].headers as Headers;
    expect(headers.get('Modal-Key')).toBeNull();
    expect(headers.get('Modal-Secret')).toBeNull();
  });

  it('surfaces operator-safe message when error body is non-json', async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: false,
      status: 502,
      statusText: 'Bad Gateway',
      json: async () => {
        throw new Error('not-json');
      },
    } as unknown as Response);
    vi.stubGlobal('fetch', fetchMock);

    const { ragApi } = await importRemoteModeClient();

    await expect(ragApi.cancelScrapeJob('job-2')).rejects.toThrow(/upstream worker/i);
  });

  it('returns live stats from documents when documents endpoint is available', async () => {
    const fetchMock = vi.fn().mockImplementation(async (input: RequestInfo | URL) => {
      const url = String(input);

      if (url.includes('/documents?')) {
        return {
          ok: true,
          json: async () => ({
            documents: [
              {
                id: 'doc-1',
                title: 'Housing Guide',
                description: 'Community housing guide',
                url: 'https://example.com/housing',
                resource_type: 'document',
                format: 'PDF',
                language: 'English',
                organization: 'Vecina',
                embedding_status: 'completed',
                created_at: '2025-01-01T00:00:00.000Z',
                updated_at: '2025-01-01T00:00:00.000Z',
              },
            ],
            total: 1,
            page: 1,
          }),
        } as Response;
      }

      if (url.includes('/jobs?')) {
        return {
          ok: true,
          json: async () => ({ jobs: [] }),
        } as Response;
      }

      return {
        ok: false,
        status: 404,
        statusText: 'Not Found',
        json: async () => ({ message: 'Not Found' }),
      } as Response;
    });
    vi.stubGlobal('fetch', fetchMock);

    const { ragApi } = await importRemoteModeClient();
    const stats = await ragApi.getStats();

    expect(stats.total_documents).toBe(1);
    expect(stats.documents_by_type.document).toBe(1);
    expect(stats.warmup_status).toBe('live');
  });

  it('falls back to job-derived stats when documents endpoint is unavailable', async () => {
    const fetchMock = vi.fn().mockImplementation(async (input: RequestInfo | URL) => {
      const url = String(input);

      if (url.includes('/documents?')) {
        return {
          ok: false,
          status: 503,
          statusText: 'Service Unavailable',
          json: async () => ({ message: 'cold start' }),
        } as Response;
      }

      if (url.includes('/jobs?')) {
        return {
          ok: true,
          json: async () => ({
            jobs: [
              {
                id: 'job-1',
                user_id: 'u1',
                status: 'completed',
                created_at: '2025-01-02T00:00:00.000Z',
                updated_at: '2025-01-02T00:10:00.000Z',
                url: 'https://example.com/resource',
                embedding_count: 12,
              },
            ],
          }),
        } as Response;
      }

      return {
        ok: false,
        status: 404,
        statusText: 'Not Found',
        json: async () => ({ message: 'Not Found' }),
      } as Response;
    });
    vi.stubGlobal('fetch', fetchMock);

    const { ragApi } = await importRemoteModeClient();
    const stats = await ragApi.getStats();

    expect(stats.total_documents).toBe(1);
    expect(stats.total_embeddings).toBe(12);
    expect(stats.documents_by_type.website).toBe(1);
    expect(stats.warmup_status).toBe('fallback');
    expect(stats.warmup_message).toContain('Document endpoint unavailable');
  });
});
