import { expect, test, type Page } from '@playwright/test';

const adminEmail = process.env.E2E_ADMIN_EMAIL ?? process.env.VITE_BOOTSTRAP_ADMIN_EMAIL;
const adminPassword = process.env.E2E_ADMIN_PASSWORD ?? process.env.VITE_BOOTSTRAP_ADMIN_PASSWORD;

async function signInAsAdmin(page: Page): Promise<void> {
  await page.goto('/login');
  await page.getByLabel('Email').fill(adminEmail as string);
  await page.getByLabel('Password').fill(adminPassword as string);
  await page.getByRole('button', { name: 'Sign In' }).click();
  await page.waitForURL('**/');
  await expect(page.getByRole('heading', { name: 'Dashboard' })).toBeVisible();
  await expect(page.getByText('Loading session...')).toHaveCount(0);
}

async function navigateCoreTabs(page: Page): Promise<void> {
  await page.getByRole('link', { name: 'Dashboard' }).click();
  await expect(page.getByRole('heading', { name: 'Dashboard' })).toBeVisible();

  await page.getByRole('link', { name: 'Corpus' }).click();
  await expect(page.getByRole('heading', { name: 'Document Corpus' })).toBeVisible();

  await page.getByRole('link', { name: 'Tags & Categories' }).click();
  await expect(page.getByRole('heading', { name: 'Tags & Categories' })).toBeVisible();

  await page.getByRole('link', { name: 'Scrape Jobs' }).click();
  await expect(page.getByRole('heading', { name: 'Scrape Jobs' })).toBeVisible();
}

test.describe('Scraper journey (mocked dev flow)', () => {
  test('login -> scrape -> jobs -> tabs @pr @mocked', async ({ page }) => {
    test.skip(
      !adminEmail || !adminPassword,
      'Set E2E_ADMIN_EMAIL and E2E_ADMIN_PASSWORD to run authenticated scraper journey tests.',
    );

    const jobs: Array<{
      job_id: string;
      url: string;
      status: 'pending' | 'processing' | 'completed';
      created_at: string;
      updated_at: string;
      embedding_count: number;
      crawl_url_count: number;
      chunk_count: number;
    }> = [];

    await page.route('**/documents**', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ documents: [], total: 0, page: 1 }),
      });
    });

    await page.route('**/jobs**', async (route) => {
      const request = route.request();
      const url = new URL(request.url());
      const pathname = url.pathname;

      if (request.method() === 'POST' && pathname.endsWith('/jobs')) {
        const payload = (await request.postDataJSON()) as { url?: string };
        const created = {
          job_id: `job-${Date.now()}`,
          url: payload.url ?? 'https://example.com',
          status: 'processing' as const,
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString(),
          embedding_count: 3,
          crawl_url_count: 2,
          chunk_count: 4,
        };
        jobs.unshift(created);

        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            job_id: created.job_id,
            status: created.status,
            created_at: created.created_at,
            url: created.url,
          }),
        });
        return;
      }

      if (request.method() === 'GET' && pathname.endsWith('/jobs')) {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            user_id: 'e2e-user',
            limit: 100,
            total: jobs.length,
            jobs: jobs.map((job) => ({
              job_id: job.job_id,
              status: job.status,
              created_at: job.created_at,
              updated_at: job.updated_at,
              url: job.url,
              progress_pct: 50,
              current_step: 'processing',
              crawl_url_count: job.crawl_url_count,
              chunk_count: job.chunk_count,
              embedding_count: job.embedding_count,
            })),
          }),
        });
        return;
      }

      if (request.method() === 'GET' && /\/jobs\/[^/]+$/.test(pathname)) {
        const jobId = pathname.split('/').pop() as string;
        const job = jobs.find((entry) => entry.job_id === jobId);

        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            job_id: job?.job_id ?? jobId,
            status: 'processing',
            progress_pct: 65,
            current_step: 'embedding',
            error_message: null,
            updated_at: new Date().toISOString(),
            created_at: job?.created_at ?? new Date().toISOString(),
            crawl_url_count: job?.crawl_url_count ?? 2,
            chunk_count: job?.chunk_count ?? 4,
            embedding_count: job?.embedding_count ?? 3,
            url: job?.url ?? 'https://example.com',
          }),
        });
        return;
      }

      await route.continue();
    });

    await signInAsAdmin(page);

    await page.getByRole('link', { name: 'Add Document/URL' }).click();
    await expect(page.getByRole('heading', { name: 'Add to Corpus' })).toBeVisible();

    await page.getByRole('tab', { name: 'Upload File' }).click();
    await expect(page.getByRole('heading', { name: 'Upload Document' })).toBeVisible();
    await page.getByRole('tab', { name: 'Manual Entry' }).click();
    await expect(page.getByRole('heading', { name: 'Manual Entry' })).toBeVisible();
    await page.getByRole('tab', { name: 'Scrape URL' }).click();
    await expect(page.getByRole('heading', { name: 'Scrape Website' })).toBeVisible();

    const targetUrl = 'https://example.com/mock-journey';
    await page.getByLabel('URL to Scrape *').fill(targetUrl);
    await page.getByRole('button', { name: 'Start Scraping Job' }).click();

    await page.waitForURL('**/scrape-jobs');
    await expect(page.getByRole('heading', { name: 'Scrape Jobs' })).toBeVisible();
    await expect(page.getByText(targetUrl)).toBeVisible();

    await page.getByText(targetUrl).click();
    await expect(page.getByText('Job Details')).toBeVisible();
    await expect(page.getByText(/Backend stage: embedding/i)).toBeVisible();

    await navigateCoreTabs(page);
  });
});

test.describe('Scraper journey (live API flow)', () => {
  test('login -> live scrape job -> jobs tab @live', async ({ page }) => {
    test.setTimeout(180_000);

    test.skip(
      !adminEmail || !adminPassword,
      'Set E2E_ADMIN_EMAIL and E2E_ADMIN_PASSWORD to run authenticated scraper journey tests.',
    );

    await signInAsAdmin(page);

    await page.getByRole('link', { name: 'Add Document/URL' }).click();
    await expect(page.getByRole('heading', { name: 'Add to Corpus' })).toBeVisible();

    const liveUrl = 'https://example.com/live-journey';
    await page.getByRole('tab', { name: 'Scrape URL' }).click();
    await page.getByLabel('URL to Scrape *').fill(liveUrl);

    const createJobResponsePromise = page.waitForResponse(
      (response) => response.url().includes('/jobs') && response.request().method() === 'POST',
      { timeout: 120_000 },
    );

    await page.getByRole('button', { name: 'Start Scraping Job' }).click();

    const createJobResponse = await createJobResponsePromise;
    const createJobBody = await createJobResponse.text();
    const requestHeaders = createJobResponse.request().headers();
    expect(requestHeaders['modal-key']).toBeUndefined();
    expect(requestHeaders['modal-secret']).toBeUndefined();

    expect(
      createJobResponse.ok(),
      `Scrape job creation failed (${createJobResponse.status()}): ${createJobBody}`,
    ).toBe(true);

    await page.waitForURL('**/scrape-jobs', { timeout: 120_000 });
    await expect(page.getByRole('heading', { name: 'Scrape Jobs' })).toBeVisible();

    await expect(page.getByText(liveUrl)).toBeVisible({ timeout: 30_000 });
    await navigateCoreTabs(page);
  });
});
