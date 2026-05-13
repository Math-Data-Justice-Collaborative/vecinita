import { test, expect } from '@playwright/test';

async function triggerAltShortcut(
  page: import('@playwright/test').Page,
  key: 'a' | 'k'
): Promise<void> {
  await page.evaluate((shortcutKey) => {
    document.dispatchEvent(
      new KeyboardEvent('keydown', {
        key: shortcutKey,
        altKey: true,
        bubbles: true,
      })
    );
  }, key);
}

async function installCommunityFixtures(page: import('@playwright/test').Page): Promise<void> {
  await page.route('**/documents/overview**', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        sources: [
          {
            url: 'https://example.org/community-guide',
            title: 'Community Guide',
            source_domain: 'example.org',
            tags: ['housing'],
          },
        ],
        unique_sources: 1,
        total_chunks: 3,
      }),
    });
  });

  await page.route('**/documents/tags**', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({ tags: [{ tag: 'housing', source_count: 1 }] }),
    });
  });

  await page.route('**/ask/config**', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        providers: [{ name: 'groq', models: ['llama-3.1-8b'], default: true }],
        models: { groq: ['llama-3.1-8b'] },
        defaultProvider: 'groq',
        defaultModel: 'llama-3.1-8b',
      }),
    });
  });

  await page.route('**/ask/stream**', async (route) => {
    await route.fulfill({
      status: 200,
      headers: {
        'Content-Type': 'text/event-stream',
        'Cache-Control': 'no-cache',
        Connection: 'keep-alive',
      },
      body: [
        `data: ${JSON.stringify({
          type: 'thinking',
          message: 'Looking through our local resources...',
          stage: 'retrieval',
          progress: 45,
          waiting: true,
          status: 'working',
        })}\n\n`,
        `data: ${JSON.stringify({
          type: 'complete',
          answer: 'Try the [Community Support Hub](https://safe.example.org/hub) for housing help.',
          sources: [
            {
              title: 'Community Support Hub',
              url: 'https://safe.example.org/hub',
              snippet: 'Housing and support services in one place.',
            },
          ],
          thread_id: 'community-widget-thread',
          metadata: { progress: 100, stage: 'complete' },
        })}\n\n`,
      ].join(''),
    });
  });
}

