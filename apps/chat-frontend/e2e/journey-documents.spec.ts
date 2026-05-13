import { expect, test, type Page } from '@playwright/test';

const journeySources = [
  {
    url: 'https://example.org/community-health-directory',
    title: 'Community Health Directory',
    source_domain: 'example.org',
    tags: ['health', 'doctor'],
  },
  {
    url: 'stored/community-clinic-flyer.pdf',
    title: 'Community Clinic Flyer',
    source_domain: 'storage',
    tags: ['health'],
    downloadable: true,
  },
  {
    url: 'stored/benefits-handbook.pdf',
    title: 'Benefits Handbook',
    source_domain: 'storage',
    tags: ['benefits'],
    download_url: 'https://downloads.example.org/benefits-handbook.pdf',
  },
];

async function installDocumentsFixtures(page: Page): Promise<void> {
  await page.route('**/documents/overview**', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        sources: journeySources,
        unique_sources: journeySources.length,
        total_chunks: 9,
      }),
    });
  });

  await page.route('**/documents/tags**', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        tags: [
          { tag: 'health', source_count: 2 },
          { tag: 'doctor', source_count: 1 },
          { tag: 'benefits', source_count: 1 },
        ],
      }),
    });
  });

  await page.route('**/documents/download-url**', async (route) => {
    const requestUrl = new URL(route.request().url());
    const sourceUrl = requestUrl.searchParams.get('source_url');
    await new Promise((resolve) => setTimeout(resolve, 250));
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        download_url:
          sourceUrl === 'stored/community-clinic-flyer.pdf'
            ? 'https://downloads.example.org/community-clinic-flyer.pdf'
            : 'https://downloads.example.org/fallback.pdf',
      }),
    });
  });
}

async function installWindowOpenRecorder(page: Page): Promise<void> {
  await page.addInitScript(() => {
    const openedUrls: string[] = [];
    (window as typeof window & { __openedUrls?: string[] }).__openedUrls = openedUrls;
    window.open = ((url?: string | URL) => {
      openedUrls.push(String(url ?? ''));
      return null;
    }) as typeof window.open;
  });
}

async function readOpenedUrls(page: Page): Promise<string[]> {
  return page.evaluate(() =>
    ((window as typeof window & { __openedUrls?: string[] }).__openedUrls ?? []).slice()
  );
}

async function ensureDocumentsAvailable(page: Page): Promise<{ sources?: unknown[] } | null> {
  const docsResponse = await page.request.get('/api/v1/documents/overview');
  const payload = (await docsResponse.json().catch(() => null)) as { sources?: unknown[] } | null;
  const documentsReady = docsResponse.ok() && !!payload && Array.isArray(payload.sources);

  test.skip(!documentsReady, 'Documents endpoint is not available');
  return payload;
}

