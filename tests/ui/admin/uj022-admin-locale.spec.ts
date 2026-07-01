import { expect, test } from "@playwright/test";

import { mockAuthenticatedAdmin } from "../helpers/mock-admin-api";

/** UJ-022: LanguageToggle ↔ AdminLayout nav labels. */
test.describe("Admin language toggle", () => {
  test.beforeEach(async ({ page }) => {
    await mockAuthenticatedAdmin(page);
  });

  test("switches sidebar navigation labels to Spanish", async ({ page }) => {
    await page.goto("/dashboard");

    await page.getByTestId("language-toggle").getByRole("button", { name: "ES" }).click();

    await expect(page.getByRole("link", { name: /panel/i })).toBeVisible();
    await expect(page.getByRole("link", { name: /corpus/i })).toBeVisible();
  });
});
