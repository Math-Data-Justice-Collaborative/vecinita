import { expect, test, type Page } from '@playwright/test';

async function submitMainChatQuestion(page: Page, question: string): Promise<void> {
  const composer = page.locator('main textarea').first();
  await composer.fill(question);
  await composer.press('Enter');
}

async function installChatConfigFixture(page: Page): Promise<void> {
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
}

async function installDoctorJourneyStream(page: Page): Promise<void> {
  await page.route('**/ask/stream**', async (route) => {
    await new Promise((resolve) => setTimeout(resolve, 300));
    const body = [
      `data: ${JSON.stringify({
        type: 'thinking',
        message: 'Looking through our local resources...',
        stage: 'retrieval',
        progress: 35,
        waiting: true,
        status: 'working',
      })}\n\n`,
      `data: ${JSON.stringify({
        type: 'source',
        url: 'https://clinic.example.org/directory',
        title: 'Community Clinic Directory',
        source_type: 'link',
      })}\n\n`,
      `data: ${JSON.stringify({
        type: 'complete',
        answer:
          'You can start with the [Providence Community Health Center](https://clinic.example.org/providers). They can help you find a doctor near you.',
        sources: [
          {
            title: 'Community Clinic Directory',
            url: 'https://clinic.example.org/directory',
            snippet: 'Directory of doctors and clinics near Providence.',
          },
        ],
        thread_id: 'doctor-journey-thread',
        metadata: { progress: 100, stage: 'complete' },
      })}\n\n`,
    ].join('');

    await route.fulfill({
      status: 200,
      headers: {
        'Content-Type': 'text/event-stream',
        'Cache-Control': 'no-cache',
        Connection: 'keep-alive',
      },
      body,
    });
  });
}

async function installClarificationJourneyStream(page: Page): Promise<void> {
  await page.route('**/ask/stream**', async (route) => {
    const requestUrl = new URL(route.request().url());
    const clarificationResponse = requestUrl.searchParams.get('clarification_response');

    if (!clarificationResponse) {
      await route.fulfill({
        status: 200,
        headers: {
          'Content-Type': 'text/event-stream',
          'Cache-Control': 'no-cache',
          Connection: 'keep-alive',
        },
        body: [
          `data: ${JSON.stringify({
            type: 'clarification',
            message: 'I need more details to continue.',
            questions: ['Which city are you in?', 'Do you need a primary care doctor?'],
            stage: 'clarification',
            progress: 80,
            waiting: true,
          })}\n\n`,
        ].join(''),
      });
      return;
    }

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
          message: 'Finalizing answer...',
          stage: 'answer',
          progress: 92,
          waiting: false,
          status: 'working',
        })}\n\n`,
        `data: ${JSON.stringify({
          type: 'complete',
          answer:
            'Thanks. In Providence, start with the [Open Door Health Clinic](https://clinic.example.org/open-door).',
          sources: [
            {
              title: 'Open Door Health Clinic',
              url: 'https://clinic.example.org/open-door',
              snippet: 'Primary care and referrals in Providence.',
            },
          ],
          thread_id: 'clarification-thread',
          metadata: { progress: 100, stage: 'complete' },
        })}\n\n`,
      ].join(''),
    });
  });
}

async function installUnsafeContentJourneyStream(page: Page): Promise<void> {
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
          type: 'complete',
          answer:
            'Unsafe test <script>window.__vecinita_xss = true<\\/script> [bad](javascript:alert(1)) [safe clinic](https://safe.example.org/clinic)',
          sources: [
            {
              title: 'Safe Clinic',
              url: 'https://safe.example.org/clinic',
              snippet: 'Safe destination for clickthrough verification.',
            },
          ],
          thread_id: 'unsafe-content-thread',
          metadata: { progress: 100, stage: 'complete' },
        })}\n\n`,
      ].join(''),
    });
  });
}

