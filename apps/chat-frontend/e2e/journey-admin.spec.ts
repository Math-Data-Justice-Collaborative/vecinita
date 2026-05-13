import { expect, test } from '@playwright/test';
import process from 'node:process';
import { Buffer } from 'node:buffer';
import type { Page } from '@playwright/test';

const adminEmail = process.env.E2E_ADMIN_EMAIL || process.env.VITE_DEV_ADMIN_EMAIL;
const adminPassword = process.env.E2E_ADMIN_PASSWORD || process.env.VITE_DEV_ADMIN_PASSWORD;
const nonAdminEmail = process.env.E2E_NON_ADMIN_EMAIL;
const nonAdminPassword = process.env.E2E_NON_ADMIN_PASSWORD;

async function loginAsAdmin(page: Page): Promise<void> {
  await page.goto('/login?redirect=/admin');
  await page.getByLabel('Email').fill(adminEmail!);
  await page.getByLabel('Password').fill(adminPassword!);
  await page.getByRole('button', { name: /sign in|iniciar sesión/i }).click();
  await expect(page.getByRole('heading', { name: /Admin|Administración/i })).toBeVisible();
}

test.describe('Journey Admin (J017-J026)', () => {
  test('J017 redirects unauthenticated admin access', async ({ page }) => {
    await page.goto('/admin');
    await page.waitForURL(/\/login\?redirect=%2Fadmin/, { timeout: 30000 });
    await expect(page).toHaveURL(/\/login\?redirect=%2Fadmin/);
  });

  test.describe('authenticated admin journeys', () => {
    test.skip(!adminEmail || !adminPassword, 'Admin credentials required for J018-J024');

    test('J018 logs in successfully and lands on admin', async ({ page }) => {
      await loginAsAdmin(page);
      await expect(page).toHaveURL(/\/admin/);
    });

    test('J019 views admin sources list', async ({ page }) => {
      await loginAsAdmin(page);
      await expect(page.getByRole('button', { name: /Sources|Fuentes/i })).toBeVisible();
      await expect(page.locator('main')).toContainText(/Sources|Fuentes/i);
    });

    test('J020 adds source from admin', async ({ page }) => {
      await loginAsAdmin(page);
      const sourceUrl = `https://example.com/journey-admin-source-${Date.now()}`;

      await page.getByPlaceholder('https://example.com/page').fill(sourceUrl);
      await page
        .locator('main')
        .getByRole('combobox', { name: /Tags|Etiquetas/i })
        .first()
        .fill('__e2e__,journey');
      await page.getByRole('button', { name: /^(Add|Agregar)$/i }).click();
      await expect(page.getByText(sourceUrl)).toBeVisible();
    });

    test('J021 uploads a document in admin', async ({ page }) => {
      await loginAsAdmin(page);
      await page.getByRole('button', { name: /Upload|Subir/i }).click();

      const fileInput = page.locator('input[type="file"]');
      await fileInput.setInputFiles({
        name: `journey-upload-${Date.now()}.txt`,
        mimeType: 'text/plain',
        buffer: Buffer.from('Journey upload test payload'),
      });

      await page
        .locator('main')
        .getByRole('combobox', { name: /Tags|Etiquetas/i })
        .last()
        .fill('__e2e__,journey');
      await page.getByRole('button', { name: /Upload & Embed|Subir y vectorizar/i }).click();
      await expect(
        page.getByText(/Uploaded:\s*\d+ chunks inserted\.|Subido:\s*\d+ fragmentos insertados\./i)
      ).toBeVisible({ timeout: 45000 });
    });

    test('J022 views processing queue', async ({ page }) => {
      await loginAsAdmin(page);
      await page.getByRole('button', { name: /Queue|Cola/i }).click();
      await expect(page.locator('main')).toContainText(/Queue|Cola|Job|Trabajo/i);
    });

    test('J023 saves model settings', async ({ page }) => {
      await loginAsAdmin(page);
      await page.getByRole('button', { name: /Models|Modelos/i }).click();

      const saveButton = page.getByRole('button', { name: /Save|Guardar/i }).first();
      test.skip(
        (await saveButton.count()) === 0,
        'Model save UI not available in this environment'
      );

      await saveButton.click();
      await expect(page.locator('main')).toContainText(/Saved|Guardado|success|éxito/i);
    });

    test('J024 signs out and returns to public state', async ({ page }) => {
      await loginAsAdmin(page);
      await page.getByRole('button', { name: /Sign out|Cerrar sesión/i }).click();
      await expect(
        page.getByRole('link', { name: /Admin login|Iniciar sesión de administrador/i })
      ).toBeVisible();
    });
  });

  test('J025 shows error for invalid admin credentials', async ({ page }) => {
    await page.goto('/login?redirect=/admin');
    await page.getByLabel('Email').fill('invalid@example.com');
    await page.getByLabel('Password').fill('invalid-password');
    await page.getByRole('button', { name: /sign in|iniciar sesión/i }).click();

    await expect(page.getByText(/invalid|error|incorrect|fall[oó]/i)).toBeVisible({
      timeout: 15000,
    });
    await expect(page).toHaveURL(/\/login/);
  });

  test('J026 rejects non-admin user dashboard access', async ({ page }) => {
    test.skip(
      !nonAdminEmail || !nonAdminPassword,
      'Set E2E_NON_ADMIN_EMAIL/PASSWORD for non-admin journey'
    );

    await page.goto('/login?redirect=/admin');
    await page.getByLabel('Email').fill(nonAdminEmail!);
    await page.getByLabel('Password').fill(nonAdminPassword!);
    await page.getByRole('button', { name: /sign in|iniciar sesión/i }).click();

    await expect(page).not.toHaveURL(/\/admin$/);
  });
});
