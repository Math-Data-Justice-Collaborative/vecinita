import { expect, test } from '@playwright/test';

test('documents tab fails closed during canonical outage', async ({ page }) => {
  await page.route('**/api/v1/documents/overview', async (route) => {
    await route.fulfill({
      status: 503,
      contentType: 'application/json',
      body: JSON.stringify({
        detail: 'Document index is temporarily unavailable because the database is not reachable.',
      }),
    });
  });
  await page.route('**/api/v1/documents/tags?limit=100', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({ tags: [] }),
    });
  });

  await page.goto('/documents');
  await expect(page.getByText(/temporarily unavailable/i)).toBeVisible();
  await expect(page.getByRole('link', { name: /open source/i })).toHaveCount(0);
});
