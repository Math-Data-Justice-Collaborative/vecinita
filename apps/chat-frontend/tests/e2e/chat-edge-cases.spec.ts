import { expect, test } from '@playwright/test';

import { installChatRenderingFixtures } from './chat-rendering.fixtures';

test.describe('chat edge case rendering', () => {
  test('renders remote images as links, keeps table scrollable, and strips html tags', async ({
    page,
  }) => {
    await installChatRenderingFixtures(page, {
      answer:
        'Remote image: ![Flood map](https://example.org/map.png)\n\n| Agency | Contact |\n| --- | --- |\n| WRWC | support@example.org |\n\n<script>alert(1)</script> safe text',
    });

    await page.goto('/');
    const composer = page.locator('main textarea').first();
    await composer.fill('Render edge cases');
    await composer.press('Enter');

    await expect(page.getByRole('link', { name: 'Flood map' })).toBeVisible();
    await expect(page.locator('[data-message-role="assistant"] img[alt="Flood map"]')).toHaveCount(
      0
    );

    const assistantMessage = page.locator('[data-message-role="assistant"]').last();
    await expect(assistantMessage.locator('table')).toBeVisible();
    await expect(assistantMessage.getByText('WRWC')).toBeVisible();
    await expect(assistantMessage.getByText('<script>')).toHaveCount(0);
    await expect(assistantMessage.getByText('safe text')).toBeVisible();
  });
});