async function installSuggestionJourneyStream(page: Page): Promise<void> {
  await page.route('**/ask/stream**', async (route) => {
    const body = [
      `data: ${JSON.stringify({
        type: 'complete',
        answer: 'Here are community resources to get started.',
        sources: [],
        suggested_questions: ['Can you summarize this in 3 key points?', 'What should I do first?'],
        thread_id: 'suggestion-thread',
        metadata: { progress: 100, stage: 'complete' },
      })}\n\n`,
    ].join('');

    await route.fulfill({
      status: 200,
      headers: {
        'Content-Type': 'text/event-stream',
        'Cache-Control': 'no-cache',
        Connection: 'keep-alive',
      },
      body,
    });
  });
}

const J004_MOCK_SOURCE_URL = 'https://example.com/doc';
const J004_MOCK_SOURCE_TITLE = 'E2E source';

async function installDocumentsOverviewFixtureForJ004(page: Page): Promise<void> {
  await page.route('**/documents/overview', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        sources: [{ url: J004_MOCK_SOURCE_URL, title: J004_MOCK_SOURCE_TITLE }],
      }),
    });
  });
  await page.route('**/documents/tags**', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({ tags: [] }),
    });
  });
}

test.describe('Journey Chat (J001-J008)', () => {
  test('J001 loads chat home', async ({ page }) => {
    await page.goto('/');
    await expect(page.getByRole('heading', { name: /Vecinita/i })).toBeVisible();
    await expect(page.locator('main textarea').first()).toBeVisible();
  });

  test('J002 sends an English question', async ({ page }) => {
    await page.goto('/');
    const question = 'Hello Vecinita, can you list housing resources?';
    await submitMainChatQuestion(page, question);
    await expect(page.getByText(question)).toBeVisible();
  });

  test('J003 receives an assistant answer', async ({ page }) => {
    await page.goto('/');
    const question = `Please answer briefly ${Date.now()}`;
    await submitMainChatQuestion(page, question);
    await expect(page.getByText(question)).toBeVisible();

    const assistantMessage = page.locator('[data-testid="chat-message"]').filter({
      hasNotText: question,
    });
    await expect(assistantMessage.first()).toBeVisible({ timeout: 45000 });
  });

  test('J004 renders source cards with links', async ({ page, context }) => {
    const docsHealth = await page.request.get('/api/v1/documents/overview');
    test.skip(!docsHealth.ok(), 'Requires documents backend availability');

    await installDocumentsOverviewFixtureForJ004(page);
    await page.goto('/documents');
    const link = page.getByRole('link', { name: new RegExp(J004_MOCK_SOURCE_TITLE, 'i') }).first();
    await expect(link).toBeVisible();

    const [popup] = await Promise.all([context.waitForEvent('page'), link.click()]);
    await expect(popup).toHaveURL(J004_MOCK_SOURCE_URL);
    await popup.close();
  });

  test('J005 starts a new chat and clears messages', async ({ page }) => {
    await page.goto('/');
    const question = `New chat reset check ${Date.now()}`;
    await submitMainChatQuestion(page, question);
    await expect(page.getByText(question)).toBeVisible();

    await page
      .locator('button:has-text("New chat"), button:has-text("Nuevo chat")')
      .first()
      .click();
    const questionInUserMessages = page
      .locator('[data-testid="chat-message"][data-message-role="user"]')
      .filter({ hasText: question });
    await expect(questionInUserMessages).toHaveCount(0, { timeout: 10000 });
  });

  test('J006 sends a Spanish question and gets localized response', async ({ page }) => {
    await page.addInitScript(() => localStorage.setItem('vecinita-language', 'es'));
    await page.goto('/');

    const question = 'Necesito ayuda con recursos de vivienda';
    await submitMainChatQuestion(page, question);
    await expect(page.getByText(question)).toBeVisible();
    await expect(page.locator('[data-testid="chat-message"]').first()).toBeVisible({
      timeout: 45000,
    });
  });

  test('J007 retries after a failed request', async ({ page }) => {
    let askCalls = 0;
    await page.route('**/ask/stream**', async (route) => {
      askCalls += 1;
      if (askCalls === 1) {
        await route.fulfill({
          status: 500,
          contentType: 'application/json',
          body: '{"detail":"forced error"}',
        });
        return;
      }
      await route.fulfill({
        status: 200,
        headers: {
          'Content-Type': 'text/event-stream',
          'Cache-Control': 'no-cache',
          Connection: 'keep-alive',
        },
        body: [
          `data: ${JSON.stringify({
            type: 'complete',
            answer: 'Retry succeeded.',
            sources: [],
            thread_id: 'retry-thread',
            metadata: { progress: 100, stage: 'complete' },
          })}\n\n`,
        ].join(''),
      });
    });

    await page.goto('/');
    const question = `Retry journey ${Date.now()}`;
    await submitMainChatQuestion(page, question);

    const retryButton = page.getByRole('button', { name: /Retry|Reintentar/i }).first();
    await expect(retryButton).toBeVisible({ timeout: 15000 });
    await retryButton.click();

    await expect.poll(() => askCalls, { timeout: 20000 }).toBeGreaterThanOrEqual(2);
  });

  test('J008 displays streaming progression before completion', async ({ page }) => {
    await page.goto('/');
    const question = `Streaming check ${Date.now()}`;
    await submitMainChatQuestion(page, question);
    await expect(page.getByText(question)).toBeVisible();

    await expect(
      page
        .locator('[data-testid="streaming-indicator"]')
        .or(page.locator('text=/Thinking|Pensando/i'))
        .first()
    ).toBeVisible({ timeout: 15000 });
    await expect(page.locator('[data-testid="chat-message"]').first()).toBeVisible({
      timeout: 45000,
    });
  });

  test('doctor journey renders response, exposes links, and remains accessible', async ({
    page,
    context,
  }) => {
    await installChatConfigFixture(page);
    await installDoctorJourneyStream(page);
    await context.route('https://clinic.example.org/**', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'text/html',
        body: '<html><body><h1>Mock clinic page</h1></body></html>',
      });
    });

    await page.goto('/');

    const question = 'Can you help me find a doctor near Providence?';
    await submitMainChatQuestion(page, question);
    await expect(page.getByText(question)).toBeVisible();

    const streamingStatus = page.getByRole('status', {
      name: /Assistant is thinking|El asistente está pensando/i,
    });
    await expect(streamingStatus).toBeVisible({ timeout: 15000 });

    const assistantMessage = page
      .locator('[data-testid="chat-message"][data-message-role="assistant"]')
      .last();
    await expect(assistantMessage).toBeVisible({ timeout: 45000 });
    await expect(assistantMessage).toContainText('Providence Community Health Center');

    const inlineDoctorLink = assistantMessage.getByRole('link', {
      name: /Providence Community Health Center/i,
    });
    await expect(inlineDoctorLink).toBeVisible();
    await inlineDoctorLink.focus();
    await expect(inlineDoctorLink).toBeFocused();

    const [popup] = await Promise.all([
      context.waitForEvent('page', { timeout: 30000 }),
      page.keyboard.press('Enter'),
    ]);
    await expect(popup).toHaveURL('https://clinic.example.org/providers');
    await popup.close();

    const sourceCardLink = page.getByRole('link', {
      name: /Source 1: Community Clinic Directory/i,
    });
    await expect(sourceCardLink).toBeVisible();

    await page.keyboard.press('Alt+a');
    const accessibilityDialog = page.getByRole('dialog');
    await expect(accessibilityDialog).toBeVisible();
    const screenReaderToggle = accessibilityDialog.getByRole('checkbox', {
      name: /Screen reader|Lector de pantalla/i,
    });
    await screenReaderToggle.check();
    await expect(screenReaderToggle).toBeChecked();
    await page.keyboard.press('Escape');
    await expect(accessibilityDialog).toBeHidden();
  });

  test('clarification journey requests more detail and completes after follow-up', async ({
    page,
    context,
  }) => {
    await installChatConfigFixture(page);
    await installClarificationJourneyStream(page);
    await context.route('https://clinic.example.org/**', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'text/html',
        body: '<html><body><h1>Clarification clinic</h1></body></html>',
      });
    });

    await page.goto('/');

    await submitMainChatQuestion(page, 'I need help finding a doctor');

    await expect(page.locator('li').filter({ hasText: '1. Which city are you in?' })).toBeVisible({
      timeout: 15000,
    });
    await expect(
      page.locator('li').filter({ hasText: '2. Do you need a primary care doctor?' })
    ).toBeVisible();

    await submitMainChatQuestion(page, 'Providence, and yes I need primary care');

    const assistantMessage = page
      .locator('[data-testid="chat-message"][data-message-role="assistant"]')
      .last();
    await expect(assistantMessage).toContainText('Open Door Health Clinic', { timeout: 15000 });

    const clinicLink = assistantMessage.getByRole('link', {
      name: 'Open Door Health Clinic',
      exact: true,
    });
    const [popup] = await Promise.all([
      context.waitForEvent('page', { timeout: 30000 }),
      clinicLink.click(),
    ]);
    await expect(popup).toHaveURL('https://clinic.example.org/open-door');
    await popup.close();
  });

  test('unsafe assistant content is rendered safely and keeps only safe navigation', async ({
    page,
    context,
  }) => {
    await installChatConfigFixture(page);
    await installUnsafeContentJourneyStream(page);
    await context.route('https://safe.example.org/**', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'text/html',
        body: '<html><body><h1>Safe clinic page</h1></body></html>',
      });
    });

    await page.addInitScript(() => {
      (window as typeof window & { __vecinita_xss?: boolean }).__vecinita_xss = false;
    });
    await page.goto('/');

    await submitMainChatQuestion(page, 'Show me clinics and include links');

    const assistantMessage = page
      .locator('[data-testid="chat-message"][data-message-role="assistant"]')
      .first();
    await expect(assistantMessage).toBeVisible({ timeout: 15000 });
    await expect(assistantMessage.locator('script')).toHaveCount(0);
    const safeInlineLink = assistantMessage.getByRole('link', { name: 'safe clinic', exact: true });
    await expect(safeInlineLink).toBeVisible();
    await expect(assistantMessage.locator('a[href^="javascript:"]')).toHaveCount(0);

    const executed = await page.evaluate(
      () => (window as typeof window & { __vecinita_xss?: boolean }).__vecinita_xss === true
    );
    expect(executed).toBeFalsy();

    const [popup] = await Promise.all([
      context.waitForEvent('page', { timeout: 30000 }),
      safeInlineLink.click(),
    ]);
    await expect(popup).toHaveURL('https://safe.example.org/clinic');
    await popup.close();
  });

  test('suggestion journey shows splash chips and auto-sends follow-up chips', async ({ page }) => {
    await installChatConfigFixture(page);
    await installSuggestionJourneyStream(page);

    await page.goto('/');

    const splashSuggestion = page
      .locator('main')
      .getByRole('button', {
        name: /What environmental concerns can I report in my neighborhood\?|¿Qué problemas ambientales puedo reportar en mi vecindario\?/i,
      })
      .first();
    await expect(splashSuggestion).toBeVisible();
    await splashSuggestion.click();

    await expect(
      page
        .locator('[data-testid="chat-message"][data-message-role="user"]')
        .filter({
          hasText:
            /What environmental concerns can I report in my neighborhood\?|¿Qué problemas ambientales puedo reportar en mi vecindario\?/i,
        })
        .first()
    ).toBeVisible();

    const followupSuggestion = page.getByRole('button', {
      name: 'What should I do first?',
      exact: true,
    });
    await expect(followupSuggestion).toBeVisible({ timeout: 15000 });
    await followupSuggestion.click();

    const userMessages = page
      .locator('[data-testid="chat-message"][data-message-role="user"]')
      .filter({ hasText: 'What should I do first?' });
    await expect(userMessages.first()).toBeVisible({ timeout: 15000 });
  });
});
