import { afterEach, describe, expect, it, vi } from 'vitest';

describe('scraper-config', () => {
  afterEach(() => {
    vi.unstubAllEnvs();
    vi.resetModules();
  });

  it('is configured from runtime env in this app context', async () => {
    const { getScraperConfigDiagnostic, isScraperConfigured, scraperRuntimeConfig } = await import('./scraper-config');

    expect(typeof scraperRuntimeConfig.apiBaseUrl).toBe('string');
    expect(typeof scraperRuntimeConfig.defaultUserId).toBe('string');
    expect(typeof isScraperConfigured()).toBe('boolean');

    const diagnostic = getScraperConfigDiagnostic();
    expect(typeof diagnostic.hasDeprecatedBrowserAuthEnv).toBe('boolean');
    expect(typeof diagnostic.hasDirectModalWebApiBase).toBe('boolean');
    expect(typeof diagnostic.hasModalTokenViteKeys).toBe('boolean');
    expect(Array.isArray(diagnostic.warnings)).toBe(true);
  });

  it('falls back to the local data-management API on localhost', async () => {
    const { getScraperConfigDiagnostic, scraperRuntimeConfig } = await import('./scraper-config');

    expect(scraperRuntimeConfig.apiBaseUrl).toBe('http://localhost:8005');

    const diagnostic = getScraperConfigDiagnostic();
    expect(diagnostic.configured).toBe(true);
    expect(diagnostic.validUrl).toBe(true);
    expect(diagnostic.apiBaseUrl).toBe('http://localhost:8005');
  });

  it('flags *.modal.run as DM API base (SC-001 / SC-005)', async () => {
    vi.stubEnv('VITE_DM_API_BASE_URL', 'https://vecinita--scraper.modal.run');
    vi.resetModules();
    const {
      browserDmHttpApiBase,
      getScraperConfigDiagnostic,
      getScraperHealthUrl,
      isScraperConfigured,
      scraperJobsApiRoot,
    } = await import('./scraper-config');
    const d = getScraperConfigDiagnostic();
    expect(d.hasDirectModalWebApiBase).toBe(true);
    expect(d.issues.some((x) => x.includes('modal.run'))).toBe(true);
    expect(browserDmHttpApiBase()).toBe('');
    expect(getScraperHealthUrl()).toBeNull();
    expect(scraperJobsApiRoot()).toBe('');
    expect(isScraperConfigured()).toBe(false);
  });

  it('allows https DM API base (non-Modal) for browser HTTP(S) calls', async () => {
    vi.stubEnv('VITE_DM_API_BASE_URL', 'https://dm-api.internal.example.com/path/');
    vi.resetModules();
    const { browserDmHttpApiBase, getScraperHealthUrl, isScraperConfigured, scraperJobsApiRoot } =
      await import('./scraper-config');
    expect(browserDmHttpApiBase()).toBe('https://dm-api.internal.example.com/path');
    expect(getScraperHealthUrl()).toBe('https://dm-api.internal.example.com/path/health');
    expect(scraperJobsApiRoot()).toBe('https://dm-api.internal.example.com/path/jobs');
    expect(isScraperConfigured()).toBe(true);
  });

  it('flags VITE_* keys that embed MODAL_TOKEN (SC-005)', async () => {
    vi.stubEnv('VITE_DM_API_BASE_URL', 'http://localhost:8005');
    vi.stubEnv('VITE_MODAL_TOKEN_ID', 'should-not-ship');
    vi.resetModules();
    const { getScraperConfigDiagnostic } = await import('./scraper-config');
    const d = getScraperConfigDiagnostic();
    expect(d.hasModalTokenViteKeys).toBe(true);
    expect(d.issues.some((x) => x.includes('VITE_MODAL_TOKEN_ID'))).toBe(true);
  });
});