test.describe('Community flows', () => {
  test('documents links, chat interactions, accessibility controls, keyboard combos, and chat widget', async ({
    page,
    context,
  }) => {
    const docsHealth = await page.request.get('/api/v1/documents/overview');
    test.skip(
      !docsHealth.ok(),
      'Requires running gateway/docs backend for full community flow e2e'
    );
    const docsOverview = (await docsHealth.json().catch(() => null)) as {
      unique_sources?: number;
    } | null;
    test.skip(
      (docsOverview?.unique_sources ?? 0) < 1,
      'Requires at least one indexed source for document link verification'
    );

    await page.goto('/documents');
    await expect(page.getByRole('heading', { name: /Documents|Documentos/i })).toBeVisible();

    const sourceLinks = page.locator('table tbody a[href^="http"]');
    await expect(sourceLinks.first()).toBeVisible();
    const [popup] = await Promise.all([context.waitForEvent('page'), sourceLinks.first().click()]);
    await expect(popup).toHaveURL(/https?:\/\//);
    await popup.close();

    await page.goto('/');
    await expect(page.getByRole('heading', { name: /Vecinita/i })).toBeVisible();

    const mainComposer = page.locator('main textarea').first();
    await mainComposer.fill('Hello Vecinita, can you share housing resources?');
    await mainComposer.press('Enter');
    await expect(page.getByText('Hello Vecinita, can you share housing resources?')).toBeVisible();

    await mainComposer.fill('Can you also include food assistance contacts?');
    await mainComposer.press('Enter');
    await expect(page.getByText('Can you also include food assistance contacts?')).toBeVisible();

    await page.keyboard.press('Alt+a');
    await expect(page.getByRole('dialog')).toBeVisible();

    const toggles = page.getByRole('dialog').locator('input[type="checkbox"]');
    const toggleCount = await toggles.count();
    for (let index = 0; index < toggleCount; index += 1) {
      const toggle = toggles.nth(index);
      await toggle.check();
      await expect(toggle).toBeChecked();
      await toggle.uncheck();
      await expect(toggle).not.toBeChecked();
    }

    await page.keyboard.press('Escape');
    await expect(page.getByRole('dialog')).toBeHidden();

    await page.keyboard.press('Alt+k');
    await expect(
      page.getByRole('heading', { name: /Keyboard Shortcuts|Atajos de Teclado/i })
    ).toBeVisible();
    await page.keyboard.press('Escape');

    const widgetOpenButton = page.locator('button.fixed[aria-label]').first();
    await widgetOpenButton.click();

    const widgetComposer = page.locator('textarea').last();
    await widgetComposer.fill('Widget test message');
    await page
      .getByRole('button', { name: /Send message|Enviar mensaje/i })
      .last()
      .click();
    await expect(page.getByText('Widget test message')).toBeVisible();

    await page.getByRole('link', { name: /Admin login/i }).click();
    await expect(page).toHaveURL(/\/login\?redirect=%2Fadmin/);
    await expect(page.getByRole('heading', { name: /Admin Login/i })).toBeVisible();
    await expect(page.getByLabel('Email')).toBeVisible();
    await expect(page.getByLabel('Password')).toBeVisible();

    await page.getByRole('link', { name: /Browse documents/i }).click();
    await expect(page).toHaveURL(/\/documents/);
  });

  test('public community journey covers nav, widget chat, safe link clickthrough, and accessibility', async ({
    page,
    context,
  }) => {
    await installCommunityFixtures(page);
    await context.route('https://example.org/**', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'text/html',
        body: '<html><body><h1>Community guide</h1></body></html>',
      });
    });
    await context.route('https://safe.example.org/**', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'text/html',
        body: '<html><body><h1>Support hub</h1></body></html>',
      });
    });

    await page.goto('/');
    await page.getByRole('link', { name: /Documents|Documentos/i }).click();
    await expect(page).toHaveURL(/\/documents/);
    await expect(page.getByText('Community Guide')).toBeVisible();

    const [docsPopup] = await Promise.all([
      context.waitForEvent('page', { timeout: 30000 }),
      page.getByRole('link', { name: /Open source|Abrir fuente/i }).click(),
    ]);
    await expect(docsPopup).toHaveURL('https://example.org/community-guide');
    await docsPopup.close();

    await page.getByRole('link', { name: /Chat/i }).click();
    await expect(page).toHaveURL(/\/$/);

    const widgetOpenButton = page.getByTestId('chat-widget-open');
    await expect(widgetOpenButton).toBeVisible();
    await widgetOpenButton.click();

    const widgetPanel = page.getByTestId('chat-widget-panel');
    await expect(widgetPanel).toBeVisible();

    const widgetComposer = widgetPanel.getByTestId('chat-widget-composer');
    await expect(widgetComposer).toBeVisible();
    await widgetComposer.fill('I need housing support resources');
    await widgetPanel.getByTestId('chat-widget-send').click();

    await expect(widgetPanel.getByText('I need housing support resources')).toBeVisible();
    const safeLink = widgetPanel.getByRole('link', { name: 'Community Support Hub', exact: true });
    await expect(safeLink).toBeVisible({ timeout: 30000 });

    const [chatPopup] = await Promise.all([
      context.waitForEvent('page', { timeout: 30000 }),
      safeLink.click(),
    ]);
    await expect(chatPopup).toHaveURL('https://safe.example.org/hub');
    await chatPopup.close();

    await triggerAltShortcut(page, 'a');
    const accessibilityDialog = page.getByRole('dialog');
    await expect(accessibilityDialog).toBeVisible();
    await accessibilityDialog.getByRole('checkbox').first().check();
    await expect(accessibilityDialog.getByRole('checkbox').first()).toBeChecked();
    await page.keyboard.press('Escape');
    await expect(accessibilityDialog).toBeHidden();

    await triggerAltShortcut(page, 'k');
    await expect(
      page.getByRole('heading', { name: /Keyboard Shortcuts|Atajos de Teclado/i })
    ).toBeVisible();
    await page.keyboard.press('Escape');
    await expect(widgetComposer).toBeVisible();
  });
});
