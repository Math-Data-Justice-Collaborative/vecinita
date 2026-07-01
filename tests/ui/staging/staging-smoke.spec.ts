import { expect, test } from "@playwright/test";

const chatUrl = process.env.VECINITA_STAGING_CHAT_FRONTEND_URL;
const adminUrl = process.env.VECINITA_STAGING_ADMIN_FRONTEND_URL;

/**
 * T3-ui — live staging browser smoke (H6).
 * Skipped in CI unless staging URLs are set. No route mocks — validates deployed bundles.
 */
test.describe("Staging frontend smoke (T3-ui)", () => {
  test("chat staging shell loads", async ({ page }) => {
    test.skip(!chatUrl, "VECINITA_STAGING_CHAT_FRONTEND_URL not set");

    await page.goto(chatUrl!);
    await expect(page.getByTestId("sidebar")).toBeVisible({ timeout: 30_000 });
    await expect(page.getByTestId("app-header")).toBeVisible();
  });

  test("admin staging login page loads", async ({ page }) => {
    test.skip(!adminUrl, "VECINITA_STAGING_ADMIN_FRONTEND_URL not set");

    await page.goto(`${adminUrl!.replace(/\/$/, "")}/login`);
    await expect(page.getByTestId("login-form")).toBeVisible({
      timeout: 30_000,
    });
  });
});
