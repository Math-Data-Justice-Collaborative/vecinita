import { expect, test } from "@playwright/test";

import { mockSupabaseAuth } from "../helpers/mock-supabase-auth";

/** UJ-026: Login form ↔ AuthProvider error display. */
test.describe("Login form errors", () => {
  test.beforeEach(async ({ page }) => {
    await mockSupabaseAuth(page);
    await page.route(/\/auth\/v1\/token/, async (route) => {
      if (route.request().method() === "POST") {
        await route.fulfill({
          status: 400,
          contentType: "application/json",
          body: JSON.stringify({
            error: "invalid_grant",
            error_description: "Invalid login credentials",
          }),
        });
        return;
      }
      await route.continue();
    });
  });

  test("shows an error when credentials are rejected", async ({ page }) => {
    await page.goto("/login");

    await page.getByLabel(/email/i).fill("bad@example.com");
    await page.getByLabel(/password/i).fill("wrong-password");
    await page.getByRole("button", { name: /sign in/i }).click();

    await expect(page.getByRole("alert")).toBeVisible();
    await expect(page).toHaveURL(/\/login/);
  });
});
