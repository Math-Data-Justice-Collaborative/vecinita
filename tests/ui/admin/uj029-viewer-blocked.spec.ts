import { expect, test } from "@playwright/test";

import { mockAuthenticatedViewer } from "../helpers/mock-admin-api";

/** UJ-029: Auth role ↔ AdminLayout nav ↔ write surfaces. */
test.describe("Viewer role gating", () => {
  test.beforeEach(async ({ page }) => {
    await mockAuthenticatedViewer(page);
  });

  test("hides Users nav and shows read-only ingest notice", async ({ page }) => {
    await page.goto("/dashboard");

    await expect(page.getByTestId("admin-nav")).toBeVisible();
    await expect(page.getByRole("link", { name: /users/i })).toHaveCount(0);

    await page.getByRole("link", { name: /^corpus$/i }).click();
    await expect(page.getByTestId("viewer-read-only-notice")).toBeVisible();
  });
});
