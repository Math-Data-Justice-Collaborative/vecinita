import { test, expect } from '@playwright/test';
import process from 'node:process';

const adminEmail = process.env.E2E_ADMIN_EMAIL || process.env.VITE_DEV_ADMIN_EMAIL;
const adminPassword = process.env.E2E_ADMIN_PASSWORD || process.env.VITE_DEV_ADMIN_PASSWORD;

test.describe('Admin Spanish language toggle', () => {
  test.skip(
    !adminEmail || !adminPassword,
    'Set E2E_ADMIN_EMAIL and E2E_ADMIN_PASSWORD (or VITE_DEV_ADMIN_*) for admin E2E tests.'
  );

  test('switches language to Spanish and shows localized admin tab labels', async ({ page }) => {
    await page.addInitScript(() => {
      localStorage.setItem('vecinita-language', 'en');
    });

    await page.goto('/login?redirect=/admin');

    await page.getByLabel('Email').fill(adminEmail!);
    await page.getByLabel('Password').fill(adminPassword!);
    await page.getByRole('button', { name: /sign in/i }).click();

    await expect(page.getByRole('heading', { name: 'Admin' })).toBeVisible();

    const languageSelect = page.locator('#language-select');
    await expect(languageSelect).toBeVisible();
    await languageSelect.selectOption('es');

    await expect(page.getByRole('heading', { name: 'Administración' })).toBeVisible();
    await expect(page.getByRole('button', { name: 'Fuentes' })).toBeVisible();
    await expect(page.getByRole('button', { name: 'Subir' })).toBeVisible();
    await expect(page.getByRole('button', { name: 'Cola' })).toBeVisible();
    await expect(page.getByRole('button', { name: 'Modelos' })).toBeVisible();

    await page.getByRole('button', { name: 'Cola' }).click();
    const queueStatusFilter = page.locator('main').getByRole('combobox').first();
    await expect(queueStatusFilter).toBeVisible();
    await expect(queueStatusFilter.locator('option[value=""]')).toHaveText(
      /All statuses|Todos los estados/i
    );

    await page.getByRole('button', { name: 'Modelos' }).click();
    await expect(page.getByText('Configuración de modelos')).toBeVisible();
  });
});