test.describe('Journey Documents (J009-J016)', () => {
  test('J009 loads documents dashboard', async ({ page }) => {
    await ensureDocumentsAvailable(page);
    await page.goto('/documents');
    await expect(page.getByRole('heading', { name: /Documents|Documentos/i })).toBeVisible();
    await expect(page.getByText(/Community Sources|Fuentes comunitarias/i)).toBeVisible();
  });

  test('J010 renders topic filters', async ({ page }) => {
    await ensureDocumentsAvailable(page);
    await page.goto('/documents');
    const topicFilter = page.getByRole('button', { name: /All Topics|Todos los temas/i });
    await expect(topicFilter).toBeVisible();
  });

  test('J011 filters by topic', async ({ page }) => {
    await ensureDocumentsAvailable(page);
    await page.goto('/documents');

    const beforeRows = await page.locator('table tbody tr').count();
    const firstFilter = page
      .locator('button')
      .filter({ hasText: /^#|^[A-Za-z].+/ })
      .first();

    test.skip((await firstFilter.count()) === 0, 'No topic filters available in this dataset');

    await firstFilter.click();
    const afterRows = await page.locator('table tbody tr').count();
    expect(afterRows).toBeLessThanOrEqual(beforeRows);
  });

  test('J012 clears filters', async ({ page }) => {
    await ensureDocumentsAvailable(page);
    await page.goto('/documents');

    const clearButton = page.getByRole('button', { name: /Clear filters|Limpiar filtros/i });
    test.skip(
      (await clearButton.count()) === 0,
      'Clear filter control not present for this dataset'
    );

    await clearButton.click();
    await expect(page.locator('table tbody tr').first()).toBeVisible();
  });

  test('J013 searches documents', async ({ page }) => {
    await ensureDocumentsAvailable(page);
    await page.goto('/documents');

    const search = page.getByPlaceholder(/Search|Buscar/i).first();
    test.skip((await search.count()) === 0, 'Search input unavailable');

    await search.fill('community');
    await expect(page.locator('table tbody tr').first()).toBeVisible();
  });

  test('J014 opens source link in new tab', async ({ page, context }) => {
    await ensureDocumentsAvailable(page);
    await page.goto('/documents');

    const sourceLink = page.locator('table tbody a[href^="http"]').first();
    await expect(sourceLink).toBeVisible();
    const [popup] = await Promise.all([context.waitForEvent('page'), sourceLink.click()]);
    await expect(popup).toHaveURL(/https?:\/\//);
    await popup.close();
  });

  test('J015 toggles language labels', async ({ page }) => {
    await ensureDocumentsAvailable(page);
    await page.goto('/documents');

    const languageToggle = page.getByRole('button', { name: /ES|EN/i }).first();
    test.skip((await languageToggle.count()) === 0, 'Language toggle not available');

    await languageToggle.click();
    await expect(page.getByRole('heading', { name: /Documents|Documentos/i })).toBeVisible();
  });

  test('J016 renders empty state when backend returns no sources', async ({ page }) => {
    await page.route('**/documents/overview**', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ sources: [], unique_sources: 0, total_chunks: 0 }),
      });
    });

    await page.goto('/documents');
    await expect(
      page.getByText(/No resources match your filters|Ningún recurso coincide con tus filtros/i)
    ).toBeVisible();
  });

  test('documents journey supports navigation, link opening, downloads, and accessibility controls', async ({
    page,
    context,
  }) => {
    await installDocumentsFixtures(page);
    await installWindowOpenRecorder(page);
    await context.route('https://example.org/**', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'text/html',
        body: '<html><body><h1>Mock external source</h1></body></html>',
      });
    });

    await page.goto('/');
    await page.getByRole('link', { name: /Documents|Documentos/i }).click();
    await expect(page).toHaveURL(/\/documents/);
    await expect(page.getByRole('heading', { name: /Documents|Documentos/i })).toBeVisible();

    await page.getByRole('button', { name: 'health (2)' }).click();
    await expect(page.getByText('Community Health Directory')).toBeVisible();
    await expect(page.getByText('Community Clinic Flyer')).toBeVisible();
    await expect(page.getByText('Benefits Handbook')).toBeHidden();

    const openSourceLink = page.getByRole('link', { name: /Open source|Abrir fuente/i }).first();
    await openSourceLink.focus();
    await expect(openSourceLink).toBeFocused();

    const [popup] = await Promise.all([
      context.waitForEvent('page', { timeout: 30000 }),
      page.keyboard.press('Enter'),
    ]);
    await expect(popup).toHaveURL('https://example.org/community-health-directory');
    await popup.close();

    await page.getByRole('button', { name: /Clear filters|Limpiar filtros/i }).click();
    await expect(page.getByText('Benefits Handbook')).toBeVisible();

    const clinicFlyerRow = page
      .locator('table tbody tr')
      .filter({ hasText: 'Community Clinic Flyer' });
    const benefitsRow = page.locator('table tbody tr').filter({ hasText: 'Benefits Handbook' });
    const clinicFlyerDownload = clinicFlyerRow.getByRole('button');
    const benefitsDownload = benefitsRow.getByRole('button');

    await expect(clinicFlyerDownload).toBeVisible();
    await expect(benefitsDownload).toBeVisible();

    await clinicFlyerDownload.click();
    await expect(clinicFlyerRow.getByRole('button')).toBeDisabled();
    await expect
      .poll(async () => readOpenedUrls(page), { timeout: 10000 })
      .toContain('https://downloads.example.org/community-clinic-flyer.pdf');

    await benefitsDownload.click();
    await expect
      .poll(async () => readOpenedUrls(page), { timeout: 10000 })
      .toContain('https://downloads.example.org/benefits-handbook.pdf');

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

  test('documents journey surfaces a download failure alert', async ({ page }) => {
    await page.route('**/documents/overview**', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          sources: [
            {
              url: 'stored/failing-download.pdf',
              title: 'Failing Download',
              source_domain: 'storage',
              tags: ['health'],
              downloadable: true,
            },
          ],
          unique_sources: 1,
          total_chunks: 1,
        }),
      });
    });

    await page.route('**/documents/tags**', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ tags: [{ tag: 'health', source_count: 1 }] }),
      });
    });

    await page.route('**/documents/download-url**', async (route) => {
      await route.fulfill({ status: 500, contentType: 'application/json', body: '{}' });
    });

    await page.goto('/documents');
    await expect(page.getByText('Failing Download')).toBeVisible();

    const dialogPromise = page.waitForEvent('dialog');
    await page.getByRole('button', { name: /Download|Descargar/i }).click();
    const dialog = await dialogPromise;
    expect(dialog.message()).toMatch(
      /Unable to resolve a download link|No se pudo resolver un enlace de descarga/
    );
    await dialog.accept();
  });
});
