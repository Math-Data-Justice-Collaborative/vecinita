import { expect, test } from '@playwright/test';

import { installChatRenderingFixtures } from './chat-rendering.fixtures';

test.describe('chat markdown rendering', () => {
  test('renders markdown content and hides raw payload metadata', async ({ page }) => {
    await installChatRenderingFixtures(page, {
      answer:
        '## Community Support\n\n- **Housing support**\n- [Find services](https://example.org/services)\n\n```\nmetadata should not be rendered as payload object\n```',
    });

    await page.goto('/');

    const composer = page.locator('main textarea').first();
    await composer.fill('Show community resources');
    await composer.press('Enter');

    await expect(page.getByText('Community Support')).toBeVisible();
    await expect(page.getByRole('link', { name: 'Find services' })).toBeVisible();
    await expect(page.getByText('metadata should not be rendered as payload object')).toBeVisible();
    await expect(page.getByText("'model': 'llama3.2'")).toHaveCount(0);
  });
});
