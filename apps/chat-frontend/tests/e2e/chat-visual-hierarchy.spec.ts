import { expect, test } from '@playwright/test';

import { installChatRenderingFixtures } from './chat-rendering.fixtures';

test.describe('chat visual hierarchy', () => {
  test('keeps distinct user and assistant roles and stable layout', async ({ page }) => {
    await installChatRenderingFixtures(page, {
      answer: 'Assistant response with enough content to verify stable layout and role styling.',
    });

    await page.goto('/');
    const composer = page.locator('main textarea').first();

    await composer.fill('Role hierarchy check');
    await composer.press('Enter');

    const userMessage = page
      .locator('[data-testid="chat-message"][data-message-role="user"]')
      .last();
    const assistantMessage = page
      .locator('[data-testid="chat-message"][data-message-role="assistant"]')
      .last();

    await expect(userMessage).toBeVisible();
    await expect(assistantMessage).toBeVisible();

    const box = await assistantMessage.boundingBox();
    expect(box).not.toBeNull();
    expect((box?.height ?? 0) > 0).toBe(true);
  });
});
