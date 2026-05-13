import { test, expect } from '@playwright/test';
import process from 'node:process';
import { Buffer } from 'node:buffer';

const adminEmail = process.env.E2E_ADMIN_EMAIL || process.env.VITE_DEV_ADMIN_EMAIL;
const adminPassword = process.env.E2E_ADMIN_PASSWORD || process.env.VITE_DEV_ADMIN_PASSWORD;
const adminToken =
  process.env.E2E_ADMIN_TOKEN ||
  process.env.VITE_DEV_ADMIN_TOKEN ||
  process.env.DEV_ADMIN_BEARER_TOKEN;

test.describe('Admin authentication and ingestion', () => {
  test.skip(
    !adminEmail || !adminPassword,
    'Set E2E_ADMIN_EMAIL and E2E_ADMIN_PASSWORD (or VITE_DEV_ADMIN_*) for admin E2E tests.'
  );

  test('logs in, adds source with tags, uploads by click and drag-drop, and logs out', async ({
    page,
  }) => {
    const cleanupSourceUrls = new Set<string>();
    const maybeSkipForInfraConstraint = async (): Promise<void> => {
      const adminError = page.getByText(/Admin API error/i).first();
      const visible = await adminError.isVisible().catch(() => false);
      if (!visible) return;

      const message = (await adminError.textContent()) ?? '';
      if (
        /429|Too Many Requests|ECONNREFUSED|connection refused|Could not connect to (?:a|the) (?:database|vector|ingestion|storage|Postgres) (?:backend|service|server)/i.test(
          message
        )
      ) {
        test.skip(true, `Environment constraint for admin ingestion flow: ${message.trim()}`);
      }
    };

    await page.goto('/login?redirect=/admin');

    await page.getByLabel('Email').fill(adminEmail!);
    await page.getByLabel('Password').fill(adminPassword!);
    await page.getByRole('button', { name: /sign in/i }).click();

    await expect(page.getByRole('heading', { name: /Admin|Administración/i })).toBeVisible();

    const sourceUrl = `https://example.com/?source=community-resource-${Date.now()}`;
    cleanupSourceUrls.add(sourceUrl);
    const tagsComboboxes = page.locator('main').getByRole('combobox', { name: /Tags|Etiquetas/i });
    await page.getByPlaceholder('https://example.com/page').fill(sourceUrl);
    await expect(tagsComboboxes.first()).toBeVisible();
    await tagsComboboxes.first().fill('__e2e__,community');
    await page.getByRole('button', { name: /^(Add|Agregar)$/i }).click();
    await maybeSkipForInfraConstraint();

    await expect(page.getByText(sourceUrl)).toBeVisible();

    await page.getByRole('button', { name: /Upload|Subir/i }).click();

    const fileInput = page.locator('input[type="file"]');
    const clickUploadFilename = `community-resource-${Date.now()}-click.txt`;
    await fileInput.setInputFiles({
      name: clickUploadFilename,
      mimeType: 'text/plain',
      buffer: Buffer.from('Community resource upload for automated verification.'),
    });
    await expect(tagsComboboxes.last()).toBeVisible();
    await tagsComboboxes.last().fill('__e2e__,community');
    await page.getByRole('button', { name: /Upload & Embed|Subir y vectorizar/i }).click();
    await maybeSkipForInfraConstraint();
    await expect(
      page.getByText(/Uploaded:\s*\d+ chunks inserted\.|Subido:\s*\d+ fragmentos insertados\./i)
    ).toBeVisible();

    await page.getByRole('button', { name: /Sources|Fuentes/i }).click();
    await expect(page.locator('span', { hasText: clickUploadFilename }).first()).toBeVisible();

    await page.getByRole('button', { name: /Upload|Subir/i }).click();

    const dropZone = page
      .getByText(
        /Drop a file here or click to select|Suelta un archivo aqui o haz clic para seleccionar/i
      )
      .locator('..');
    const dataTransfer = await page.evaluateHandle(() => new DataTransfer());
    const dragUploadFilename = `community-resource-drag-${Date.now()}.txt`;
    await page.evaluate(
      ({ dt, name }) => {
        const file = new File(
          ['Community resource drag-and-drop upload for automated verification.'],
          name,
          { type: 'text/plain' }
        );
        (dt as DataTransfer).items.add(file);
      },
      { dt: dataTransfer, name: dragUploadFilename }
    );

    await dropZone.dispatchEvent('drop', { dataTransfer });
    await expect(tagsComboboxes.last()).toBeVisible();
    await tagsComboboxes.last().fill('__e2e__,community');
    await page.getByRole('button', { name: /Upload & Embed|Subir y vectorizar/i }).click();
    await maybeSkipForInfraConstraint();
    await expect(
      page.getByText(/Uploaded:\s*\d+ chunks inserted\.|Subido:\s*\d+ fragmentos insertados\./i)
    ).toBeVisible();

    await page.getByRole('button', { name: /Sources|Fuentes/i }).click();
    await expect(page.locator('span', { hasText: dragUploadFilename }).first()).toBeVisible();

    await page.goto('/documents');
    await expect(page.getByRole('heading', { name: /Documents|Documentos/i })).toBeVisible();

    if (adminToken) {
      const listResponse = await page.request.get('/api/v1/admin/sources?limit=500&offset=0', {
        headers: {
          Authorization: `Bearer ${adminToken}`,
        },
      });

      if (listResponse.ok()) {
        const payload = (await listResponse.json()) as {
          sources?: Array<{ url?: string; tags?: string[] }>;
        };
        for (const source of payload.sources ?? []) {
          const sourceUrlValue = source.url ?? '';
          const sourceTags = source.tags ?? [];
          if (sourceTags.includes('__e2e__')) {
            cleanupSourceUrls.add(sourceUrlValue);
          }
        }
      }

      for (const cleanupUrl of cleanupSourceUrls) {
        if (!cleanupUrl) continue;
        await page.request.delete(`/api/v1/admin/sources?url=${encodeURIComponent(cleanupUrl)}`, {
          headers: {
            Authorization: `Bearer ${adminToken}`,
          },
        });
      }
    }

    await page.getByRole('button', { name: /Sign out|Cerrar sesión/i }).click();
    await expect(
      page.getByRole('link', { name: /Admin login|Iniciar sesión de administrador/i })
    ).toBeVisible();
  });
});
