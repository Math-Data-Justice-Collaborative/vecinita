import { expect, test, type Page } from '@playwright/test';

const adminEmail = process.env.E2E_ADMIN_EMAIL ?? process.env.VITE_BOOTSTRAP_ADMIN_EMAIL;
const adminPassword = process.env.E2E_ADMIN_PASSWORD ?? process.env.VITE_BOOTSTRAP_ADMIN_PASSWORD;

async function signInAsAdmin(page: Page): Promise<void> {
  await page.goto('/login');
  await page.getByLabel('Email').fill(adminEmail as string);
  await page.getByLabel('Password').fill(adminPassword as string);
  await page.getByRole('button', { name: 'Sign In' }).click();
  await page.waitForURL('**/');
}

async function installDmApiRoutes(page: Page): Promise<void> {
  await page.route('**/health**', async (route) => {
    if (route.request().method() !== 'GET') {
      await route.continue();
      return;
    }
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({ status: 'ok', service: 'dm-scraper' }),
    });
  });

  await page.route('**/jobs**', async (route) => {
    if (route.request().method() !== 'GET') {
      await route.continue();
      return;
    }
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        user_id: 'frontend-user',
        limit: 100,
        jobs: [
          {
            job_id: 'e2e-job-1',
            status: 'completed',
            created_at: '2026-04-21T12:00:00.000Z',
            updated_at: '2026-04-21T12:05:00.000Z',
            url: 'https://example.org/e2e-wiring',
          },
        ],
        total: 1,
      }),
    });
  });

  await page.route('**/documents?**', async (route) => {
    if (route.request().method() !== 'GET') {
      await route.continue();
      return;
    }
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({ documents: [], total: 0, page: 1 }),
    });
  });
}

test.describe('DM dashboard wiring (FR-009)', () => {
  test('shows runtime diagnostics and scrape job list with keyboard-friendly nav', async ({ page }) => {
    test.skip(
      !adminEmail || !adminPassword,
      'Set E2E_ADMIN_EMAIL and E2E_ADMIN_PASSWORD (or VITE_BOOTSTRAP_*) to run authenticated DM E2E tests.',
    );

    await installDmApiRoutes(page);
    await signInAsAdmin(page);

    await expect(page.locator('html')).toHaveAttribute('lang', 'en');

    await page.goto('/admin-access');
    await expect(page.getByText('Runtime Connectivity')).toBeVisible();
    await expect(page.getByText('Configured Base URL:')).toBeVisible();

    const jobsNav = page.getByRole('button', { name: 'Scrape Jobs' });
    await jobsNav.focus();
    await expect(jobsNav).toBeFocused();

    await page.goto('/scrape-jobs');
    await expect(page.getByText('https://example.org/e2e-wiring')).toBeVisible({ timeout: 15_000 });
  });
});
