/**
 * Contract: URL shapes for data-management-frontend → DM API
 * (`/jobs/*`, `/documents`, auth probe on `/jobs?limit=1`).
 */
import { afterEach, describe, expect, it, vi } from 'vitest';

describe('dm-api routing (VITE_DM_API_BASE_URL origin)', () => {
  afterEach(() => {
    vi.unstubAllEnvs();
    vi.restoreAllMocks();
    vi.resetModules();
  });

  it('validateApiKey probes GET {origin}/jobs?limit=1 with Authorization bearer', async () => {
    vi.stubEnv('VITE_DM_API_BASE_URL', 'https://dm.example.net/api/');
    vi.resetModules();

    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => ({}),
    } as Response);
    vi.stubGlobal('fetch', fetchMock);

    const { validateApiKey } = await import('../auth/apiKeyAuth');
    await validateApiKey('my-solid-api-key-value');

    expect(fetchMock).toHaveBeenCalledTimes(1);
    const [url, init] = fetchMock.mock.calls[0] as [string | URL, RequestInit];
    expect(String(url)).toBe('https://dm.example.net/api/jobs?limit=1');
    expect(init.method).toBe('GET');
    const headers = init.headers;
    if (headers instanceof Headers) {
      expect(headers.get('Authorization')).toBe('Bearer my-solid-api-key-value');
    } else {
      expect(headers).toMatchObject({ Authorization: 'Bearer my-solid-api-key-value' });
    }
  });

  it('ragApi.getDocuments calls GET {origin}/documents with page and limit', async () => {
    vi.stubEnv('VITE_DM_API_BASE_URL', 'https://dm.example.net');
    vi.resetModules();

    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => ({ documents: [], total: 0, page: 1 }),
    } as Response);
    vi.stubGlobal('fetch', fetchMock);

    const { ragApi } = await import('./rag-api');
    await ragApi.getDocuments({ page: 1, limit: 100 });

    expect(fetchMock).toHaveBeenCalled();
    const firstUrl = String(fetchMock.mock.calls[0]?.[0] ?? '');
    expect(firstUrl).toBe('https://dm.example.net/documents?page=1&limit=100');
  });

  it('ragApi.getScrapeJobs calls GET {origin}/jobs with user_id and limit', async () => {
    vi.stubEnv('VITE_DM_API_BASE_URL', 'https://dm.example.net');
    vi.stubEnv('VITE_DEFAULT_SCRAPER_USER_ID', 'u-contract');
    vi.resetModules();

    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => ({ jobs: [], user_id: 'u-contract', limit: 100, total: 0 }),
    } as Response);
    vi.stubGlobal('fetch', fetchMock);

    const { ragApi } = await import('./rag-api');
    await ragApi.getScrapeJobs();

    const listUrl = String(fetchMock.mock.calls[0]?.[0] ?? '');
    expect(listUrl).toMatch(/^https:\/\/dm\.example\.net\/jobs\?/);
    expect(listUrl).toContain('user_id=u-contract');
    expect(listUrl).toContain('limit=100');
  });
});
