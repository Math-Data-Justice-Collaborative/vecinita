import { test, expect } from '@playwright/test';

test.describe('Agent config connectivity', () => {
  test('loads app shell and confirms live ask config endpoint is reachable', async ({ page }) => {
    const response = await page.request.get('http://127.0.0.1:18004/api/v1/ask/config');
    expect(response.status()).toBe(200);

    const payload = await response.json();
    expect(payload).toHaveProperty('providers');
    expect(Array.isArray(payload.providers)).toBe(true);
    expect(payload.providers.length).toBeGreaterThan(0);

    await page.goto('/');
    await expect(page.getByRole('heading', { name: /Vecinita/i })).toBeVisible();
  });
});
