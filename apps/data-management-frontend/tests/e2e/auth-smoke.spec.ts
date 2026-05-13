import { test, expect } from '@playwright/test';

test('login screen is reachable', async ({ page }) => {
  await page.goto('/login');
  await expect(page.getByRole('heading', { name: 'Sign In' })).toBeVisible();
});
