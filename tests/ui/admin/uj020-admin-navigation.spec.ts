import { expect, test } from "@playwright/test";

import { mockAuthenticatedAdmin } from "../helpers/mock-admin-api";

/**
 * UJ-020: AdminLayout sidebar links swap the main outlet content.
 */
test.describe("Admin sidebar navigation", () => {
  test.beforeEach(async ({ page }) => {
    await mockAuthenticatedAdmin(page);
  });

  test("Corpus link replaces dashboard content with corpus manager", async ({
    page,
  }) => {
    await page.goto("/dashboard");

    await expect(page.getByTestId("admin-nav")).toBeVisible();
    await page.getByRole("link", { name: /^corpus$/i }).click();

    await expect(page).toHaveURL(/\/corpus/);
    await expect(
      page.getByText(/ingest urls and manage documents/i),
    ).toBeVisible();
  });

  test("Evaluation link opens eval page with tab bar", async ({ page }) => {
    await page.goto("/dashboard");

    await page.getByRole("link", { name: /evaluation/i }).click();

    await expect(page).toHaveURL(/\/evaluation/);
    await expect(page.getByTestId("evaluation-page")).toBeVisible();
    await expect(page.getByTestId("evaluation-tabs")).toBeVisible();
    await expect(page.getByTestId("evaluation-history")).toBeVisible();
  });
});
