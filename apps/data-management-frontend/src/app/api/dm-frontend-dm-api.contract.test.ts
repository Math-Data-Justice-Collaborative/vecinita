/**
 * Contract: data-management-frontend → DM API via ``VITE_DM_API_BASE_URL`` (HTTP(S) only;
 * ``*.modal.run`` bases are blocked for browser traffic — SC-001 / SC-005).
 */
import { afterEach, describe, expect, it, vi } from 'vitest';

describe('dm-frontend → DM API (VITE_DM_API_BASE_URL)', () => {
  afterEach(() => {
    vi.unstubAllEnvs();
    vi.resetModules();
  });

  it('does not issue fetch to list jobs when the configured base is a direct *.modal.run URL', async () => {
    vi.stubEnv('VITE_DM_API_BASE_URL', 'https://vecinita--vecinita-scraper-api-fastapi.modal.run');
    vi.resetModules();

    const fetchMock = vi.fn();
    vi.stubGlobal('fetch', fetchMock);

    const { ragApi } = await import('./rag-api');
    const out = await ragApi.getScrapeJobs();

    expect(fetchMock).not.toHaveBeenCalled();
    expect(out.jobs).toEqual([]);
  });
});
