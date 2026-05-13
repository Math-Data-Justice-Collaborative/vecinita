import { expect, test, type Page } from '@playwright/test';

const adminEmail = process.env.E2E_ADMIN_EMAIL ?? process.env.VITE_BOOTSTRAP_ADMIN_EMAIL;
const adminPassword = process.env.E2E_ADMIN_PASSWORD ?? process.env.VITE_BOOTSTRAP_ADMIN_PASSWORD;

async function signInAsAdmin(page: Page) {
  await page.goto('/login');
  await page.getByLabel('Email').fill(adminEmail as string);
  await page.getByLabel('Password').fill(adminPassword as string);
  await page.getByRole('button', { name: 'Sign In' }).click();
  await page.waitForURL('**/');
}

test.describe('Dashboard cold-start handling', () => {
  test('shows warmup then recovered state when backend responds slowly', async ({ page }) => {
    test.skip(
      !adminEmail || !adminPassword,
      'Set E2E_ADMIN_EMAIL and E2E_ADMIN_PASSWORD to run authenticated dashboard E2E tests.',
    );

    await page.addInitScript(() => {
      const originalFetch = window.fetch.bind(window);
      window.fetch = async (input: RequestInfo | URL, init?: RequestInit) => {
        const url = typeof input === 'string' ? input : input instanceof URL ? input.toString() : input.url;

        if (url.includes('/documents?')) {
          await new Promise((resolve) => {
            setTimeout(resolve, 1800);
          });

          return new Response(
            JSON.stringify({
              documents: [
                {
                  id: 'doc-1',
                  title: 'Warmup Resource',
                  description: 'Recovered after backend warmup',
                  url: 'https://example.com',
                  resource_type: 'website',
                  format: 'HTML',
                  language: 'English',
                  organization: 'Vecinita',
                  embedding_status: 'completed',
                  created_at: new Date().toISOString(),
                  updated_at: new Date().toISOString(),
                },
              ],
              total: 1,
              page: 1,
            }),
            {
              status: 200,
              headers: { 'Content-Type': 'application/json' },
            },
          );
        }

        if (url.includes('/jobs?')) {
          return new Response(
            JSON.stringify({ jobs: [] }),
            {
              status: 200,
              headers: { 'Content-Type': 'application/json' },
            },
          );
        }

        return originalFetch(input, init);
      };
    });

    await signInAsAdmin(page);

    await expect(page.getByText('Connected after warmup. Live data is now available.')).toBeVisible();
    await expect(page.getByText('Total Documents')).toBeVisible();
    await expect(
      page.locator('div').filter({ hasText: /^Total Documents$/ }).locator('..').locator('.text-2xl.font-bold'),
    ).toHaveText('1');
  });

  test('shows fallback state when document endpoint fails but job data is available', async ({ page }) => {
    test.skip(
      !adminEmail || !adminPassword,
      'Set E2E_ADMIN_EMAIL and E2E_ADMIN_PASSWORD to run authenticated dashboard E2E tests.',
    );

    await page.addInitScript(() => {
      const originalFetch = window.fetch.bind(window);
      window.fetch = async (input: RequestInfo | URL, init?: RequestInit) => {
        const url = typeof input === 'string' ? input : input instanceof URL ? input.toString() : input.url;

        if (url.includes('/documents?')) {
          return new Response(
            JSON.stringify({ message: 'cold start' }),
            {
              status: 503,
              statusText: 'Service Unavailable',
              headers: { 'Content-Type': 'application/json' },
            },
          );
        }

        if (url.includes('/jobs?')) {
          return new Response(
            JSON.stringify({
              jobs: [
                {
                  job_id: 'job-1',
                  status: 'completed',
                  created_at: new Date().toISOString(),
                  updated_at: new Date().toISOString(),
                  url: 'https://example.com/fallback',
                  embedding_count: 5,
                },
              ],
              total: 1,
            }),
            {
              status: 200,
              headers: { 'Content-Type': 'application/json' },
            },
          );
        }

        return originalFetch(input, init);
      };
    });

    await signInAsAdmin(page);

    await expect(
      page.getByText('Document endpoint unavailable; showing scraper-job derived stats.'),
    ).toBeVisible();
    await expect(page.getByText('Total Documents')).toBeVisible();
    await expect(
      page.locator('div').filter({ hasText: /^Total Documents$/ }).locator('..').locator('.text-2xl.font-bold'),
    ).toHaveText('1');
  });
});
