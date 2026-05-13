import { describe, expect, it } from 'vitest';

const SCRAPER_PROXY_URL = process.env.VECINA_SCRAPER_PROXY_URL
  || process.env.VECINITA_SCRAPER_PROXY_URL
  || process.env.VITE_DM_API_BASE_URL
  || '';
const isProxyTarget = /functions\/v1\/server|\/scraper(\/|$)/.test(SCRAPER_PROXY_URL);

const STRICT = process.env.VECINA_STRICT_MODAL_TEST === 'true';
const hasRequiredEnv = Boolean(SCRAPER_PROXY_URL && isProxyTarget);
const integrationDescribe = hasRequiredEnv ? describe : describe.skip;

async function sleep(ms: number) {
  await new Promise((resolve) => setTimeout(resolve, ms));
}

integrationDescribe('Scraper proxy integration', () => {
  it('reports proxy health endpoint', async () => {
    const baseUrl = SCRAPER_PROXY_URL.replace(/\/+$/, '');
    const response = await fetch(`${baseUrl}/health`);

    if (STRICT) {
      expect(response.ok).toBe(true);
    } else {
      expect([200, 503]).toContain(response.status);
    }
  });

  it('creates and polls a job via proxy without browser auth headers', async () => {
    const baseUrl = SCRAPER_PROXY_URL.replace(/\/+$/, '');
    const createResponse = await fetch(`${baseUrl}/jobs`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        url: 'https://example.com',
        user_id: 'integration-user',
        crawl_config: {
          max_depth: 1,
          timeout_seconds: 60,
          headless: true,
          wait_for_content: true,
          include_links: false,
          include_images: false,
        },
        chunking_config: {
          min_size_tokens: 200,
          max_size_tokens: 400,
          overlap_ratio: 0.1,
          split_by_sentence: true,
        },
        metadata: {
          source: 'vecinita-integration-test',
        },
      }),
    });

    const createClone = createResponse.clone();
    const createPayload = await createResponse.json().catch(async () => ({
      raw: await createClone.text(),
    }));

    if (STRICT) {
      expect(createResponse.ok).toBe(true);
    } else if (!createResponse.ok) {
      const rawMessage = JSON.stringify(createPayload);
      expect([401, 403, 503]).toContain(createResponse.status);
      expect(rawMessage.length).toBeGreaterThan(0);
      return;
    }

    const created = createPayload as { job_id: string; status: string };
    expect(created.job_id).toBeTruthy();

    const terminalStatuses = new Set(['completed', 'failed', 'cancelled']);
    let lastStatus = created.status;

    for (let attempt = 0; attempt < 8; attempt += 1) {
      const statusResponse = await fetch(`${baseUrl}/jobs/${created.job_id}`, {
        headers: {},
      });

      expect(statusResponse.ok).toBe(true);
      const statusPayload = await statusResponse.json() as { status: string };
      lastStatus = statusPayload.status;

      if (terminalStatuses.has(lastStatus)) {
        break;
      }

      await sleep(1500);
    }

    if (STRICT) {
      expect(terminalStatuses.has(lastStatus)).toBe(true);
    } else {
      expect(typeof lastStatus).toBe('string');
    }

    const cancelResponse = await fetch(`${baseUrl}/jobs/${created.job_id}/cancel`, {
      method: 'POST',
      headers: {},
    });

    expect([200, 409]).toContain(cancelResponse.status);
  });
});
