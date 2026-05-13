import { test, expect } from '@playwright/test';

test.describe('Agent config response format regression', () => {
  test('app shell remains stable when ask/config responds with HTML', async ({ page }) => {
    const parseFailures: string[] = [];

    page.on('console', (msg) => {
      const text = msg.text();
      if (text.includes('Unexpected token') || text.includes('is not valid JSON')) {
        parseFailures.push(text);
      }
    });

    await page.route('**/api/v1/ask/config**', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'text/html; charset=utf-8',
        body: '<!doctype html><html><body>not-json</body></html>',
      });
    });

    await page.goto('/');
    await expect(page.getByRole('heading', { name: /Vecinita/i })).toBeVisible();

    // Ensure the old JSON parse crash does not reappear in browser console.
    expect(parseFailures).toEqual([]);
  });
});
