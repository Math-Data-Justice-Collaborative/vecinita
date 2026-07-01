import { expect, test } from "@playwright/test";

import { mockSupabaseAuth } from "../helpers/mock-supabase-auth";

/** UJ-028: ProtectedRoute redirects unauthenticated visitors to login. */
test.describe("Protected admin routes", () => {
  test.beforeEach(async ({ page }) => {
    await mockSupabaseAuth(page);
  });

  test("redirects /dashboard to login when session is absent", async ({
    page,
  }) => {
    await page.goto("/dashboard");

    await expect(page).toHaveURL(/\/login/);
    await expect(page.getByTestId("login-form")).toBeVisible();
  });
});
